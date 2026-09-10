"""revd figures.

Sources, and nothing outside them:
  - disassembly of GTAIV.exe 1.2.0.59 (the probe loop, the table, the fourteen references)
  - pc/audio/config/waveslots.xml (slot names and declared sizes, parsed live by this script)
  - revd.log from a real session (what actually got patched)
  - two dated observations from 2026-09-06: 30 slots crashed on the stock heap; 64 slots
    runs on a 192 MB heap

The heap figure is deliberately not a model. The declared slot sizes already exceed the stock
heap at stock slot count, so the heap is plainly not a straight sum of them and the allocator's
real behaviour was never characterised. The figure shows what was configured and what was
observed, and says so.

    python make_figures.py          -> writes ./figures/*.png
"""
import os
import xml.etree.ElementTree as ET
import plotly.graph_objects as go
from figstyle import (SERIF, SANS, MONO, SURFACE, PANEL, GRID, INK, INK2, MUTED,
                      BLUE, ORANGE, AQUA, YELLOW, BLUE_F, ORANGE_F, AQUA_F, YELLOW_F,
                      base_layout, note, box, label, arrow)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)
SCALE = 2
MB = 1024 * 1024

WAVESLOTS = os.environ.get(
    "WAVESLOTS",
    r"H:\Steam\steamapps\common\Grand Theft Auto IV\GTAIV\pc\audio\config\waveslots.xml")


def save(fig, name):
    p = os.path.join(OUT, name + ".png")
    fig.write_image(p, scale=SCALE)
    print("wrote", p)


def read_waveslots(path):
    """Real slot names and sizes, straight out of the game's own config."""
    root = ET.parse(path).getroot()
    eng, other = [], []
    for s in root.findall("Slot"):
        nm = (s.findtext("Name") or "").strip()
        el = s.find("Size")
        sz = int(el.get("value")) if el is not None else 0
        (eng if nm.startswith("STREAM_ENGINE_") else other).append((nm, sz))
    return eng, other


# ---------------------------------------------------------------- figure 1
def fig_ceiling():
    """One slot per distinct model, and what happens past the twenty-fifth."""
    fig = go.Figure()
    fig.update_layout(**base_layout(
        "One engine sound per distinct model",
        "Not per vehicle. Twenty-five slots, however many cars are on the street.",
        height=720, width=1280))
    fig.update_xaxes(range=[0, 100], visible=False)
    fig.update_yaxes(range=[0, 100], visible=False)

    cols, rows_n = 16, 4
    x0, y0, w, h, gap = 6, 30, 5.0, 11, 0.8
    n = 0
    for r in range(rows_n):
        for c in range(cols):
            n += 1
            if n > 64:
                break
            voiced = n <= 25
            col = BLUE if voiced else ORANGE
            fill = BLUE_F if voiced else "rgba(0,0,0,0)"
            x = x0 + c * (w + gap)
            y = y0 + (rows_n - 1 - r) * (h + gap)
            box(fig, x, y, x + w, y + h, col, fill,
                width=2 if voiced else 1, dash=None if voiced else "dot")
            label(fig, x + w / 2, y + h / 2, str(n), 12,
                  INK if voiced else MUTED, MONO)

    label(fig, 6, 88, "slots 1 to 25", 17, BLUE, SERIF, anchor="left")
    label(fig, 6, 83, "the fixed table: these models are voiced", 14, INK2, SERIF, anchor="left")
    label(fig, 52, 88, "26 and beyond", 17, ORANGE, SERIF, anchor="left")
    label(fig, 52, 83, "no slot, no engine sound at all", 14, INK2, SERIF, anchor="left")

    label(fig, 50, 20, "cmp edi, 0x19", 20, YELLOW, MONO)
    label(fig, 50, 14, "the probe loop stops here, at RVA 0x58D50D", 14, INK2, SERIF)

    note(fig,
         "The limit is invisible in a clean install, because stock traffic rarely puts twenty-five distinct models "
         "around you at once.<br>Add a traffic pack or raise vehicle variety and cars begin rolling past in silence. "
         "revd raises the bound to sixty-four.",
         y=0.02)
    save(fig, "fig1_ceiling")


