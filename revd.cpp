// revd.asi - more engine audio slots for GTA IV: The Complete Edition (1.2.0.59).
//
// THE PROBLEM
// -----------
// GTA IV plays a looping engine sound per distinct vehicle MODEL in earshot, not per vehicle, and it
// has a fixed table of slots to put them in. The audio init (RVA 0x58D4C3..0x58D512) probes
// STREAM_ENGINE_1.. and stores each slot into a 16-byte-entry table at RVA 0xE832B8 (count at
// 0xE83298). The loop stops at `cmp edi, 0x19` (RVA 0x58D50D) - twenty five slots.
//
// Stock traffic rarely shows twenty five distinct models at once, so nobody notices. Add a traffic
// pack or raise vehicle variety and you go straight past it: every model past the twenty fifth is
// simply silent. Cars roll by making no engine noise at all.
//
// WHAT THIS DOES
// --------------
//   1. Relocates the slot table into this DLL, because the statics immediately after the stock table
//      are occupied and it cannot simply grow in place. Every reference to the table is an absolute
//      displacement onto entry 0's fields (+0 ptr, +4, +8, +12): fourteen sites, listed below with the
//      field each one addresses. All fourteen are verified against their expected values before any
//      write happens.
//   2. Raises the probe bound at 0x58D50F from 25 to [revd] Slots.
//   3. Raises the physical audio heap the slot block is carved from (`mov esi, imm32` at RVA 0x4C158C,
//      stock 126 MB) to [revd] AudioHeapMB. This is NOT optional: each slot costs about 0.8 MB, and
//      past roughly thirty slots the stock heap runs out and the game crashes during audio init. If
//      you turn the heap raise off, keep Slots at 25.
//
//   4. Declares the extra slots in pc/audio/config/waveslots.xml, because the engine probes them BY
//      NAME and a slot the file does not declare stays empty however high the bound goes. Missing
//      entries are appended, never replaced, so another audio mod's edits survive, and the original
//      is backed up first. Turn it off with [revd] WriteWaveslots=0 and declare them yourself.
//
// SAFETY
// ------
// waveslots.xml is the one and only file touched, and only when WriteWaveslots is on. Every engine
// patch is made in memory at runtime. The Complete Edition's .text
// is encrypted at load, so this polls until each site reads its expected stock value and only then
// writes. If any site disagrees, nothing is written and the reason goes in revd.log. Patching is
// skipped entirely once the audio system has initialised (the count global is no longer 0), so a late
// load is a no-op rather than a crash.
//
// Population, traffic density and ped keep radius are NOT here. That is popctl's job:
// https://github.com/gutbash/popctl
//
// MIT licensed. See LICENSE.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>

static char g_log[MAX_PATH], g_ini[MAX_PATH];
static HMODULE g_self = nullptr;

