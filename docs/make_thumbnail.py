"""revd gallery thumbnail, 1920x1080.

Designed to survive being shrunk to a ~300 px mod card: three text elements, one shape,
thick strokes. Nothing here is meant to be read at full size.

    python make_thumbnail.py     -> writes ./figures/thumbnail.png
"""
import os
import plotly.graph_objects as go
from figstyle import SERIF, SANS, SURFACE, INK, INK2, MUTED, BLUE, ORANGE, AQUA, box, label

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT, exist_ok=True)

W, H = 1920, 1080
fig = go.Figure()
fig.update_layout(
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    width=W, height=H, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
    xaxis=dict(range=[0, 100], visible=False, fixedrange=True),
    yaxis=dict(range=[0, 100], visible=False, fixedrange=True),
)

# ---- right: 64 slots, the first 25 voiced. 8x8 keeps the cells chunky.
cols, rows = 8, 8
x0, y0 = 55.0, 14.0
w, h = 3.6, 6.4
gx, gy = 1.0, 1.8
n = 0
for r in range(rows):
    for c in range(cols):
        n += 1
        voiced = n <= 25
        x = x0 + c * (w + gx)
        y = y0 + (rows - 1 - r) * (h + gy)
        box(fig, x, y, x + w, y + h,
            BLUE if voiced else ORANGE,
            "rgba(57,135,229,0.55)" if voiced else "rgba(0,0,0,0)",
            width=6 if voiced else 4)

# ---- left: wordmark and the one number that matters
label(fig, 7, 70, "revd", 150, INK, SERIF, anchor="left")
fig.add_shape(type="line", x0=7.5, y0=58, x1=38, y1=58, line=dict(color=AQUA, width=6))
label(fig, 7.5, 50, "engine sounds for cars", 50, INK2, SERIF, anchor="left")
label(fig, 7.5, 43, "that had none", 50, INK2, SERIF, anchor="left")

label(fig, 7.5, 27, "25", 86, ORANGE, SANS, anchor="left")
label(fig, 14.5, 26, "to", 46, MUTED, SERIF, anchor="left")
label(fig, 20.5, 27, "64 slots", 86, AQUA, SANS, anchor="left")

fig.write_image(os.path.join(OUT, "thumbnail.png"), scale=1)
print("wrote", os.path.join(OUT, "thumbnail.png"))
