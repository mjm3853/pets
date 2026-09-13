"""
Build the moment graph from a raw photo dump.

The load-bearing idea (see docs/data-model.md): a file is not a moment.
People burst-shoot — ten frames in forty seconds is one event, not ten.
So ingest runs: media -> detection -> burst clustering -> moments -> eras.

Usage:
    uv run ingest.py "/path/to/photos" --pet Izzy --out moments.json
"""

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

PET_CLASSES = {"dog", "cat", "bird", "horse", "sheep", "cow", "bear"}
MEDIA_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov"}

# Two frames closer together than this belong to the same burst.
BURST_GAP = timedelta(minutes=20)

FILENAME_DATE = re.compile(r"(\d{8})[_-](\d{6})")


def parse_time(path: Path, exif: dict) -> tuple[str | None, str]:
    """Capture time, preferring EXIF, falling back to the filename, then mtime."""
    raw = exif.get(36867) or exif.get(306)
    if raw:
        try:
            return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S").isoformat(), "exif"
        except ValueError:
            pass
    m = FILENAME_DATE.search(path.name)
    if m:
        try:
            return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").isoformat(), "filename"
        except ValueError:
            pass
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(), "mtime"


def gps_coords(exif) -> list[float] | None:
    try:
        g = exif.get_ifd(34853)
        if not g:
            return None
        def dec(vals, ref):
            d = float(vals[0]) + float(vals[1]) / 60 + float(vals[2]) / 3600
            return -d if ref in ("S", "W") else d
        return [round(dec(g[2], g[1]), 5), round(dec(g[4], g[3]), 5)]
    except Exception:
        return None


def variant(name: str) -> str:
    for tag in ("PORTRAIT", "NIGHT", "COLLAGE", "MP"):
        if f".{tag}" in name or f"-{tag}" in name:
            return {"MP": "motion", "PORTRAIT": "portrait", "NIGHT": "night", "COLLAGE": "collage"}[tag]
    return "photo"


def scan(root: Path, model: YOLO, conf: float) -> list[dict]:
    paths = sorted(p for p in root.rglob("*") if p.suffix.lower() in MEDIA_EXTS | VIDEO_EXTS)
    media = []
    for i, path in enumerate(paths, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(paths)}")
        is_video = path.suffix.lower() in VIDEO_EXTS
        exif, size = {}, None
        if not is_video:
            try:
                img = Image.open(path)
                size, exif = img.size, img.getexif()
            except Exception:
                pass
        taken_at, source = parse_time(path, exif)

        rec = {
            "file": path.name,
            "taken_at": taken_at,
            "time_source": source,
            "kind": "video" if is_video else variant(path.name),
            "device": exif.get(272) if exif else None,
            "gps": gps_coords(exif) if exif else None,
            "width": size[0] if size else None,
            "height": size[1] if size else None,
            "pet": False,
            "people": 0,
            "box": None,
            "score": 0.0,
        }

        if not is_video:
            try:
                r = model(str(path), conf=conf, verbose=False)[0]
                names = [r.names[int(c)] for c in r.boxes.cls]
                scores = r.boxes.conf.tolist()
                boxes = r.boxes.xyxyn.tolist()
                best = -1
                for j, n in enumerate(names):
                    if n in PET_CLASSES and scores[j] > rec["score"]:
                        rec["pet"], rec["score"], best = True, round(scores[j], 3), j
                        rec["species"] = n
                if best >= 0:
                    rec["box"] = [round(v, 4) for v in boxes[best]]
                rec["people"] = sum(1 for n in names if n == "person")
            except Exception as e:
                rec["error"] = str(e)[:80]
        media.append(rec)
    return media


def build_moments(media: list[dict]) -> list[dict]:
    """Group media into bursts. A moment is what a person would call one event."""
    media = sorted(media, key=lambda m: m["taken_at"])
    moments, cur = [], []

    def quality(g):
        """A good hero frame is a confident detection that fills the frame."""
        if not g["box"] or g["kind"] == "video":
            return 0.0
        x0, y0, x1, y1 = g["box"]
        return round(g["score"] * ((x1 - x0) * (y1 - y0)) ** 0.5, 4)

    def close(group):
        if not group:
            return
        times = [datetime.fromisoformat(g["taken_at"]) for g in group]
        withpet = [g for g in group if g["pet"]]
        hero = max(withpet or group, key=quality)
        moments.append({
            "id": f"m{len(moments):04d}",
            "started_at": min(times).isoformat(),
            "ended_at": max(times).isoformat(),
            "date": min(times).date().isoformat(),
            "span_seconds": int((max(times) - min(times)).total_seconds()),
            "media_count": len(group),
            "pet_count": len(withpet),
            "has_pet": bool(withpet),
            "dated": all(g["time_source"] != "mtime" for g in group),
            "hero_quality": quality(hero),
            "with_people": any(g["people"] > 0 for g in group),
            "kinds": sorted({g["kind"] for g in group}),
            "device": next((g["device"] for g in group if g["device"]), None),
            "gps": next((g["gps"] for g in group if g["gps"]), None),
            "hero": hero["file"],
            "hero_box": hero["box"],
            "files": [g["file"] for g in group],
        })

    for m in media:
        t = datetime.fromisoformat(m["taken_at"])
        same_source = not cur or cur[-1]["time_source"] == m["time_source"]
        if cur and (not same_source
                    or t - datetime.fromisoformat(cur[-1]["taken_at"]) > BURST_GAP):
            close(cur)
            cur = []
        cur.append(m)
    close(cur)
    return moments


