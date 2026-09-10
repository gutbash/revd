# revd

**More engine audio slots for GTA IV: The Complete Edition.** Lifts the game's twenty-five slot ceiling
to sixty-four, so traffic past the twenty-fifth vehicle model is not silent.

One plugin, one job. Population and traffic density are handled separately by
[popctl](https://github.com/gutbash/popctl); the two are independent and can be used together or apart.

## The problem

GTA IV plays one looping engine sound per distinct vehicle **model** in earshot, not per vehicle, and
it has a fixed table of slots to hold them. The audio init probes `STREAM_ENGINE_1..` and stores each
into a 25-entry table; the loop stops at `cmp edi, 0x19`.

Stock traffic rarely puts twenty-five distinct models around you at once, so the ceiling is invisible
in a clean install. Add a traffic pack, or raise vehicle variety, and you go straight past it. Every
model past the twenty-fifth gets no slot, and cars roll by making no engine noise at all. It reads as
a broken audio mod, but nothing is broken: the game has simply run out of places to put the sound.

The table cannot grow in place, because the statics immediately after it are occupied. `revd`
relocates it into its own DLL, repoints all fourteen references, and raises the probe bound.

## What it changes

| Setting | Stock | What it controls |
|---|---|---|
| `Slots` | 25 | Engine audio slots the game may use, up to 64 |
| `AudioHeapMB` | 126 | Physical audio heap the slot block is carved from |

Each slot costs about 0.8 MB of the audio heap. Past roughly thirty slots the stock 126 MB heap runs
out and the game crashes during audio init, so raising the heap is **not optional** when you raise the
slot count. 192 MB comfortably covers all sixty-four.

Nothing is written to disk by the plugin. Every change is made in memory at runtime.

## Install

1. Have an ASI loader present. Ultimate ASI Loader as `dinput8.dll` is the usual one, and if you run
   FusionFix you already have it.
2. Drop `revd.asi` and `revd.ini` into your `GTAIV` folder, next to `GTAIV.exe`.
3. **Extend `waveslots.xml`.** See below. Skipping this makes the plugin do nothing useful.
4. Launch. `revd.log` appears next to the `.asi` and says what was patched.

To uninstall, delete both files and restore `waveslots.xml` from the `.bak` the script leaves.

## Step 3, the part people miss

The game probes for slots **by name**. A slot that `pc/audio/config/waveslots.xml` does not define is a
slot that stays empty, so raising `Slots` on its own buys you nothing at all.

Run the included script, which appends the missing entries to your existing file rather than replacing
it, so any other audio mod's changes survive:

```powershell
.\add-engine-slots.ps1 -Slots 64
```

It backs the original up to `waveslots.xml.bak`, is safe to run twice, and prints what it added. Pass
`-Path` if it cannot find the file on its own.

Then make sure `Slots` in `revd.ini` matches the number you generated.

## Verifying it worked

`revd.log` is the source of truth:

```
engine slots: table relocated to 0F2A0120 (14 sites), probe bound 25 -> 64
audio heap: 126 MB -> 192 MB
```

If either line is missing, the log says which check failed and nothing was patched.

## Limitations

These are the boundaries of what was tested. Nothing outside them should be assumed to work.

- **Complete Edition 1.2.0.59 only.** Every address here is a hardcoded RVA for that exact build. On
  any other version the verification fails, nothing is patched, and the log says so. It will not damage
  anything, it simply will not do anything.
- **64 is a hard ceiling**, set by the size of the relocated table. Higher values are clamped.
- **The heap raise is mandatory above about thirty slots.** With `AudioHeapMB` left at 0 and `Slots`
  raised, expect a crash during audio init. The plugin warns about this combination in the log.
- **Slots are a ceiling, not a guarantee.** Sixty-four slots means the game *can* voice sixty-four
  distinct models at once. Whether it does depends on how much variety is actually around you.
- **The patch window is narrow.** Both changes must land after `.text` is decrypted and before audio
  init runs. If the plugin loads too late, it detects that the window has closed, leaves the game stock
  and logs it. An ASI loader loads early enough; injecting later may not.
- **One machine.** Developed and tested on a single install with FusionFix loaded through an ASI
  loader. Other mod stacks are untested.

## Building

Windows, Visual Studio 2022 with the x86 toolchain:

```
.\build.ps1            # produces revd.asi
.\build.ps1 -Deploy    # and copies it into the game folder
```

Single translation unit, no dependencies beyond the Win32 SDK.

## License

MIT. See [LICENSE](LICENSE).
