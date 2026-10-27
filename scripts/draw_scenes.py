"""Build editable Excalidraw figure specifications from the numerical summary.

Coordinates represent the actual data. Excalidraw supplies the sketch strokes,
not noise added to the measurements. Every mark remains a native element.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INK, BLUE, ORANGE, GRAY, LIGHT = "#1e1e1e", "#1971c2", "#e8590c", "#6b7280", "#d9dde2"


class Scene:
    def __init__(self, name, width=1650, height=800):
        self.name, self.width, self.height = name, width, height
        self.elements = []
        self.add("rectangle", 0, 0, width=width, height=height, opacity=0,
                 customData={"role": "canvas"})

    def add(self, kind, x, y, **kw):
        identity = f"{self.name}_{len(self.elements):04d}"
        seed = int(hashlib.sha256(identity.encode()).hexdigest()[:7], 16)
        element = {"type": kind, "id": identity, "x": x, "y": y, "strokeColor": INK,
            "backgroundColor": "transparent", "fillStyle": "hachure", "strokeWidth": 1.4,
            "strokeStyle": "solid", "roughness": 1, "opacity": 100, "seed": seed, **kw}
        self.elements.append(element)
        return element

    def text(self, x, y, text, size=23, color=INK, align="left", **kw):
        return self.add("text", x, y, text=text, fontFamily=1, fontSize=size,
            strokeColor=color, lineHeight=1.3,
            customData={"anchorX": x, "align": align, "role": "label"}, **kw)

    def line(self, points, color=INK, width=1.4, style="solid", arrow=False, **kw):
        x, y = points[0]
        return self.add("arrow" if arrow else "line", x, y,
            points=[[px-x, py-y] for px, py in points], strokeColor=color,
            strokeWidth=width, strokeStyle=style,
            **({"endArrowhead": "arrow", "startArrowhead": None} if arrow else {}), **kw)

    def rect(self, x, y, w, h, color=INK, fill="transparent", **kw):
        return self.add("rectangle", x, y, width=w, height=h, strokeColor=color,
                        backgroundColor=fill, **kw)

    def dot(self, x, y, color=INK, filled=True, square=False, radius=7, **kw):
        return self.add("rectangle" if square else "ellipse", x-radius, y-radius,
            width=radius*2, height=radius*2, strokeColor=color, fillStyle="solid",
            backgroundColor=color if filled else "#ffffff", strokeWidth=1.6, **kw)

    def header(self, title, subtitle):
        self.text(45, 25, title, 43)
        self.text(48, 98, subtitle, 23, GRAY)

    def note(self, text, y=None):
        self.text(48, y if y is not None else self.height-90, text, 21, GRAY)

    def spec(self):
        return {"name": self.name, "width": self.width, "height": self.height,
                "elements": self.elements}


def overview(s):
    c = Scene("overview", height=610)
    c.text(45, 25, "Almubdi Mutaikhan / research notes", 23, GRAY)
    c.text(45, 80, "LLM judges + creative selection", 52)
    c.text(50, 162, "How do models judge ideas, and do they repeat their choices?", 28)
    for x, title, body in [(65, "generated ideas", "TRIZ / control answers\ncreative concept sets"),
                            (610, "blind evaluation", "judge / generator families\nfixed or changed order"),
                            (1200, "measurements", "preferences + rankings\nwhich ideas are removed")]:
        w = 400 if x < 1000 else 330
        c.rect(x, 245, w, 155, BLUE if x == 610 else INK, "#e7f5ff" if x == 610 else "transparent")
        c.text(x+22, 261, title, 28, BLUE if x == 610 else INK)
        c.text(x+22, 317, body, 22)
    c.line([(480, 325), (590, 325)], arrow=True)
    c.line([(1030, 325), (1180, 325)], arrow=True)
    c.text(67, 445, "45 engineering cases / four judge models", 27)
    c.text(67, 500, "Creative-selection follow-ups: one Mars-boot problem", 23, GRAY)
    r = s["jury"]["family_interaction"]
    c.text(1000, 445, "Judge / generator effects", 25, BLUE)
    c.text(1000, 491, f"TRIZ choice: {r['mean']*100:+.2f} pp within family", 23)
    c.text(1000, 530, "45 cases; not a direct self-preference test", 20, GRAY)
    return c


def build():
    summary = json.loads((ROOT / "results/summary.json").read_text())
    out = ROOT / "tmp/excalidraw-specs.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps([overview(summary).spec()], indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(build())