def build_eras(moments: list[dict]) -> list[dict]:
    """Chapters are life years anchored on the first photo, not calendar years.

    Gap-based segmentation was tried first and produced a single era: a
    well-photographed pet has no long silences. Life years match how people
    actually narrate a pet ("the first year") and need no tuning.
    """
    pet = [m for m in moments if m["has_pet"] and m["dated"]]
    if not pet:
        return []
    start = datetime.fromisoformat(pet[0]["started_at"])
    eras = []
    for yr in range(20):
        lo = start.replace(year=start.year + yr)
        hi = start.replace(year=start.year + yr + 1)
        chunk = [m for m in pet if lo <= datetime.fromisoformat(m["started_at"]) < hi]
        if not chunk:
            if lo > datetime.fromisoformat(pet[-1]["started_at"]):
                break
            continue
        eras.append({
            "id": f"e{yr:02d}",
            "index": yr,
            "label": "First year" if yr == 0 else f"Year {yr + 1}",
            "start": chunk[0]["date"],
            "end": chunk[-1]["date"],
            "moments": len(chunk),
            "media": sum(m["media_count"] for m in chunk),
            "with_people": sum(1 for m in chunk if m["with_people"]),
            "hero": max(chunk, key=lambda m: m["hero_quality"])["hero"],
        })
    return eras


def build_milestones(moments: list[dict], media: list[dict]) -> list[dict]:
    """Facts worth telling a person, derived rather than entered."""
    pet = [m for m in moments if m["has_pet"] and m["dated"]]
    if not pet:
        return []
    out = [
        {"kind": "first", "date": pet[0]["date"], "label": "First photo", "moment": pet[0]["id"]},
        {"kind": "latest", "date": pet[-1]["date"], "label": "Most recent photo", "moment": pet[-1]["id"]},
    ]
    busiest = max(pet, key=lambda m: m["media_count"])
    out.append({"kind": "busiest_moment", "date": busiest["date"],
                "label": f"Longest single burst — {busiest['media_count']} frames", "moment": busiest["id"]})

    by_day = Counter(m["date"] for m in pet)
    day, n = by_day.most_common(1)[0]
    out.append({"kind": "busiest_day", "date": day, "label": f"Most photographed day — {n} moments"})

    gaps = [(datetime.fromisoformat(b["started_at"]) - datetime.fromisoformat(a["ended_at"]), a, b)
            for a, b in zip(pet, pet[1:])]
    if gaps:
        g, a, b = max(gaps, key=lambda x: x[0])
        out.append({"kind": "longest_gap", "date": b["date"],
                    "label": f"Longest quiet stretch — {g.days} days", "moment": b["id"]})

    start = datetime.fromisoformat(pet[0]["started_at"])
    for yr in range(1, 20):
        target = start.replace(year=start.year + yr)
        if target > datetime.fromisoformat(pet[-1]["ended_at"]):
            break
        near = min(pet, key=lambda m: abs(datetime.fromisoformat(m["started_at"]) - target))
        if abs(datetime.fromisoformat(near["started_at"]) - target) < timedelta(days=21):
            out.append({"kind": "anniversary", "date": near["date"],
                        "label": f"Year {yr}", "moment": near["id"]})
    return sorted(out, key=lambda m: m["date"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos", type=Path)
    ap.add_argument("--pet", default="Pet")
    ap.add_argument("--out", type=Path, default=Path("moments.json"))
    ap.add_argument("--conf", type=float, default=0.30)
    ap.add_argument("--model", default="yolov8n.pt")
    args = ap.parse_args()

    print(f"Scanning {args.photos}")
    media = scan(args.photos, YOLO(args.model), args.conf)
    moments = build_moments(media)
    eras = build_eras(moments)
    milestones = build_milestones(moments, media)

    pet_media = [m for m in media if m["pet"]]
    pet_moments = [m for m in moments if m["has_pet"] and m["dated"]]
    undated = [m for m in moments if not m["dated"]]
    doc = {
        "pet": {"name": args.pet,
                "species": Counter(m.get("species") for m in pet_media).most_common(1)[0][0] if pet_media else None,
                "first_seen": pet_moments[0]["date"] if pet_moments else None,
                "last_seen": pet_moments[-1]["date"] if pet_moments else None},
        "source": {"root": str(args.photos), "media_files": len(media),
                   "devices": dict(Counter(m["device"] for m in media if m["device"]))},
        "stats": {"media_with_pet": len(pet_media), "moments": len(moments),
                  "moments_with_pet": len(pet_moments),
                  "moments_with_people": sum(1 for m in pet_moments if m["with_people"]),
                  "undated_moments": len(undated),
                  "undated_media": sum(m["media_count"] for m in undated)},
        "eras": eras, "milestones": milestones, "moments": moments, "media": media,
    }
    args.out.write_text(json.dumps(doc, indent=1))

    s = doc["stats"]
    print(f"\n{len(media)} files -> {s['moments']} moments")
    print(f"Pet found in {len(pet_media)} files ({len(pet_media)/max(len(media),1):.0%}), "
          f"{s['moments_with_pet']} moments")
    print(f"Compression: {len(pet_media)/max(s['moments_with_pet'],1):.1f} files per moment")
    print(f"{len(eras)} eras, {len(milestones)} milestones")
    print(f"With people: {s['moments_with_people']} moments")
    print(f"Undated (no EXIF, no date in filename): {s['undated_media']} files "
          f"in {s['undated_moments']} moments — held out of the timeline")
    print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()