# ---------------------------------------------------------------- figure 2
def fig_relocation():
    """Why the table has to move, and what moving it costs."""
    fig = go.Figure()
    fig.update_layout(**base_layout(
        "The table cannot grow where it sits",
        "Slot table and its neighbours in GTAIV.exe 1.2.0.59. Addresses are RVAs.",
        height=800, width=1280))
    fig.update_xaxes(range=[0, 100], visible=False)
    fig.update_yaxes(range=[0, 100], visible=False)

    # stock layout, left
    label(fig, 6, 88, "in the executable", 17, INK, SERIF, anchor="left")
    box(fig, 6, 74, 42, 82, GRID, PANEL)
    label(fig, 9, 78, "0xE83298   slot count", 14, INK2, MONO, anchor="left")

    box(fig, 6, 50, 42, 72, BLUE, BLUE_F)
    label(fig, 9, 68, "0xE832B8", 14, MUTED, MONO, anchor="left")
    label(fig, 24, 61, "25 entries of 16 bytes", 16, BLUE, SANS)
    label(fig, 24, 55, "the slot table", 14, INK2, SERIF)

    box(fig, 6, 36, 42, 48, ORANGE, ORANGE_F)
    label(fig, 24, 44, "occupied", 16, ORANGE, SERIF)
    label(fig, 24, 39, "unrelated statics, immediately after", 13, INK2, SERIF)

    label(fig, 24, 30, "no room to extend", 15, ORANGE, SERIF)

    # relocated, right
    label(fig, 58, 88, "in revd.asi", 17, AQUA, SERIF, anchor="left")
    box(fig, 58, 74, 94, 82, GRID, PANEL)
    label(fig, 61, 78, "32-byte header", 14, INK2, MONO, anchor="left")

    box(fig, 58, 36, 94, 72, AQUA, AQUA_F)
    label(fig, 76, 60, "64 entries of 16 bytes", 16, AQUA, SANS)
    label(fig, 76, 53, "relocated table", 14, INK2, SERIF)
    label(fig, 76, 45, "aligned to 16 bytes,", 13, MUTED, SERIF)
    label(fig, 76, 41, "inside the plugin's own image", 13, MUTED, SERIF)

    arrow(fig, 43, 58, 57, 58, AQUA, width=3)
    label(fig, 50, 63, "14", 20, AQUA, SERIF)
    label(fig, 50, 53, "references", 13, INK2, SERIF)
    label(fig, 50, 49, "repointed", 13, INK2, SERIF)

    note(fig,
         "Every reference to the table is an absolute displacement onto entry zero's fields, at offsets 0, 4, 8 and 12. "
         "All fourteen<br>are verified against their expected values before a single byte is written; if any one "
         "disagrees, nothing is patched and revd.log says which.",
         y=0.02)
    save(fig, "fig2_relocation")


# ---------------------------------------------------------------- figure 3
def fig_waveslots():
    """What the game's own audio config actually declares."""
    eng, other = read_waveslots(WAVESLOTS)
    per = eng[0][1] if eng else 794624
    other_total = sum(s for _, s in other)
    top = sorted(other, key=lambda x: -x[1])[:6]

    fig = go.Figure()
    fig.update_layout(**base_layout(
        "What waveslots.xml declares",
        f"Parsed from the game's own audio config: {len(eng) + len(other)} slots, "
        f"{len(eng)} of them engine slots.",
        height=720, width=1280))

    names = [f"engine slot ({len(eng)} of them)"] + [n.replace('_', ' ').title() for n, _ in top]
    vals = [per / MB] + [s / MB for _, s in top]
    colors = [AQUA] + [BLUE] * len(top)

    fig.add_trace(go.Bar(
        x=vals, y=names, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.2f} MB" for v in vals], textposition="outside",
        textfont=dict(family=MONO, size=14, color=INK2),
        hoverinfo="skip", width=0.62))

    fig.update_layout(
        xaxis=dict(title="declared size, MB", showgrid=True, gridcolor=GRID,
                   zeroline=False, color=INK2, range=[0, max(vals) * 1.22],
                   title_font=dict(family=SANS, size=15, color=INK2)),
        yaxis=dict(autorange="reversed", showgrid=False, color=INK,
                   tickfont=dict(family=SANS, size=15, color=INK)),
        margin=dict(l=220, r=70, t=120, b=90))

    note(fig,
         f"One engine slot is {per:,} bytes, so sixty-four of them declare "
         f"{per * 64 / MB:.1f} MB against {per * 25 / MB:.1f} MB at stock. "
         f"The other {len(other)} slots declare {other_total / MB:.1f} MB between them,<br>"
         "which already exceeds the stock heap on its own. The heap is therefore not a simple sum of declared "
         "sizes, and its real allocation behaviour was not characterised.",
         y=-0.18)
    save(fig, "fig3_waveslots")


