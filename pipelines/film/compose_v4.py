#!/usr/bin/env python3
"""174-second sensor film: 30-second 360° introduction plus unchanged 144-second story.
Native 24 fps, 4176 frames. Geometry and optical-path visibility come from Blender.
Occluded paths are explicit faint dashed guides, never luminous through solids.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).resolve().parent
W, H, FPS, SOURCE_FPS, DURATION = 1280, 720, 24, 24, 174
SCALE = 2
CUES = json.loads((OUT / "caption_storyboard.json").read_text())

WHITE = (239, 242, 241)
BODY = (209, 218, 220)
MUTED = (153, 171, 177)
FAINT = (75, 94, 103)
GOLD = (246, 217, 163)
PHASE_COLORS = [(170, 218, 207), (232, 199, 151), (237, 173, 152)]

# Concise titles retain the meaning of the original storyboard. Full
# storyboard captions remain in the adjacent JSON for an editable source.
TITLES = [
    "Clean windows",
    "The primary\nlight path",
    "Airborne\nparticle signal",
    "A selected\nair region",
    "Deposits on\nboth windows",
    "Inspect\nWindow 1",
    "Separate\nexposures",
    "Illuminate\nWindow 2",
    "Inspect\nWindow 2",
    "Do the window\nchecks pass?",
    "Reading\nrejected",
    "Clean.\nRecheck.",
]
CAPTIONS = [
    "Laser 1 illuminates airborne particles. Camera 2 collects their scattered light.",
    "Laser 1 crosses Window 1 and the air channel, then exits through Window 2.",
    "Particles scatter light toward Camera 2. The collection path passes through Window 2.",
    "Camera 2 selects an airborne region. The main beam continues into a shielded absorbing trap.",
    "Deposits on Window 1 and Window 2 can interfere with the particle signal.",
    "Laser 1 illuminates Window 1. Camera 1 checks surface scatter against a clean baseline.",
    "Particle measurement and window inspection use time-separated exposures.",
    "Laser 2 illuminates Window 2 from the receiver side.",
    "Camera 2 observes Window 2 in a separate diagnostic exposure.",
    "If window checks meet future calibrated limits, particle measurement may continue.",
    "Excessive window contamination: reject the particle reading and show a cleaning warning.",
    "Clean Window 1 and Window 2. Repeat both diagnostic checks before using readings again.",
]
PHASES = ["01   PARTICLE MEASUREMENT", "02   WINDOW DIAGNOSTICS", "03   CLEAN + RECHECK"]
NAMES = {
    "L1": "Laser 1", "L2": "Laser 2", "W1": "Window 1", "W2": "Window 2",
    "C1": "Camera 1", "C2": "Camera 2", "TRAP": "Shielded beam trap",
    "Particles": "Airborne particles", "C2_ROI": "Selected air region",
    "Warning": "Reading unavailable", "AIR": "Ambient air channel",
}
LABEL_NAMES = {"L1": "L1", "L2": "L2", "W1": "W1", "W2": "W2", "C1": "C1", "C2": "C2", "TRAP": "TRAP", "AIR": "AIR"}
LABEL_OFFSETS = {
    "AIR": (-100, -100), "L1": (-104, -35), "W1": (-95, -8), "C1": (-93, 59),
    "W2": (-76, 83), "C2": (77, 52), "L2": (79, 2), "TRAP": (78, -40),
}


@lru_cache(maxsize=64)
def font(size: float, weight: str = "Regular", scale: int = SCALE):
    """Bundled Apache-licensed Open Sans. Used consistently in the delivered video and editable source."""
    path = OUT / "fonts" / ("OpenSans-" + ("Semibold" if weight == "Medium" else weight) + ".ttf")
    if not path.exists():
        raise FileNotFoundError(f"Bundled font missing: {path}; prepare the pipeline using tools/project.py")
    return ImageFont.truetype(str(path), round(size * scale))


def canonical(key: str) -> str:
    return "TRAP" if key.lower() == "trap" else key


def phase(ch: int) -> int:
    return 0 if ch < 9 else (1 if ch < 15 else 2)


def chapter_at(t: float) -> int:
    return min(len(CUES) - 1, max(0, bisect.bisect_right([c["start"] for c in CUES], t) - 1))


def smoothstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def active_component(ch: int, t: float) -> tuple[str | None, float]:
    for cue in CUES[ch]["highlight_cues"]:
        if cue["start"] <= t < cue["end"]:
            fade = min((t - cue["start"]) / .35, (cue["end"] - t) / .35, 1)
            return canonical(cue["component"]), smoothstep(fade)
    return None, 0.0


def text(draw, xy, string, size, fill=WHITE, weight="Regular", tracking=0.0):
    x, y = xy
    f = font(size, weight)
    if tracking:
        for char in string:
            draw.text((round(x * SCALE), round(y * SCALE)), char, font=f, fill=fill, anchor="lt")
            x += draw.textlength(char, font=f) / SCALE + tracking
        return x
    draw.text((round(x * SCALE), round(y * SCALE)), string, font=f, fill=fill, anchor="lt")
    return x + draw.textlength(string, font=f) / SCALE


def wrap_lines(string: str, size: float, width: float, weight="Regular") -> list[str]:
    f = font(size, weight)
    result = []
    for para in string.split("\n"):
        line = ""
        for word in para.split():
            test = (line + " " + word).strip()
            if f.getlength(test) / SCALE > width and line:
                result.append(line)
                line = word
            else:
                line = test
        result.append(line)
    return result


def paragraph(draw, string, xy, width, size, fill=BODY, line_height=None, weight="Regular"):
    line_height = line_height or size * 1.38
    x, y = xy
    for line in wrap_lines(string, size, width, weight):
        text(draw, (x, y), line, size, fill, weight)
        y += line_height
    return y


def story_editorial_entries(ch: int) -> list[dict]:
    """The exact line-by-line layout shared by PIL and editable Blender type."""
    entries = []
    def add(xy, string, size, color=WHITE, weight="Regular", tracking=0.0):
        entries.append({"text": string, "x": xy[0], "y": xy[1], "size": size,
                        "color": [v / 255 for v in color], "font": weight.lower(),
                        "tracking": tracking})
    def para(string, xy, width, size, color=BODY, line_height=None, weight="Regular"):
        x, y = xy
        for line in wrap_lines(string, size, width, weight):
            add((x, y), line, size, color, weight)
            y += line_height or size * 1.38
        return y
    color = PHASE_COLORS[phase(ch + 5)]
    add((48, 45), "How the air sensor works", 23, WHITE)
    add((49, 82), "CONCEPT ANIMATION", 11.5, MUTED, "Medium", 1.45)
    add((1154, 49), f"{ch + 1:02d} / 12", 16, MUTED)
    add((898, 147), PHASES[phase(ch + 5)], 11.5, color, "Medium", 1.05)
    title_y = 185
    title_bottom = para(TITLES[ch], (896, title_y), 342, 40, WHITE, 46)
    body_y = max(305, title_bottom + 29)
    body_bottom = para(CAPTIONS[ch], (898, body_y), 329, 23, BODY, 31)
    if ch == 9:
        para("No proven numerical\nstain correction.", (898, max(501, body_bottom + 24)), 330, 17, color, 23)
    if ch == 11:
        para("Resume only after\nboth checks pass.", (898, max(515, body_bottom + 24)), 330, 17, color, 23)
    add((48, 643), "Illustrative concept. Geometry, sensor performance and optical safety are not validated.", 14, MUTED)
    add((48, 665), "Colors show function, not wavelength. Particles enlarged. Sensing and diagnostic exposures are separate.", 13.5, MUTED)
    return entries


def editorial_entries(ch: int) -> list[dict]:
    if ch >= 5:
        entries = story_editorial_entries(ch - 5)
    else:
        entries = []
        def add(x, y, string, size, color=WHITE, weight="regular", tracking=0):
            entries.append(dict(text=string,x=x,y=y,size=size,color=[c/255 for c in color],font=weight,tracking=tracking))
        add(48,45,"How the air sensor works",23)
        add(49,82,"CONCEPT ANIMATION",11.5,MUTED,"medium",1.45)
        add(1132,49,f"VIEW {ch + 1} / 5",14,MUTED)
        add(898,147,"00   MEET THE SENSOR",11.5,PHASE_COLORS[0],"medium",1.05)
        y=185
        for line in wrap_lines(CUES[ch]["title"],40,342):
            add(896,y,line,40);y+=46
        y=max(305,y+23)
        for line in wrap_lines(CUES[ch]["caption"],23,329):
            add(898,y,line,23,BODY);y+=31
        add(48,643,"Illustrative concept. Geometry, sensor performance and optical safety are not validated.",14,MUTED)
        add(48,665,"Colors show function, not wavelength. Particles enlarged. Sensing and diagnostic exposures are separate.",13.5,MUTED)
    entries.append(dict(text="Faint dashed paths are hidden-view guides, not light through solids.",x=48,y=621,size=12.5,color=[v/255 for v in MUTED],font="regular",tracking=0))
    return entries


@lru_cache(maxsize=1)
def caption_backdrop() -> Image.Image:
    """Borderless, background-colored fade protects type during close-ups."""
    width, height = W * SCALE, H * SCALE
    xmask = Image.new("L", (width, 1))
    xmask.putdata([round(247 * smoothstep((x / SCALE - 811) / 103)) for x in range(width)])
    ymask = Image.new("L", (1, height))
    ymask.putdata([round(255 * min(smoothstep((y / SCALE - 98) / 44), smoothstep((651 - y / SCALE) / 41))) for y in range(height)])
    mask = ImageChops.multiply(xmask.resize((width, height)), ymask.resize((width, height)))
    im = Image.new("RGBA", (width, height), (28, 36, 42, 0))
    im.putalpha(mask)
    return im


@lru_cache(maxsize=17)
def static_overlay(ch: int) -> Image.Image:
    """Unboxed, restrained hierarchy with ample empty space around the model."""
    im = caption_backdrop().copy()
    # Soft top and footer scrims retain legibility on purposeful closeups.
    scrim=Image.new("RGBA",im.size)
    sd=ImageDraw.Draw(scrim)
    for py in range(H*SCALE):
        y=py/SCALE
        alpha=round(210*max(smoothstep((y-592)/58),1-smoothstep((y-76)/62)))
        if alpha:sd.line((0,py,W*SCALE,py),fill=(28,36,42,alpha))
    im=Image.alpha_composite(im,scrim)
    d = ImageDraw.Draw(im)
    for entry in editorial_entries(ch):
        color = tuple(round(v * 255) for v in entry["color"])
        text(d, (entry["x"], entry["y"]), entry["text"], entry["size"], color,
             entry["font"].capitalize(), entry.get("tracking", 0))
    d.line((48 * SCALE, 700 * SCALE, 1232 * SCALE, 700 * SCALE), fill=(*FAINT, 170), width=SCALE)
    return im


def export_editorial_layout(path: Path | str = OUT / "editorial_layout.json"):
    """Export exact wrapped top-left text anchors; coordinates are pixels."""
    rows = []
    for ch in range(len(CUES)):
        for entry in editorial_entries(ch):
            rec = dict(entry)
            rec.update(start=CUES[ch]["start"], end=CUES[ch]["end"])
            rows.append(rec)
    Path(path).write_text(json.dumps(rows, indent=2) + "\n")
    return Path(path)


def export_editable_layout(metadata_path=OUT / "metadata24.json", label_path=OUT / "label_layout24.json", editorial_path=OUT / "editorial_layout.json"):
    """Export all 4176 native-frame labels and wrapped caption records for Blender."""
    raw=json.loads(Path(metadata_path).read_text())
    records=raw.get("frames",raw) if isinstance(raw,dict) else raw
    if len(records)!=DURATION*FPS:
        raise ValueError(f"Expected {DURATION*FPS} metadata frames, got {len(records)}")
    rows=[]
    for index,record in enumerate(records):
        t=index/FPS; ch=chapter_at(t);active,strength=active_component(ch,t)
        rows.append(dict(time=t,frame=index,labels=layout_labels(ch,record),active=active,strength=strength))
    Path(label_path).write_text(json.dumps(rows,separators=(",",":"))+"\n")
    export_editorial_layout(editorial_path)
    return dict(labels=str(label_path),editorial=str(editorial_path),frames=len(rows),duration=DURATION)


def normalize_metadata(metadata: Any) -> dict[str, dict]:
    if not metadata:
        return {}
    raw = metadata.get("components", metadata) if isinstance(metadata, dict) else {}
    result = {}
    for name, value in raw.items():
        name = canonical(str(name))
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            rec = {"xy": [float(value[0]), float(value[1])], "visible": True}
        elif isinstance(value, dict) and ("xy" in value or "screen" in value):
            rec = dict(value)
            rec["xy"] = rec.get("xy", rec.get("screen"))
        else:
            continue
        if len(rec["xy"]) >= 2 and all(math.isfinite(float(v)) for v in rec["xy"][:2]):
            result[name] = rec
    return result


def interpolate_metadata(a: Any, b: Any, amount: float) -> dict:
    aa, bb = normalize_metadata(a), normalize_metadata(b)
    result = {}
    for key in aa.keys() | bb.keys():
        va, vb = aa.get(key), bb.get(key)
        if va is None or vb is None:
            chosen = va if amount < .5 else vb
            if chosen is not None:
                result[key] = dict(chosen)
            continue
        rec = dict(va if amount < .5 else vb)
        for prop in ("xy", "label_xy", "label_offset"):
            if prop in va and prop in vb:
                rec[prop] = [va[prop][i] * (1 - amount) + vb[prop][i] * amount for i in range(2)]
        result[key] = rec
    return {"components": result}


def layout_labels(ch: int, metadata: Any) -> list[dict]:
    """Continuous adaptive offsets; labels follow their projected 3D anchors."""
    components = normalize_metadata(metadata)
    labels = []
    for key in LABEL_NAMES:
        if ch < 5:
            introduced = [{"AIR"},{"AIR","L1","L2"},{"AIR","L1","L2","W1","W2"},{"AIR","L1","L2","C1","C2","W1","W2"},set(LABEL_NAMES)][ch]
            if key not in introduced:
                continue
        elif key == "AIR":
            continue
        if ch == 10 and key not in ("W1", "C1", "L1"):
            continue
        if ch in (12, 13) and key not in ("W2", "C2", "L2"):
            continue
        if 5 <= ch < 9 and key in ("L2", "C1"):
            continue
        rec = components.get(key)
        if not rec or not rec.get("visible", True):
            continue
        ax, ay = map(float, rec["xy"][:2])
        if not (10 <= ax <= 855 and 96 <= ay <= 631):
            continue
        dx, dy = rec.get("label_offset", LABEL_OFFSETS[key])
        x, y = rec.get("label_xy", (ax + dx, ay + dy))
        label = LABEL_NAMES[key]
        width = font(17, "Medium").getlength(label) / SCALE
        x = min(839 - width, max(38, float(x)))
        y = min(601, max(122, float(y)))
        labels.append({"key": key, "label": label, "anchor": (ax, ay), "x": x, "y": y, "w": width, "h": 18})
    # Preserve their natural offsets, with a small smooth vertical relaxation
    # only where labels overlap. This avoids discrete layout switches on zooms.
    for _ in range(8):
        for i, a in enumerate(labels):
            for b in labels[i + 1:]:
                overlap_x = min(a["x"] + a["w"] + 9, b["x"] + b["w"] + 9) - max(a["x"] - 9, b["x"] - 9)
                overlap_y = min(a["y"] + a["h"] + 8, b["y"] + b["h"] + 8) - max(a["y"] - 8, b["y"] - 8)
                if overlap_x > 0 and overlap_y > 0:
                    sign = -1 if a["y"] <= b["y"] else 1
                    a["y"] = max(122, min(601, a["y"] + sign * overlap_y * .51))
                    b["y"] = max(122, min(601, b["y"] - sign * overlap_y * .51))
    return labels


def dashed_line(draw, pts, fill, width, dash=7, gap=7):
    """Arc-length dashes, carried through vertices so guides never look solid."""
    phase = 0.0
    for a,b in zip(pts,pts[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
        if length < 1e-6: continue
        pos=0.
        while pos < length:
            cycle=phase % (dash+gap); on=cycle < dash
            step=min(length-pos,(dash if on else dash+gap)-cycle)
            if step < 1e-6: step=min(length-pos,1e-5)
            if on:
                draw.line([(a[0]+dx*pos/length,a[1]+dy*pos/length),(a[0]+dx*(pos+step)/length,a[1]+dy*(pos+step)/length)],fill=fill,width=width)
            pos+=step;phase+=step


@lru_cache(maxsize=4)
def load_beam_masks(path):
    with Image.open(path) as image:
        rgb=image.convert("RGB")
        if rgb.size != (W,H):
            raise ValueError(f"Expected {W}x{H} beam mask, got {rgb.size}: {path}")
        # Nearest-neighbor prevents mask resampling from bleeding into hardware.
        return tuple(channel.resize((W*SCALE,H*SCALE),Image.Resampling.NEAREST) for channel in rgb.split())


def light_overlay(metadata):
    """Depth-tested visible paths and glow; hidden guides stay faint and glow-free."""
    metadata=metadata or {}
    size=(W*SCALE,H*SCALE)
    guides=Image.new("RGBA",size);dg=ImageDraw.Draw(guides)
    groups={}
    factor=max(.1,float(metadata.get("light_scale",1)))**.5
    for light in metadata.get("lights",[]):
        rgb=tuple(round(v) for v in light["color"])
        if max(rgb)<=1: rgb=tuple(round(v*255) for v in light["color"])
        hidden=bool(light.get("occluded",False));region=light.get("region",False)
        channel=int(light.get("mask_channel",0))
        if channel not in (0,1,2):raise ValueError(f"Invalid mask_channel {channel}")
        if channel not in groups:
            halo=Image.new("RGBA",size);core=Image.new("RGBA",size)
            groups[channel]=(halo,core,ImageDraw.Draw(halo),ImageDraw.Draw(core))
        halo,core,dh,dc=groups[channel]
        if "points" in light:
            pts=[(round(x*SCALE),round(y*SCALE)) for x,y in light["points"]]
            if len(pts)<2: continue
            if hidden:
                dashed_line(dg,pts,(*rgb,52 if region else 70),max(1,round(.8*SCALE)),7*SCALE,7*SCALE)
                continue
            dh.line(pts,fill=(*rgb,65 if region else 170),width=max(1,round((3 if region else 7)*SCALE*factor)))
            dc.line(pts,fill=(*rgb,145 if region else 255),width=max(1,round((.7 if region else 1.55)*SCALE*factor)))
            if not region:
                luminous=tuple(round(v*.4+255*.6) for v in rgb)
                dc.line(pts,fill=(*luminous,245),width=max(1,round(.6*SCALE*factor)))
        elif not hidden and "point" in light:
            x,y=[v*SCALE for v in light["point"]];r=1.35*SCALE*factor
            dh.ellipse((x-r*2,y-r*2,x+r*2,y+r*2),fill=(*rgb,140))
            dc.ellipse((x-r,y-r,x+r,y+r),fill=(*rgb,245))
    masks=None
    if metadata.get("mask_file"):
        mask_path=Path(metadata["mask_file"])
        if not mask_path.is_absolute():mask_path=OUT/mask_path
        masks=load_beam_masks(str(mask_path))
    result=Image.new("RGBA",size)
    for channel,(halo,core,_,__) in groups.items():
        halo=halo.filter(ImageFilter.GaussianBlur(2.2*SCALE))
        if masks is not None:
            halo.putalpha(ImageChops.multiply(halo.getchannel("A"),masks[channel]))
            core.putalpha(ImageChops.multiply(core.getchannel("A"),masks[channel]))
        result=Image.alpha_composite(result,halo)
        result=Image.alpha_composite(result,core)
    return Image.alpha_composite(result,guides)


def overlay(ch: int, t: float, metadata: Any = None) -> Image.Image:
    """Return the requested transparent PIL RGBA overlay at 1280x720."""
    ch = max(0, min(len(CUES) - 1, int(ch)))
    im = light_overlay(metadata)
    im = Image.alpha_composite(im, static_overlay(ch))
    d = ImageDraw.Draw(im)
    active, strength = active_component(ch, t)
    for rec in layout_labels(ch, metadata):
        x, y, w = rec["x"], rec["y"], rec["w"]
        ax, ay = rec["anchor"]
        selected = rec["key"] == active
        amount = strength if selected else 0
        label_color = tuple(round(WHITE[i] * (1 - amount) + GOLD[i] * amount) for i in range(3))
        leader_color = (*tuple(round(MUTED[i] * (1 - amount) + GOLD[i] * amount) for i in range(3)), round(158 + 50 * amount))
        # The short horizontal tail sits outside the text, and its angled end
        # points to the renderer's actual component position.
        right_side = x + w / 2 >= ax
        tx = x - 8 if right_side else x + w + 8
        ty = y + 9
        ex = tx - 11 if right_side else tx + 11
        d.line([(ax * SCALE, ay * SCALE), (ex * SCALE, ty * SCALE), (tx * SCALE, ty * SCALE)], fill=leader_color, width=SCALE)
        r = 1.45 * SCALE
        d.ellipse((ax * SCALE - r, ay * SCALE - r, ax * SCALE + r, ay * SCALE + r), fill=leader_color)
        d.text((round(x * SCALE), round(y * SCALE)), rec["label"], font=font(17, "Medium"), fill=(*label_color, 245), anchor="lt", stroke_width=2 * SCALE, stroke_fill=(14, 24, 31, 155))

    progress = max(0, min(1, t / DURATION))
    d.line((48 * SCALE, 700 * SCALE, (48 + 1184 * progress) * SCALE, 700 * SCALE), fill=(*PHASE_COLORS[phase(ch)], 240), width=2 * SCALE)
    return im.resize((W, H), Image.Resampling.LANCZOS)


class FrameSource:
    """Bounded-memory access to full or partial source frame sequences."""
    def __init__(self, frames: Path | str, metadata: Path | str | None = None, source_fps: float = SOURCE_FPS):
        self.frames = Path(frames)
        self.source_fps = source_fps
        self.paths = {int(p.stem[1:]): p for p in self.frames.glob("f[0-9][0-9][0-9][0-9][0-9].png")}
        if not self.paths:
            raise FileNotFoundError(f"No f00000.png-style source frames in {self.frames}")
        self.indices = sorted(self.paths)
        self.metadata = {}
        if metadata and Path(metadata).exists():
            raw = json.loads(Path(metadata).read_text())
            if isinstance(raw, dict) and "frames" in raw:
                raw = raw["frames"]
            if isinstance(raw, list):
                self.metadata = {i: rec for i, rec in enumerate(raw)}
            elif isinstance(raw, dict):
                for key, rec in raw.items():
                    try:
                        self.metadata[int(Path(str(key)).stem.lstrip("f"))] = rec
                    except ValueError:
                        continue

    @lru_cache(maxsize=4)
    def image(self, index: int) -> Image.Image:
        with Image.open(self.paths[index]) as im:
            if im.size != (W, H):
                raise ValueError(f"Expected 1280x720 frame, got {im.size}: {self.paths[index]}")
            return im.convert("RGBA")

    def meta(self, index: int) -> Any:
        if index in self.metadata:
            return self.metadata[index]
        sidecar = self.paths[index].with_suffix(".json")
        if sidecar.exists():
            self.metadata[index] = json.loads(sidecar.read_text())
        return self.metadata.get(index, {})

    def sample(self, t: float, allow_missing: bool = False) -> tuple[Image.Image, Any]:
        source_pos = max(0, t * self.source_fps)
        a = int(math.floor(source_pos + 1e-8))
        b = min(self.indices[-1], a + 1)
        a = min(self.indices[-1], a)
        if a in self.paths and abs(source_pos-a) < 1e-7:
            return self.image(a).copy(), self.meta(a)
        if a not in self.paths or b not in self.paths:
            if not allow_missing:
                raise FileNotFoundError(f"Missing source frame near t={t:.3f}: f{a:05d}.png or f{b:05d}.png")
            nearest = min(self.indices, key=lambda i: abs(i - source_pos))
            return self.image(nearest).copy(), self.meta(nearest)
        amount = max(0, min(1, source_pos - a))
        if a == b or amount < 1e-7:
            return self.image(a).copy(), self.meta(a)
        return Image.blend(self.image(a), self.image(b), amount), interpolate_metadata(self.meta(a), self.meta(b), amount)


def preview(source: FrameSource, t: float, output: Path | str | None = None) -> Image.Image:
    """Composite a review image; partial source sequences are supported."""
    base, metadata = source.sample(t, allow_missing=True)
    frame = Image.alpha_composite(base, overlay(chapter_at(t), t, metadata)).convert("RGB")
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        frame.save(output, quality=96, subsampling=0)
    return frame


def compose(source: FrameSource, output: Path | str, fps: int = FPS, duration: float = DURATION, crf: int = 18):
    expected = math.ceil(duration * source.source_fps)
    missing = [i for i in range(expected) if i not in source.paths]
    if missing:
        raise FileNotFoundError(f"{len(missing)} source frames are missing; first missing index {missing[0]}. Use --preview while rendering.")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for index in range(round(duration * fps)):
            t = index / fps
            base, metadata = source.sample(t)
            frame = Image.alpha_composite(base, overlay(chapter_at(t), t, metadata)).convert("RGB")
            process.stdin.write(frame.tobytes())
            if index and index % (10 * fps) == 0:
                print(f"Composited {t:.0f} / {duration:g} seconds", flush=True)
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("ffmpeg encoding failed")
    except BaseException:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
        if process.poll() is None:
            process.terminate()
        process.wait()
        raise
    print(output, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--frames", type=Path, default=OUT / "frames24")
    parser.add_argument("--metadata", type=Path, default=OUT / "metadata24.json")
    parser.add_argument("--output", type=Path, default=OUT / "Sensor_Mechanism_Panorama_174s.mp4")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--indices", type=int, nargs="+")
    parser.add_argument("--times", type=float, nargs="+")
    parser.add_argument("--preview-dir", type=Path, default=OUT)
    parser.add_argument("--source-fps", type=float, default=SOURCE_FPS)
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--duration", type=float, default=DURATION)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--export-layout", action="store_true", help="Write editable per-line editorial_layout.json without requiring frames")
    args = parser.parse_args()
    if args.export_layout:
        print(export_editorial_layout())
        if not args.preview:
            return
    source = FrameSource(args.frames, args.metadata, args.source_fps)
    if args.preview:
        times = args.times or ([i / args.source_fps for i in args.indices] if args.indices else [3, 9, 15, 21, 27, 32, 86, 106, 135])
        for t in times:
            path = args.preview_dir / f"preview_{t:06.2f}s.jpg"
            preview(source, t, path)
            print(path)
    else:
        compose(source, args.output, args.fps, args.duration, args.crf)


if __name__ == "__main__":
    main()