static void Log(const char* fmt, ...)
{
    FILE* f = fopen(g_log, "a"); if (!f) return;
    SYSTEMTIME st; GetLocalTime(&st);
    fprintf(f, "[%02d:%02d:%02d.%03d] ", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
    va_list ap; va_start(ap, fmt); vfprintf(f, fmt, ap); va_end(ap);
    fputc('\n', f); fclose(f);
}

// ---- engine audio wave slots --------------------------------------------------------------------
static const DWORD kSlotTableRva = 0xE832B8;
static const DWORD kSlotCountRva = 0xE83298;
static const DWORD kSlotBoundRva = 0x58D50F;      // imm8 of `cmp edi, 0x19`
struct SlotRef { DWORD rva; DWORD field; };
static const SlotRef kSlotRefs[] = {
    { 0x58B979, 8 }, { 0x58B984, 8 }, { 0x58B98F, 12 }, { 0x58B995, 8 },
    { 0x58CBD0, 0 }, { 0x58D4C6, 8 }, { 0x58ECC6, 0 }, { 0x58ED09, 0 },
    { 0x58ED0F, 8 }, { 0x58ED23, 4 }, { 0x58ED35, 8 }, { 0x599577, 0 },
    { 0x599767, 0 }, { 0x828054, 0 },
};
static const int kNumSlotRefs = (int)(sizeof kSlotRefs / sizeof kSlotRefs[0]);
static const int kStockSlots = 25;
static const int kMaxSlots   = 64;      // the relocated table's capacity

static int g_cfgSlots = 0;              // 0 = leave stock
static __declspec(align(16)) DWORD g_slotTable[(kMaxSlots + 2) * 4];   // 32-byte header + entries
static bool g_slotsDone = false, g_slotsWarned = false;
static bool g_slotsMissedWindow = false;   // audio init beat us to it; stop trying, but do not claim success

// ---- physical audio heap ------------------------------------------------------------------------
static const DWORD kAudioHeapRva = 0x4C158C;            // imm32 of `mov esi, 0x7E00000`
static const int   kAudioHeapStock = 132120576;         // 126 MB
static int g_cfgHeapMB = 0;                             // 0 = leave stock
static bool g_heapDone = false, g_heapWarned = false;

// ---- waveslots.xml ------------------------------------------------------------------------------
// The engine probes slots BY NAME, so raising the bound achieves nothing unless
// pc/audio/config/waveslots.xml also declares STREAM_ENGINE_1..Slots. This used to be a separate
// PowerShell script; Nexus quarantines any archive containing one, so it lives here instead.
//
// The file is read by the audio system, which initialises well after this DLL is attached, so
// writing it at load lands in time for the same session. Missing entries are APPENDED, never
// replaced, so another audio mod's edits survive. The original is copied to waveslots.xml.bak the
// first time, and never overwritten after that.
static const int kSlotBytes = 794624;    // every stock engine slot declares exactly this
static bool g_cfgWriteWaveslots = true;

static bool ReadWholeFile(const char* path, char** out, size_t* outLen)
{
    FILE* f = fopen(path, "rb");
    if (!f) return false;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    if (n <= 0 || n > 8 * 1024 * 1024) { fclose(f); return false; }
    fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)n + 1);
    if (!buf) { fclose(f); return false; }
    size_t got = fread(buf, 1, (size_t)n, f);
    fclose(f);
    buf[got] = 0;
    *out = buf; *outLen = got;
    return true;
}

static void WaveslotsPath(char* dst, size_t cap)
{
    char exe[MAX_PATH];
    GetModuleFileNameA(NULL, exe, MAX_PATH);          // ...\GTAIV\GTAIV.exe
    char* slash = strrchr(exe, '\\');
    if (slash) *slash = 0;
    _snprintf(dst, cap, "%s\\pc\\audio\\config\\waveslots.xml", exe);
    dst[cap - 1] = 0;
}

static bool EnsureWaveslots(int slots)
{
    char path[MAX_PATH];
    WaveslotsPath(path, sizeof path);

    char* buf = NULL; size_t len = 0;
    if (!ReadWholeFile(path, &buf, &len)) { Log("waveslots: cannot read %s - leaving it alone", path); return false; }

    // which STREAM_ENGINE_<n> already exist
    bool present[kMaxSlots + 1];
    memset(present, 0, sizeof present);
    const char* kNeedle = "STREAM_ENGINE_";
    for (const char* p = strstr(buf, kNeedle); p; p = strstr(p + 1, kNeedle)) {
        int n = atoi(p + strlen(kNeedle));
        if (n >= 1 && n <= kMaxSlots) present[n] = true;
    }
    int missing = 0;
    for (int i = 1; i <= slots; i++) if (!present[i]) missing++;
    if (missing == 0) { Log("waveslots: already declares STREAM_ENGINE_1..%d - not touched", slots); free(buf); return true; }

    const char* close = NULL;
    for (const char* p = strstr(buf, "</WaveSlots>"); p; p = strstr(p + 1, "</WaveSlots>")) close = p;
    if (!close) { Log("waveslots: no </WaveSlots> in %s - leaving it alone", path); free(buf); return false; }

    const char* eol = strstr(buf, "\r\n") ? "\r\n" : "\n";

    char bak[MAX_PATH];
    _snprintf(bak, sizeof bak, "%s.bak", path); bak[sizeof bak - 1] = 0;
    if (CopyFileA(path, bak, TRUE)) Log("waveslots: backed the original up to %s", bak);

    char tmp[MAX_PATH];
    _snprintf(tmp, sizeof tmp, "%s.revdtmp", path); tmp[sizeof tmp - 1] = 0;
    FILE* out = fopen(tmp, "wb");
    if (!out) { Log("waveslots: cannot write %s - leaving the original alone", tmp); free(buf); return false; }

    fwrite(buf, 1, (size_t)(close - buf), out);
    for (int i = 1; i <= slots; i++) {
        if (present[i]) continue;
        fprintf(out, "  <Slot>%s", eol);
        fprintf(out, "    <Name content=\"ascii\">STREAM_ENGINE_%d</Name>%s", i, eol);
        fprintf(out, "    <MaxHeaderSize value=\"2048\" />%s", eol);
        fprintf(out, "    <LoadType content=\"ascii\">BANK</LoadType>%s", eol);
        fprintf(out, "    <Size value=\"%d\" />%s", kSlotBytes, eol);
        fprintf(out, "  </Slot>%s", eol);
    }
    fwrite(close, 1, len - (size_t)(close - buf), out);
    fclose(out);
    free(buf);

    if (!MoveFileExA(tmp, path, MOVEFILE_REPLACE_EXISTING)) {
        Log("waveslots: could not replace %s (error %lu) - the original is untouched", path, GetLastError());
        DeleteFileA(tmp);
        return false;
    }
    Log("waveslots: added %d missing slot(s), now declares STREAM_ENGINE_1..%d", missing, slots);
    return true;
}

