"""Convert the Nexus BBCode draft to HTML, so it can be pasted into the WYSIWYG editor.

The editor stores BBCode but only accepts real formatting through a paste; pasting the raw
BBCode inserts it as literal text. Pasting HTML makes the editor build its own model, which
it then serialises back to BBCode on save.
"""
import re
import sys
import html as _html


def convert(bb: str) -> str:
    out = []
    lines = bb.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("[code]") or line.strip() == "[code]":
            block = [re.sub(r"^\s*\[code\]", "", line)]
            while "[/code]" not in block[-1] and i + 1 < len(lines):
                i += 1
                block.append(lines[i])
            block[-1] = block[-1].replace("[/code]", "")
            body = "\n".join(block).strip("\n")
            out.append("<pre>" + _html.escape(body) + "</pre>")
            i += 1
            continue

        if line.strip() in ("[list]", "[list=1]"):
            tag = "ol" if "=1" in line else "ul"
            items = []
            i += 1
            while i < len(lines) and lines[i].strip() != "[/list]":
                s = lines[i].strip()
                if s.startswith("[*]"):
                    items.append(inline(s[3:]))
                elif items:
                    items[-1] += " " + inline(s)
                i += 1
            i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % t for t in items), tag))
            continue

        if not line.strip():
            i += 1
            continue

        m = re.fullmatch(r"\[size=(\d)\]\[b\](.*?)\[/b\]\[/size\]", line.strip())
        if m:
            lvl = {"5": "h2", "4": "h3", "3": "h4"}.get(m.group(1), "h3")
            out.append("<%s>%s</%s>" % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue

        out.append("<p>%s</p>" % inline(line))
        i += 1

    return "<div>" + "\n".join(out) + "</div>"


def inline(s: str) -> str:
    s = _html.escape(s)
    s = re.sub(r"\[url=(.*?)\](.*?)\[/url\]", r'<a href="\1">\2</a>', s)
    s = re.sub(r"\[b\](.*?)\[/b\]", r"<b>\1</b>", s)
    s = re.sub(r"\[i\](.*?)\[/i\]", r"<i>\1</i>", s)
    s = re.sub(r"\[size=\d\](.*?)\[/size\]", r"\1", s)
    return s


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    open(dst, "w", encoding="utf-8").write(convert(open(src, encoding="utf-8").read()))
    print("wrote", dst)
