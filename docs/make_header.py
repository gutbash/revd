"""revd Nexus header banner, 1300x372.

    python make_header.py     -> writes ./figures/header.png
"""
import os
import plotly.graph_objects as go
from figstyle import (SERIF, SANS, SURFACE, INK, INK2, MUTED,
                      BLUE, ORANGE, AQUA, BLUE_F, box, label)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT, exist_ok=True)

W, H = 1300, 372
fig = go.Figure()
fig.update_layout(
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    width=W, height=H, margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False,
    xaxis=dict(range=[0, 100], visible=False, fixedrange=True),
    yaxis=dict(range=[0, 100], visible=False, fixedrange=True),
)

# left: the name
label(fig, 6, 66, "revd", 74, INK, SERIF, anchor="left")
label(fig, 6.6, 44, "more engine audio slots for GTA IV", 27, INK2, SERIF, anchor="left")
fig.add_shape(type="line", x0=6.5, y0=34, x1=38, y1=34,
              line=dict(color=AQUA, width=2))
label(fig, 6.6, 24, "a research release", 18, MUTED, SERIF, anchor="left")

# right: the slot table, 25 voiced and the rest silent
# a banner x-unit is 13 px and a y-unit 3.72 px, so square cells need h about 3.5x w
cols, rows = 16, 4
x0, y0 = 52.0, 30.0
w, h = 1.9, 6.7
gx, gy = 0.35, 0.9
n = 0
for r in range(rows):
    for c in range(cols):
        n += 1
        voiced = n <= 25
        x = x0 + c * (w + gx)
        y = y0 + (rows - 1 - r) * (h + gy)
        box(fig, x, y, x + w, y + h,
            BLUE if voiced else ORANGE,
            BLUE_F if voiced else "rgba(0,0,0,0)",
            width=2 if voiced else 1,
            dash=None if voiced else "dot")

label(fig, 52.0, 74, "25 voiced", 16, BLUE, SANS, anchor="left")
label(fig, 70.0, 74, "39 silent", 16, ORANGE, SANS, anchor="left")
label(fig, 52.0, 19, "revd lifts the ceiling to 64", 16, AQUA, SANS, anchor="left")

fig.write_image(os.path.join(OUT, "header.png"), scale=1)
print("wrote", os.path.join(OUT, "header.png"))