static bool PatchAudioHeap(BYTE* base)
{
    BYTE* p = base + kAudioHeapRva;
    MEMORY_BASIC_INFORMATION mbi;
    if (!VirtualQuery(p, &mbi, sizeof mbi) || !(mbi.State & MEM_COMMIT)) return false;
    const int want = g_cfgHeapMB * 1024 * 1024;
    int cur = *(int*)p;
    if (cur == want) { g_heapDone = true; return true; }
    if (cur != kAudioHeapStock) {
        if (!g_heapWarned) { g_heapWarned = true; Log("audio heap: RVA %X reads %d, expected stock %d - waiting", kAudioHeapRva, cur, kAudioHeapStock); }
        return false;
    }
    DWORD old;
    if (!VirtualProtect(p, 4, PAGE_EXECUTE_READWRITE, &old)) { Log("audio heap: VirtualProtect failed %lu", GetLastError()); return false; }
    *(int*)p = want;
    VirtualProtect(p, 4, old, &old);
    FlushInstructionCache(GetCurrentProcess(), p, 4);
    g_heapDone = true;
    Log("audio heap: %d MB -> %d MB", kAudioHeapStock / (1024 * 1024), g_cfgHeapMB);
    return true;
}

static bool PatchEngineSlots(BYTE* base)
{
    if (*(DWORD*)(base + kSlotCountRva) != 0) {
        Log("engine slots: audio already initialised (count %u) - not touched", *(DWORD*)(base + kSlotCountRva));
        return false;
    }
    if (base[kSlotBoundRva] != 0x19) {
        if (!g_slotsWarned) { g_slotsWarned = true; Log("engine slots: bound byte reads %02x, expected 19 - waiting", base[kSlotBoundRva]); }
        return false;
    }
    const DWORD oldBase = (DWORD)base + kSlotTableRva;
    for (int i = 0; i < kNumSlotRefs; i++) {
        DWORD v = *(DWORD*)(base + kSlotRefs[i].rva);
        if (v != oldBase + kSlotRefs[i].field) {
            if (!g_slotsWarned) { g_slotsWarned = true; Log("engine slots: site %X reads %08X, expected %08X - waiting", kSlotRefs[i].rva, v, oldBase + kSlotRefs[i].field); }
            return false;
        }
    }
    memset(g_slotTable, 0, sizeof g_slotTable);
    const DWORD newBase = (DWORD)&g_slotTable[8];
    for (int i = 0; i < kNumSlotRefs; i++) {
        BYTE* p = base + kSlotRefs[i].rva;
        DWORD old;
        if (!VirtualProtect(p, 4, PAGE_EXECUTE_READWRITE, &old)) { Log("engine slots: VirtualProtect failed at %X", kSlotRefs[i].rva); return false; }
        *(DWORD*)p = newBase + kSlotRefs[i].field;
        VirtualProtect(p, 4, old, &old);
    }
    DWORD old;
    VirtualProtect(base + kSlotBoundRva, 1, PAGE_EXECUTE_READWRITE, &old);
    base[kSlotBoundRva] = (BYTE)g_cfgSlots;
    VirtualProtect(base + kSlotBoundRva, 1, old, &old);
    FlushInstructionCache(GetCurrentProcess(), base + 0x58B000, 0x2E0000);
    g_slotsDone = true;
    Log("engine slots: table relocated to %08X (%d sites), probe bound %d -> %d", newBase, kNumSlotRefs, kStockSlots, g_cfgSlots);
    return true;
}

