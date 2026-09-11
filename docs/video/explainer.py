"""revd explainer.

    manim -qh explainer.py Explainer

Text only, no LaTeX. Type is CMU (Computer Modern), matching the figures.
Note: CMU has no U+00D7 or U+2192, so no multiplication signs or arrows in any string here.
"""
from manim import *

BG     = "#1a1a19"
PANEL  = "#232320"
INK    = "#f2f0ea"
INK2   = "#b8b4a8"
MUTED  = "#7d7a70"
GRID   = "#3a3a36"
BLUE   = "#3987e5"
ORANGE = "#d95926"
AQUA   = "#199e70"
YELLOW = "#c98500"

SERIF = "CMU Serif"
SANS  = "CMU Sans Serif"
MONO  = "CMU Typewriter Text"

config.background_color = BG


def T(s, size=28, color=INK, font=SERIF, weight=NORMAL):
    return Text(s, font=font, font_size=size, color=color, weight=weight)


def rbox(w, h, stroke=GRID, fill=PANEL, r=0.12, op=1.0):
    return RoundedRectangle(width=w, height=h, corner_radius=r,
                            stroke_color=stroke, stroke_width=2,
                            fill_color=fill, fill_opacity=op)


class Explainer(Scene):
    def construct(self):
        self.title()
        self.problem()
        self.per_model()
        self.the_wall()
        self.relocate()
        self.heap()
        self.waveslots()
        self.limits()
        self.outro()

    def wipe(self):
        stuff = list(self.mobjects)
        if stuff:
            self.play(*[FadeOut(m) for m in stuff], run_time=0.5)

    # ------------------------------------------------------------------
    def title(self):
        name = T("revd", 100, INK, SERIF)
        sub = T("more engine audio slots for GTA IV", 34, INK2, SERIF)
        rule = Line(LEFT * 3.2, RIGHT * 3.2, color=AQUA, stroke_width=2)
        tag = T("a research release", 24, MUTED, SERIF)
        VGroup(name, sub, rule, tag).arrange(DOWN, buff=0.36)
        rule.set_width(5.6)
        self.play(FadeIn(name, shift=UP * 0.3), run_time=0.9)
        self.play(FadeIn(sub), Create(rule), run_time=0.7)
        self.play(FadeIn(tag), run_time=0.5)
        self.wait(1.4)
        self.wipe()

    # ------------------------------------------------------------------
    def problem(self):
        head = T("Some cars make no sound", 46, INK, SERIF).to_edge(UP, buff=0.8)
        self.play(FadeIn(head), run_time=0.6)

        cars = VGroup()
        for i in range(9):
            body = RoundedRectangle(width=1.05, height=0.52, corner_radius=0.12,
                                    stroke_color=GRID, stroke_width=2,
                                    fill_color=PANEL, fill_opacity=1)
            cars.add(body)
        cars.arrange(RIGHT, buff=0.28).shift(UP * 0.6)
        self.play(LaggedStart(*[FadeIn(c, shift=LEFT * 0.3) for c in cars],
                              lag_ratio=0.09), run_time=1.2)

        voiced = [0, 1, 3, 5, 8]
        waves, silents = VGroup(), VGroup()
        for i, c in enumerate(cars):
            if i in voiced:
                a = Arc(radius=0.30, start_angle=PI / 4, angle=PI / 2,
                        stroke_color=BLUE, stroke_width=3).next_to(c, UP, buff=0.08)
                waves.add(a)
                c.set_stroke(BLUE)
            else:
                x = T("silent", 18, ORANGE, SERIF).next_to(c, DOWN, buff=0.22)
                silents.add(x)
                c.set_stroke(ORANGE)
        self.play(FadeIn(waves), FadeIn(silents), run_time=0.9)

        msg = T("and which ones are silent keeps changing", 28, INK2, SERIF).shift(DOWN * 1.9)
        self.play(FadeIn(msg), run_time=0.6)
        msg2 = T("nothing is broken", 26, MUTED, SERIF).shift(DOWN * 2.7)
        self.play(FadeIn(msg2), run_time=0.5)
        self.wait(1.7)
        self.wipe()

    # ------------------------------------------------------------------
    def per_model(self):
        head = T("One sound per distinct model", 44, INK, SERIF).to_edge(UP, buff=0.8)
        sub = T("not per vehicle", 28, INK2, SERIF).next_to(head, DOWN, buff=0.25)
        self.play(FadeIn(head), FadeIn(sub), run_time=0.7)

        # three of the same model share one slot
        group = VGroup()
        for _ in range(3):
            group.add(RoundedRectangle(width=1.0, height=0.5, corner_radius=0.12,
                                       stroke_color=BLUE, stroke_width=2,
                                       fill_color="#16283f", fill_opacity=1))
        group.arrange(RIGHT, buff=0.3).shift(LEFT * 3.4 + UP * 0.2)
        glab = T("three of the same model", 22, INK2, SERIF).next_to(group, DOWN, buff=0.3)

        slot = rbox(2.4, 0.9, AQUA, "#0e2c22").shift(RIGHT * 3.2 + UP * 0.2)
        slot_t = T("one slot", 24, AQUA, SANS).move_to(slot)

        arr = Arrow(group.get_right() + RIGHT * 0.15, slot.get_left(), buff=0.12,
                    color=MUTED, stroke_width=3, max_tip_length_to_length_ratio=0.18)

        self.play(FadeIn(group), FadeIn(glab), run_time=0.7)
        self.play(GrowArrow(arr), FadeIn(VGroup(slot, slot_t)), run_time=0.7)

        note = T("so variety is what costs slots, not traffic volume",
                 26, INK2, SERIF).shift(DOWN * 2.3)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(1.8)
        self.wipe()

    # ------------------------------------------------------------------
    def the_wall(self):
        head = T("There are twenty-five", 44, INK, SERIF).to_edge(UP, buff=0.7)
        self.play(FadeIn(head), run_time=0.6)

        cells = VGroup()
        for i in range(64):
            on = i < 25
            c = Square(side_length=0.42,
                       stroke_color=BLUE if on else ORANGE,
                       stroke_width=2 if on else 1.2,
                       fill_color="#16283f" if on else BG,
                       fill_opacity=1 if on else 0)
            cells.add(c)
        cells.arrange_in_grid(rows=4, cols=16, buff=0.13).shift(UP * 0.35)
        self.play(LaggedStart(*[FadeIn(c) for c in cells[:25]], lag_ratio=0.02), run_time=1.1)

        lab1 = T("the whole table", 24, BLUE, SERIF).next_to(cells, UP, buff=0.35)
        self.play(FadeIn(lab1), run_time=0.4)
        self.wait(0.7)

        self.play(LaggedStart(*[FadeIn(c) for c in cells[25:]], lag_ratio=0.012), run_time=1.0)
        lab2 = T("everything past it: no slot, no sound", 26, ORANGE, SERIF).shift(DOWN * 1.9)
        self.play(FadeIn(lab2), run_time=0.5)

        code = T("cmp edi, 0x19", 34, YELLOW, MONO).shift(DOWN * 2.8)
        self.play(FadeIn(code), run_time=0.6)
        self.wait(1.7)
        self.wipe()

    # ------------------------------------------------------------------
    def relocate(self):
        head = T("The table cannot grow where it is", 42, INK, SERIF).to_edge(UP, buff=0.7)
        self.play(FadeIn(head), run_time=0.6)

        exe = rbox(4.6, 4.0, GRID, PANEL).shift(LEFT * 3.5 + DOWN * 0.4)
        exe_l = T("GTAIV.exe", 24, INK2, MONO).next_to(exe, UP, buff=0.22)

        tbl = rbox(3.9, 1.6, BLUE, "#16283f").move_to(exe.get_center() + UP * 0.85)
        tbl_t = VGroup(T("slot table", 22, BLUE, SANS),
                       T("0xE832B8", 19, MUTED, MONO)).arrange(DOWN, buff=0.12).move_to(tbl)

        occ = rbox(3.9, 1.3, ORANGE, "#3b1d10").move_to(exe.get_center() + DOWN * 0.95)
        occ_t = VGroup(T("occupied", 22, ORANGE, SANS),
                       T("unrelated statics", 19, INK2, SERIF)).arrange(DOWN, buff=0.12).move_to(occ)

        self.play(FadeIn(exe), FadeIn(exe_l), run_time=0.5)
        self.play(FadeIn(VGroup(tbl, tbl_t)), run_time=0.5)
        self.play(FadeIn(VGroup(occ, occ_t)), run_time=0.5)
        self.wait(0.8)

        asi = rbox(4.6, 4.0, AQUA, "#0e2c22").shift(RIGHT * 3.5 + DOWN * 0.4)
        asi_l = T("revd.asi", 24, AQUA, MONO).next_to(asi, UP, buff=0.22)
        big = rbox(3.9, 3.0, AQUA, "#123528").move_to(asi.get_center())
        big_t = VGroup(T("64 entries", 24, AQUA, SANS),
                       T("relocated", 20, INK2, SERIF)).arrange(DOWN, buff=0.14).move_to(big)

        self.play(FadeIn(asi), FadeIn(asi_l), run_time=0.5)
        self.play(FadeIn(VGroup(big, big_t)), run_time=0.6)

        arr = Arrow(exe.get_right(), asi.get_left(), buff=0.15, color=AQUA,
                    stroke_width=4, max_tip_length_to_length_ratio=0.15)
        n14 = T("14 references", 24, AQUA, SERIF).next_to(arr, UP, buff=0.18)
        n14b = T("repointed", 20, INK2, SERIF).next_to(arr, DOWN, buff=0.18)
        self.play(GrowArrow(arr), FadeIn(n14), FadeIn(n14b), run_time=0.8)

        chk = T("all fourteen verified before a single byte is written",
                24, MUTED, SERIF).shift(DOWN * 3.2)
        self.play(FadeIn(chk), run_time=0.6)
        self.wait(1.7)
        self.wipe()

    # ------------------------------------------------------------------
    def heap(self):
        head = T("The heap has to move too", 44, INK, SERIF).to_edge(UP, buff=0.8)
        self.play(FadeIn(head), run_time=0.6)

        b1 = Rectangle(width=4.2, height=0.7, stroke_color=ORANGE, stroke_width=2,
                       fill_color="#3b1d10", fill_opacity=1).shift(UP * 1.1 + LEFT * 1.5)
        t1 = T("126 MB  stock", 24, ORANGE, MONO).next_to(b1, RIGHT, buff=0.35)
        b2 = Rectangle(width=6.4, height=0.7, stroke_color=AQUA, stroke_width=2,
                       fill_color="#0e2c22", fill_opacity=1).shift(UP * 0.1 + LEFT * 0.4)
        t2 = T("192 MB  revd", 24, AQUA, MONO).next_to(b2, RIGHT, buff=0.35)
        b1.align_to(b2, LEFT)
        t1.next_to(b1, RIGHT, buff=0.35)

        self.play(FadeIn(b1), FadeIn(t1), run_time=0.6)
        self.play(FadeIn(b2), FadeIn(t2), run_time=0.6)

        obs = VGroup(
            T("30 slots on the stock heap:  crashes", 26, ORANGE, SERIF),
            T("64 slots on 192 MB:  runs", 26, AQUA, SERIF),
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT).shift(DOWN * 1.6)
        self.play(FadeIn(obs[0]), run_time=0.5)
        self.play(FadeIn(obs[1]), run_time=0.5)

        honest = T("observed, not derived", 22, MUTED, SERIF).shift(DOWN * 2.9)
        self.play(FadeIn(honest), run_time=0.5)
        self.wait(1.7)
        self.wipe()

    # ------------------------------------------------------------------
    def waveslots(self):
        head = T("Half the fix is a text file", 42, INK, SERIF).to_edge(UP, buff=0.8)
        self.play(FadeIn(head), run_time=0.6)

        body = VGroup(
            T("the game looks slots up by name", 30, INK, SERIF),
            T("", 10),
            T("STREAM_ENGINE_26", 26, YELLOW, MONO),
            T("", 10),
            T("if waveslots.xml does not declare it,", 26, INK2, SERIF),
            T("the slot stays empty", 26, INK2, SERIF),
        ).arrange(DOWN, buff=0.22).shift(UP * 0.3)
        self.play(FadeIn(body[0]), run_time=0.5)
        self.play(FadeIn(body[2]), run_time=0.5)
        self.play(FadeIn(body[4]), FadeIn(body[5]), run_time=0.6)
        self.wait(0.8)

        # revd 0.2.0 declares them itself, so there is nothing for you to run
        self.play(FadeOut(body[0]), FadeOut(body[2]), FadeOut(body[4]), FadeOut(body[5]),
                  run_time=0.5)
        lead = VGroup(
            T("revd declares them for you,", 32, AQUA, SERIF),
            T("at load, before the audio starts", 32, AQUA, SERIF),
        ).arrange(DOWN, buff=0.3).shift(UP * 0.75)
        detail = VGroup(
            T("only the missing ones are added,", 24, INK2, SERIF),
            T("and the original is backed up first", 24, INK2, SERIF),
        ).arrange(DOWN, buff=0.26).shift(DOWN * 1.15)
        self.play(FadeIn(lead), run_time=0.7)
        self.play(FadeIn(detail), run_time=0.6)

        foot = T("no script, nothing to edit by hand", 24, MUTED, SERIF).shift(DOWN * 2.9)
        self.play(FadeIn(foot), run_time=0.6)
        self.wait(1.7)
        self.wipe()

    # ------------------------------------------------------------------
    def limits(self):
        head = T("What was not measured", 42, INK, SERIF).to_edge(UP, buff=0.8)
        self.play(FadeIn(head), run_time=0.6)

        items = [
            "the exact crash threshold on the stock heap",
            "what the allocator really reserves per slot",
            "any effect on the mix, or on CPU cost",
            "any build other than 1.2.0.59",
        ]
        g = VGroup()
        for s in items:
            d = Dot(radius=0.055, color=ORANGE)
            t = T(s, 26, INK2, SERIF)
            g.add(VGroup(d, t).arrange(RIGHT, buff=0.35))
        g.arrange(DOWN, buff=0.42, aligned_edge=LEFT).shift(UP * 0.05)
        for row in g:
            self.play(FadeIn(row, shift=RIGHT * 0.15), run_time=0.4)

        foot = T("192 MB is a value known to work, not a computed requirement",
                 23, MUTED, SERIF).shift(DOWN * 2.7)
        self.play(FadeIn(foot), run_time=0.6)
        self.wait(1.8)
        self.wipe()

    # ------------------------------------------------------------------
    def outro(self):
        name = T("revd", 80, INK, SERIF)
        url = T("github.com/gutbash/revd", 30, AQUA, MONO)
        rule = Line(LEFT * 2.6, RIGHT * 2.6, color=GRID, stroke_width=2)
        comp = T("companion release:  popctl", 26, INK2, SERIF)
        comp2 = T("moves the pedestrian and traffic keep radius", 22, MUTED, SERIF)
        lic = T("MIT   ·   one mod, one job", 22, MUTED, SERIF)
        VGroup(name, url, rule, comp, comp2, lic).arrange(DOWN, buff=0.3)
        rule.set_width(6.0)
        self.play(FadeIn(name, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(url), Create(rule), run_time=0.6)
        self.play(FadeIn(comp), FadeIn(comp2), run_time=0.6)
        self.play(FadeIn(lic), run_time=0.5)
        self.wait(2.4)