# ---------------------------------------------------------------- figure 4
def fig_heap():
    """Configured heap sizes, and the one thing actually observed."""
    fig = go.Figure()
    fig.update_layout(**base_layout(
        "The audio heap, and what was observed",
        "The heap is a single immediate in the executable. These are settings and outcomes, not a model.",
        height=680, width=1280))
    fig.update_xaxes(range=[0, 100], visible=False)
    fig.update_yaxes(range=[0, 100], visible=False)

    label(fig, 6, 84, "mov esi, imm32", 16, YELLOW, MONO, anchor="left")
    label(fig, 6, 78.5, "RVA 0x4C158C, patched in place", 14, INK2, SERIF, anchor="left")

    # two bars to scale
    scale = 72.0 / 192.0
    box(fig, 6, 58, 6 + 126 * scale, 68, ORANGE, ORANGE_F)
    label(fig, 8.5, 63, "126 MB   stock", 15, ORANGE, MONO, anchor="left")

    box(fig, 6, 43, 6 + 192 * scale, 53, AQUA, AQUA_F)
    label(fig, 8.5, 48, "192 MB   revd default", 15, AQUA, MONO, anchor="left")

    # observations
    label(fig, 6, 33, "Observed, 2026-09-06", 16, INK, SERIF, anchor="left")
    rows = [
        ("25 slots", "126 MB", "stock, runs", BLUE),
        ("30 slots", "126 MB", "crashes during audio init", ORANGE),
        ("64 slots", "192 MB", "runs", AQUA),
    ]
    y = 25
    for slots, heap, outcome, col in rows:
        label(fig, 8, y, slots, 15, INK, MONO, anchor="left")
        label(fig, 24, y, heap, 15, INK2, MONO, anchor="left")
        label(fig, 40, y, outcome, 15, col, SERIF, anchor="left")
        y -= 7

    note(fig,
         "Three data points, one machine, one mod stack. The crash threshold between twenty-five and thirty slots "
         "was not bisected,<br>and no reading was taken of what the allocator actually reserves, so treat 192 MB as "
         "a value known to work rather than a derived requirement.",
         y=0.04)
    save(fig, "fig4_heap")


# ---------------------------------------------------------------- figure 5
def fig_settings():
    """Everything revd changes."""
    fig = go.Figure()
    fig.update_layout(**base_layout(
        "Every value revd changes",
        "Stock read from the running process; shipped values from revd.ini.",
        height=560, width=1280))
    fig.update_xaxes(range=[0, 100], visible=False)
    fig.update_yaxes(range=[0, 100], visible=False)

    rows = [
        ("Slots", "0x58D50F", "25", "64", "probe loop bound, imm8"),
        ("(table)", "0xE832B8", "25 entries", "relocated", "14 references repointed"),
        ("AudioHeapMB", "0x4C158C", "126", "192", "physical audio heap, imm32"),
    ]
    hdr = 74
    for x, t in ((9, "setting"), (30, "address"), (50, "stock"), (66, "revd"), (80, "what it is")):
        label(fig, x, hdr, t, 14, MUTED, SERIF, anchor="left")
    fig.add_shape(type="line", x0=7, y0=hdr - 6, x1=95, y1=hdr - 6, line=dict(color=GRID, width=1))

    y = hdr - 18
    for name, rva, stock, new, what in rows:
        label(fig, 9,  y, name, 15, INK, MONO, anchor="left")
        label(fig, 30, y, rva, 14, MUTED, MONO, anchor="left")
        label(fig, 50, y, stock, 15, ORANGE, MONO, anchor="left")
        label(fig, 66, y, new, 15, AQUA, MONO, anchor="left")
        label(fig, 80, y, what, 14, INK2, SERIF, anchor="left")
        y -= 13

    note(fig,
         "All three land in the window between the executable's .text being decrypted and the audio system "
         "initialising. revd polls for that<br>window and verifies every site before writing; if the window closes "
         "first, it leaves the game stock and logs that it did.",
         y=0.06)
    save(fig, "fig5_settings")


if __name__ == "__main__":
    fig_ceiling()
    fig_relocation()
    fig_waveslots()
    fig_heap()
    fig_settings()
    print("done")