// First fatal exception in the process, logged and passed straight on to the game's own handler.
// This only ever reads and logs; it never swallows a crash.
static LONG g_excLogged = 0;
static LONG CALLBACK ExcLogger(EXCEPTION_POINTERS* ep)
{
    const DWORD code = ep->ExceptionRecord->ExceptionCode;
    if (code != EXCEPTION_ACCESS_VIOLATION && code != EXCEPTION_ILLEGAL_INSTRUCTION && code != EXCEPTION_STACK_OVERFLOW
        && code != EXCEPTION_INT_DIVIDE_BY_ZERO && code != EXCEPTION_PRIV_INSTRUCTION) return EXCEPTION_CONTINUE_SEARCH;
    if (InterlockedIncrement(&g_excLogged) > 6) return EXCEPTION_CONTINUE_SEARCH;
    BYTE* base = (BYTE*)GetModuleHandleA(NULL);
    DWORD exeSize = 0x1BE6400;   // 1.2.0.59 SizeOfImage
    CONTEXT* c = ep->ContextRecord;
    DWORD eip = c->Eip;
    HMODULE owner = nullptr; char modName[MAX_PATH] = "?";
    if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)eip, &owner) && owner) {
        GetModuleFileNameA(owner, modName, sizeof modName);
        const char* slash = strrchr(modName, '\\'); if (slash) memmove(modName, slash + 1, strlen(slash));
    }
    Log("EXCEPTION %08X at %08X (%s+0x%X) tid %lu", code, eip, modName, eip - (DWORD)(owner ? owner : (HMODULE)base), GetCurrentThreadId());
    if (code == EXCEPTION_ACCESS_VIOLATION && ep->ExceptionRecord->NumberParameters >= 2)
        Log("  %s at %08X", ep->ExceptionRecord->ExceptionInformation[0] ? "write" : "read", (DWORD)ep->ExceptionRecord->ExceptionInformation[1]);
    Log("  eax %08X ebx %08X ecx %08X edx %08X esi %08X edi %08X ebp %08X esp %08X", c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    Log("  slot table at %08X, engine slot count %u", (DWORD)&g_slotTable[8], *(DWORD*)(base + kSlotCountRva));
    DWORD* sp = (DWORD*)(c->Esp & ~3u);
    int shown = 0;
    for (int i = 0; i < 512 && shown < 24; i++) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQuery(sp + i, &mbi, sizeof mbi) || !(mbi.State & MEM_COMMIT) || (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD))) break;
        DWORD v = sp[i];
        if (v >= (DWORD)base && v < (DWORD)base + exeSize) { Log("  stack[%3d] %08X  GTAIV.exe+0x%X", i, v, v - (DWORD)base); shown++; }
        else if (g_self && v >= (DWORD)g_self && v < (DWORD)g_self + 0x40000) { Log("  stack[%3d] %08X  revd+0x%X", i, v, v - (DWORD)g_self); shown++; }
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

// Both patches have to land in the window between .text being decrypted and the audio system
// initialising, so poll quickly rather than waiting on one signature.
static DWORD WINAPI Worker(LPVOID)
{
    BYTE* base = (BYTE*)GetModuleHandleA(NULL);
    const bool wantHeap  = g_cfgHeapMB > 0;
    const bool wantSlots = g_cfgSlots > kStockSlots;
    Log("base %p; waiting for decrypted .text (heap %s, slots %s)",
        base, wantHeap ? "on" : "off", wantSlots ? "on" : "off");
    if (!wantHeap && !wantSlots) { Log("nothing to do; both features off"); return 0; }

    // Do this first and only once: the audio system parses waveslots.xml during the same init the
    // patches below are racing, so the file has to be right before that starts.
    if (wantSlots) {
        if (g_cfgWriteWaveslots) EnsureWaveslots(g_cfgSlots);
        else Log("waveslots: WriteWaveslots=0, so you must declare STREAM_ENGINE_1..%d yourself", g_cfgSlots);
    }

    for (int i = 0; i < 2400; i++) {   // up to 2 minutes at 50 ms
        if (wantHeap && !g_heapDone) PatchAudioHeap(base);
        if (wantSlots && !g_slotsDone) {
            MEMORY_BASIC_INFORMATION mbi;
            if (VirtualQuery(base + kSlotBoundRva, &mbi, sizeof mbi) && (mbi.State & MEM_COMMIT)
                && !(mbi.Protect & PAGE_NOACCESS) && !(mbi.Protect & PAGE_GUARD)) {
                if (*(DWORD*)(base + kSlotCountRva) != 0) {
                    Log("engine slots: audio initialised before the patch could land - left stock");
                    g_slotsMissedWindow = true;   // stop trying; the window is gone
                } else {
                    PatchEngineSlots(base);
                }
            }
        }
        if ((!wantHeap || g_heapDone) && (!wantSlots || g_slotsDone || g_slotsMissedWindow)) {
            Log("finished after %d polls; heap %s, slots %s", i,
                !wantHeap ? "off" : (g_heapDone ? "patched" : "NOT patched"),
                !wantSlots ? "off" : (g_slotsDone ? "patched" : "NOT patched"));
            return 0;
        }
        Sleep(50);
    }
    Log("timed out; heap %s, slots %s",
        !wantHeap ? "off" : (g_heapDone ? "patched" : "NOT patched"),
        !wantSlots ? "off" : (g_slotsDone ? "patched" : "NOT patched"));
    return 0;
}

BOOL APIENTRY DllMain(HMODULE mod, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(mod);
        g_self = mod;
        AddVectoredExceptionHandler(1, ExcLogger);
        char path[MAX_PATH]; GetModuleFileNameA(mod, path, MAX_PATH);
        char* dot = strrchr(path, '.'); if (dot) *dot = 0;
        sprintf(g_log, "%s.log", path); sprintf(g_ini, "%s.ini", path);

        g_cfgSlots  = GetPrivateProfileIntA("revd", "Slots", 0, g_ini);
        g_cfgHeapMB = GetPrivateProfileIntA("revd", "AudioHeapMB", 0, g_ini);
        g_cfgWriteWaveslots = GetPrivateProfileIntA("revd", "WriteWaveslots", 1, g_ini) != 0;

        if (g_cfgSlots != 0 && g_cfgSlots <= kStockSlots) {
            Log("Slots=%d is at or below stock %d - nothing to raise", g_cfgSlots, kStockSlots);
            g_cfgSlots = 0;
        }
        if (g_cfgSlots > kMaxSlots) { Log("Slots=%d exceeds the table capacity - clamped to %d", g_cfgSlots, kMaxSlots); g_cfgSlots = kMaxSlots; }
        if (g_cfgHeapMB != 0 && g_cfgHeapMB < 126) { Log("AudioHeapMB=%d is below stock 126 - ignored", g_cfgHeapMB); g_cfgHeapMB = 0; }
        if (g_cfgHeapMB > 512) { Log("AudioHeapMB=%d clamped to 512", g_cfgHeapMB); g_cfgHeapMB = 512; }
        if (g_cfgSlots > 30 && g_cfgHeapMB == 0)
            Log("WARNING: Slots=%d with the stock 126 MB audio heap will very likely crash during audio init. Set AudioHeapMB.", g_cfgSlots);

        Log("revd loaded: Slots=%d AudioHeapMB=%d WriteWaveslots=%d (stock 25 / 126)", g_cfgSlots, g_cfgHeapMB, g_cfgWriteWaveslots ? 1 : 0);
        HANDLE t = CreateThread(NULL, 0, Worker, NULL, 0, NULL);
        if (t) CloseHandle(t);
    }
    return TRUE;
}
