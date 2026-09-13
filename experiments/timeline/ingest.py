"""
Build the moment graph from a raw photo dump.

The load-bearing idea (see docs/data-model.md): a file is not a moment.
People burst-shoot — ten frames in forty seconds is one event, not ten.
So ingest runs: media -> detection -> burst clustering -> moments -> eras.

Usage:
    uv run ingest.py --roll Matt="/path/a" --roll Renee="/path/b" --pet Izzy
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

from cache import Cache, Digests, param_key

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


def detect(model: YOLO, path: Path, conf: float) -> dict:
    """The only expensive step, and a pure function of (bytes, model, conf) —
    so it is the only thing worth caching. Everything else on a rec is cheap
    and varies with where the file was found."""
    r = model(str(path), conf=conf, verbose=False)[0]
    names = [r.names[int(c)] for c in r.boxes.cls]
    scores = r.boxes.conf.tolist()
    boxes = r.boxes.xyxyn.tolist()
    out = {"pet": False, "score": 0.0, "box": None,
           "people": sum(1 for n in names if n == "person")}
    best = -1
    for j, n in enumerate(names):
        if n in PET_CLASSES and scores[j] > out["score"]:
            out["pet"], out["score"], best = True, round(scores[j], 3), j
            out["species"] = n
    if best >= 0:
        out["box"] = [round(v, 4) for v in boxes[best]]
    return out


def scan(root: Path, who: str, model: YOLO, name: str, conf: float, seen: dict,
         digests: Digests, cache: Cache, firsts: Cache, now: str,
         reuse: bool, about: str | None = None) -> list[dict]:
    """Read one folder. `about` marks it a subject folder — every file in it is
    a person's statement that this pet is in it, which is an assignment, not a
    guess (D21). Most folders people hand over are this: an exported album."""
    paths = sorted(p for p in root.rglob("*") if p.suffix.lower() in MEDIA_EXTS | VIDEO_EXTS)
    media = []
    for i, path in enumerate(paths, 1):
        # The same photo often lives in two rolls after being texted between
        # them. Pixel filenames carry a millisecond timestamp, so a repeat
        # name is the same capture. First roll to claim it keeps it.
        if path.name in seen:
            if about:
                seen[path.name].setdefault("assign", []).append(about)
            else:
                seen[path.name].setdefault("also_in", []).append(who)
            continue
        digest = digests.of(path)
        # First sight is a property of the content, so it survives re-runs,
        # renames and re-imports. Resurfacing keys off taken_at; "what changed"
        # keys off this. They are never interchangeable.
        first_seen = firsts.get_json(digest)
        if first_seen is None:
            first_seen = now
            firsts.put_json(digest, first_seen)
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
            "id": digest,
            "path": str(path),
            "contributor": who,
            "ingested_at": first_seen,
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
        if about:
            rec["assign"] = [about]

        if not is_video:
            key = param_key(digest, name, conf)
            det = cache.get_json(key) if reuse else None
            if det is None:
                try:
                    det = detect(model, path, conf)
                    cache.put_json(key, det)
                except Exception as e:
                    rec["error"], det = str(e)[:80], {}
            rec.update(det)
        seen[path.name] = rec
        media.append(rec)
    return media


def moment_id(group: list[dict]) -> str:
    """Identity from membership, so a re-ingest cannot silently repoint it.

    Positional ids renumbered 100% of moments when 708 earlier photos arrived,
    and every stale pointer resolved to a different, plausible photo (D13).
    Hashing the member set means a moment that gains or loses a frame gets a
    new id and a stale pointer MISSES — loud, not silent.
    """
    return "mo" + hashlib.sha256(
        "".join(sorted(g["id"] for g in group)).encode()).hexdigest()[:14]


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
            "id": moment_id(group),
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
            "hero_path": hero["path"],
            "hero_box": hero["box"],
            "hero_by": hero["contributor"],
            "contributors": sorted({g["contributor"] for g in group}),
            "co_attended": len({g["contributor"] for g in group}) > 1,
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


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "pet"


def load_profile(path: Path, pet_name: str, species: str | None, anchor: str | None,
                 rolls: list[str], abouts: list[str]) -> dict:
    """People, pets and who may see what. The user owns everything in here;
    nothing derived ever overwrites it."""
    p = json.loads(path.read_text()) if path.exists() else {}
    if "pets" not in p:  # migrate the flat {anchor, species} shape
        p = {"pets": [{"id": slug(pet_name), "name": pet_name,
                       **({"species": p["species"]} if p.get("species") else {}),
                       **({"anchor": p["anchor"]} if p.get("anchor") else {})}],
             "people": [], "access": []}
    p.setdefault("people", [])
    p.setdefault("access", [])

    by_id = {x["id"]: x for x in p["pets"]}
    primary = p["pets"][0] if p["pets"] else None
    if primary and pet_name != "Pet":
        primary["name"] = pet_name
    if primary and species:
        primary["species"] = species
    if primary and anchor:
        primary["anchor"] = anchor

    # A pet named by --about that nobody has declared is created with a name
    # and nothing else. Requiring a date or species here is exactly the
    # friction D21 forbids.
    for name in abouts:
        if slug(name) not in by_id:
            pet = {"id": slug(name), "name": name}
            p["pets"].append(pet)
            by_id[pet["id"]] = pet

    known = {x["id"] for x in p["people"]}
    for who in rolls:
        if slug(who) not in known:
            p["people"].append({"id": slug(who), "name": who})
            known.add(slug(who))
    # Someone who hands over their camera roll owns the pet the roll is about.
    # That is the only access edge ever created automatically.
    if primary:
        have = {(a["person"], a["pet"]) for a in p["access"]}
        for who in rolls:
            if (slug(who), primary["id"]) not in have:
                p["access"].append({"person": slug(who), "pet": primary["id"],
                                    "role": "owner"})
    path.write_text(json.dumps(p, indent=1))
    return p


def owned_by(profile: dict) -> dict[str, list[str]]:
    return {x["id"]: [a["pet"] for a in profile["access"]
                      if a["person"] == x["id"] and a["role"] == "owner"]
            for x in profile["people"]}


def caretaking(profile: dict, person: str, when: str) -> list[str]:
    out = []
    for a in profile["access"]:
        if a["person"] != person or a["role"] != "caretaker":
            continue
        if a.get("from") and when < a["from"]:
            continue
        if a.get("to") and when > a["to"]:
            continue
        out.append(a["pet"])
    return out


def assign_appearances(moments: list[dict], media: list[dict], profile: dict) -> None:
    """Decide which pets are in each moment, guessing as rarely as possible.

    Order: user > album > caretaker > inferred. An album is a strong hint, not
    proof — a hand-tagged sample of one found it 32% wrong, because people
    build a pet's album out of the occasions that pet was around and both
    animals are in frame (D23). So an album file also picks up its
    contributor's own pet, and a moment resting on an album alone is flagged
    for review rather than trusted (D24).

    A contributor who owns two pets gets no inference at all: ambiguity
    resolves to unassigned, which is visible and fixable, where a wrong
    assignment is silent (D21).
    """
    by_file = {x["file"]: x for x in media}
    owns = owned_by(profile)
    manual = profile.get("assignments", {})
    known = {x["id"] for x in profile["pets"]}

    for m in moments:
        found: dict[str, str] = {}
        if m["id"] in manual:
            for pet in manual[m["id"]]:
                found[pet] = "user"
        else:
            for fname in m["files"]:
                row = by_file.get(fname, {})
                if not row.get("pet"):
                    continue
                for name in row.get("assign", []):
                    found.setdefault(slug(name), "album")
                care = caretaking(profile, slug(row["contributor"]), m["date"])
                if len(care) == 1:
                    found.setdefault(care[0], "caretaker")
                    continue
                mine = owns.get(slug(row["contributor"]), [])
                if len(mine) == 1:
                    found.setdefault(mine[0], "inferred")
        m["appearances"] = [{"pet": k, "assigned_by": v}
                            for k, v in sorted(found.items()) if k in known]
        m["unassigned"] = m["has_pet"] and not m["appearances"]
        # Nothing but an album vouches for this one, and an album is 32%
        # wrong. Not an error — a question for the person who was there.
        m["needs_review"] = bool(m["appearances"]) and all(
            a["assigned_by"] == "album" for a in m["appearances"])


def find_anchor(pet: list[dict], min_run: int = 5, window: int = 30) -> datetime:
    """The earliest date where photography actually *starts*, not the earliest
    photo. A single misdetected animal years earlier is enough to wreck a
    plain minimum — two stray dogs in a contributor's roll moved this archive's
    anchor back 2.5 years and invented two empty chapters. Requiring a run of
    activity makes the anchor robust to outliers without dropping anything.
    """
    for i, m in enumerate(pet):
        t0 = datetime.fromisoformat(m["started_at"])
        n = sum(1 for x in pet[i:i + min_run * 8]
                if datetime.fromisoformat(x["started_at"]) - t0 <= timedelta(days=window))
        if n >= min_run:
            return t0
    return datetime.fromisoformat(pet[0]["started_at"])


def build_eras(moments: list[dict], start: datetime) -> list[dict]:
    """Chapters are life years anchored on the first photo, not calendar years.

    Gap-based segmentation was tried first and produced a single era: a
    well-photographed pet has no long silences. Life years match how people
    actually narrate a pet ("the first year") and need no tuning.
    """
    pet = [m for m in moments if m["has_pet"] and m["dated"] and not m["before_anchor"]]
    if not pet:
        return []
    eras = []
    # A user-given anchor is the day the pet came home, which can be later than
    # the first photo — meeting them at the shelter, foster or breeder photos.
    # Those predate every chapter and would otherwise fall out of the timeline
    # entirely, so they get a prologue. A derived anchor never produces one,
    # since it is the first photo by construction.
    before = [m for m in pet if datetime.fromisoformat(m["started_at"]) < start]
    if before:
        eras.append({
            "id": "e_pre", "index": None, "label": "Before she came home",
            "eyebrow": "Prologue",
            "start": before[0]["date"], "end": before[-1]["date"],
            "moments": len(before),
            "media": sum(m["media_count"] for m in before),
            "with_people": sum(1 for m in before if m["with_people"]),
            "hero": max(before, key=lambda m: m["hero_quality"])["hero"],
        })
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
            "eyebrow": f"Chapter {yr + 1}",
            "start": chunk[0]["date"],
            "end": chunk[-1]["date"],
            "moments": len(chunk),
            "media": sum(m["media_count"] for m in chunk),
            "with_people": sum(1 for m in chunk if m["with_people"]),
            "hero": max(chunk, key=lambda m: m["hero_quality"])["hero"],
        })
    return eras


def superlative(values: list[float]) -> dict:
    """A maximum plus the runner-up it beat.

    Every superlative here is an extremum, and extrema are decided by their
    top two values. When those are close the winner is a coin flip that the
    next import can flip back, so it is marked provisional rather than shown
    as a standing record (D15).
    """
    top = max(values)
    rest = [v for v in values if v != top] or [0]
    second = max(rest)
    margin = (top - second) / top if top else 0
    return {"value": top, "runner_up": second, "margin": round(margin, 3),
            "provisional": margin < 0.15}


def build_milestones(moments: list[dict], media: list[dict]) -> list[dict]:
    """Facts worth telling a person, derived rather than entered."""
    pet = [m for m in moments if m["has_pet"] and m["dated"] and not m["before_anchor"]]
    if not pet:
        return []
    out = [
        {"kind": "first", "date": pet[0]["date"], "label": "First photo", "moment": pet[0]["id"]},
        {"kind": "latest", "date": pet[-1]["date"], "label": "Most recent photo", "moment": pet[-1]["id"]},
    ]
    busiest = max(pet, key=lambda m: m["media_count"])
    out.append({"kind": "busiest_moment", "date": busiest["date"],
                "label": f"Longest single burst — {busiest['media_count']} frames",
                "moment": busiest["id"],
                **superlative([m["media_count"] for m in pet])})

    by_day = Counter(m["date"] for m in pet)
    day, n = by_day.most_common(1)[0]
    out.append({"kind": "busiest_day", "date": day,
                "label": f"Most photographed day — {n} moments",
                **superlative(list(by_day.values()))})

    gaps = [(datetime.fromisoformat(b["started_at"]) - datetime.fromisoformat(a["ended_at"]), a, b)
            for a, b in zip(pet, pet[1:])]
    if gaps:
        g, a, b = max(gaps, key=lambda x: x[0])
        # A gap can *shrink* when photos land inside it, so unlike the other
        # superlatives this one can be falsified by an import, not just beaten.
        out.append({"kind": "longest_gap", "date": b["date"],
                    "label": f"Longest quiet stretch — {g.days} days", "moment": b["id"],
                    "shrinkable": True,
                    **superlative([x[0].days for x in gaps])})

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


def build_digest(doc: dict, prev: dict | None, now: str) -> dict:
    """What this run changed. An import is an event, not a silent recompute.

    Backfill routinely rewrites the past — adding two albums re-clustered 26
    bursts and moved 25 moments between pets, none of which was visible
    anywhere. Diffing on content ids rather than positions is what makes the
    comparison meaningful (D13).
    """
    new = [x for x in doc["media"] if x["ingested_at"] == now]
    d = {"at": now, "new_media": len(new),
         "new_by_contributor": dict(Counter(x["contributor"] for x in new)),
         "covering": [min((x["taken_at"][:10] for x in new), default=None),
                      max((x["taken_at"][:10] for x in new), default=None)]}
    if not prev:
        d["first_run"] = True
        return d

    old_m = {m["id"] for m in prev["moments"]}
    now_m = {m["id"] for m in doc["moments"]}
    d["moments"] = {"before": len(old_m), "after": len(now_m),
                    "unchanged": len(old_m & now_m),
                    "reclustered": len(old_m - now_m), "new": len(now_m - old_m)}

    oldp = {p["id"]: p for p in prev.get("pets", [])}
    d["pets"] = {}
    for p in doc["pets"]:
        o = oldp.get(p["id"])
        if not o:
            d["pets"][p["id"]] = {"added": True, "moments": p["moments"]}
            continue
        change = {}
        if o["moments"] != p["moments"]:
            change["moments"] = [o["moments"], p["moments"]]
        if o.get("anchor_derived") != p.get("anchor_derived"):
            change["anchor_derived"] = [o.get("anchor_derived"), p.get("anchor_derived")]
        oldb = {(e["start"], e["end"]) for e in o.get("eras", [])}
        newb = {(e["start"], e["end"]) for e in p.get("eras", [])}
        if oldb != newb:
            change["eras"] = [len(oldb), len(newb)]
        oldms = {(m["kind"], m["date"], m["label"]) for m in o.get("milestones", [])}
        newms = {(m["kind"], m["date"], m["label"]) for m in p.get("milestones", [])}
        if oldms != newms:
            change["milestones_changed"] = [list(x) for x in sorted(newms - oldms)]
        if change:
            d["pets"][p["id"]] = change

    def days(doc_):
        return {m["date"] for m in doc_["moments"] if m["has_pet"] and m["dated"]}
    d["days"] = {"before": len(days(prev)), "after": len(days(doc))}
    return d


def build_merge_report(moments: list[dict], media: list[dict], rolls: list[str]) -> dict:
    """How much does each roll actually add? The D6 question, quantified."""
    pet = [m for m in moments if m["has_pet"] and m["dated"] and not m["before_anchor"]]
    days = {}
    for m in pet:
        days.setdefault(m["date"], set()).update(m["contributors"])
    report = {"co_attended_moments": sum(1 for m in pet if m["co_attended"]),
              "days_total": len(days),
              "days_shared": sum(1 for v in days.values() if len(v) > 1),
              "per_roll": {}}
    for who in rolls:
        solo_days = [d for d, v in days.items() if v == {who}]
        report["per_roll"][who] = {
            "media": sum(1 for x in media if x["contributor"] == who and x["pet"]),
            "moments": sum(1 for m in pet if who in m["contributors"]),
            "days_only_theirs": len(solo_days),
            "earliest": min((m["date"] for m in pet if who in m["contributors"]), default=None),
        }
    dupes = [x for x in media if x.get("also_in")]
    report["shared_copies"] = len(dupes)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roll", action="append", default=[],
                    metavar="NAME=PATH", help="a contributor's photo folder; repeatable")
    ap.add_argument("--about", action="append", default=[], metavar="PET=PATH",
                    help="a folder that is about one pet — an exported album. "
                         "Every file in it is assigned to that pet; repeatable")
    ap.add_argument("--pet", default="Pet")
    ap.add_argument("--out", type=Path, default=Path("moments.json"))
    ap.add_argument("--conf", type=float, default=0.30)
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--rebuild", type=Path, metavar="MOMENTS.JSON",
                    help="reuse detections from a previous run; skip the model entirely")
    ap.add_argument("--cache", type=Path, default=Path(__file__).resolve().parent / ".cache")
    ap.add_argument("--no-cache", action="store_true",
                    help="re-run detection even when cached; still writes results")
    ap.add_argument("--species", help="the pet's species; the detector is not "
                                      "trusted to decide this")
    ap.add_argument("--anchor", metavar="YYYY-MM-DD",
                    help="the real adoption or birth date; outranks the derived "
                         "anchor, persists to pet.json, and is never moved by a backfill")
    args = ap.parse_args()

    def pairs(specs, flag):
        out = []
        for spec in specs:
            who, _, path = spec.partition("=")
            if not path:
                raise SystemExit(f"{flag} needs NAME=PATH, got {spec!r}")
            out.append((who, Path(path)))
        return out

    if args.rebuild:
        prev = json.loads(args.rebuild.read_text())
        media = prev["media"]
        rolls = [(w, Path(r)) for w, r in prev["source"]["rolls"].items()]
        abouts = [(w, Path(r)) for w, r in prev["source"].get("about", {}).items()]
        print(f"Rebuilding from {args.rebuild}: {len(media)} media rows, no detection")
    else:
        media, rolls, abouts = None, [], []

    rolls += pairs(args.roll, "--roll")
    abouts += pairs(args.about, "--about")
    if not rolls:
        raise SystemExit("pass at least one --roll NAME=PATH, or --rebuild")

    cache, now, media_scanned = None, "", False
    if media is None:
        digests, cache = Digests(args.cache), Cache(args.cache, "detect")
        firsts, now = Cache(args.cache, "firstseen"), datetime.now().isoformat(timespec="seconds")
        media_scanned = True
        model, seen, media = YOLO(args.model), {}, []
        for who, root in rolls:
            print(f"Scanning {who}: {root}")
            media += scan(root, who, model, args.model, args.conf, seen,
                          digests, cache, firsts, now, not args.no_cache)
        # Subject folders come second so they can attach to rows the rolls
        # already claimed rather than duplicating them.
        for pet, root in abouts:
            print(f"Scanning album about {pet}: {root}")
            media += scan(root, "unknown", model, args.model, args.conf, seen,
                          digests, cache, firsts, now, not args.no_cache, about=pet)
        digests.save()
    moments = build_moments(media)
    conf = Path(__file__).resolve().parent / "pet.json"
    profile = load_profile(conf, args.pet, args.species, args.anchor,
                           [w for w, _ in rolls], [w for w, _ in abouts])
    assign_appearances(moments, media, profile)

    owns = owned_by(profile)
    contributes = {slug(w) for w, _ in rolls}
    # A pet only gets a life story if someone who handed over photos owns it.
    # A friend's dog has no anchor we could confirm and usually no sustained
    # period either — Ray is fragments across eleven years (D21).
    storied = {p for who in contributes for p in owns.get(who, [])}

    pets = []
    for pet in profile["pets"]:
        mine = [m for m in moments
                if any(a["pet"] == pet["id"] for a in m["appearances"])]
        dated = [m for m in mine if m["dated"]]
        block = dict(pet)
        if pet["id"] in storied and dated:
            # A given anchor is a fact the user owns, remembered rather than
            # re-asked; no import moves it. The derived one stays as the
            # fallback and as the reference for spotting strays.
            derived = find_anchor(dated)
            anchor = datetime.fromisoformat(pet["anchor"]) if pet.get("anchor") else derived
            for m in mine:
                m["before_anchor"] = bool(
                    datetime.fromisoformat(m["started_at"]) < derived)
            keep = [m for m in dated if not m["before_anchor"]]
            block.update(sparse=False,
                         eras=build_eras(mine, anchor),
                         milestones=build_milestones(mine, media),
                         anchor=anchor.date().isoformat(),
                         anchor_source="given" if pet.get("anchor") else "derived",
                         anchor_derived=derived.date().isoformat(),
                         before_anchor_moments=len(dated) - len(keep))
        else:
            keep = dated
            block.update(sparse=True, eras=[], milestones=[],
                         before_anchor_moments=0)
        block.update(moments=len(keep), media=sum(m["media_count"] for m in keep),
                     with_people=sum(1 for m in keep if m["with_people"]),
                     first_seen=keep[0]["date"] if keep else None,
                     last_seen=keep[-1]["date"] if keep else None,
                     contributors=sorted({c for m in keep for c in m["contributors"]}))
        pets.append(block)

    for m in moments:
        m.setdefault("before_anchor", False)

    pet_media = [m for m in media if m["pet"]]
    undated = [m for m in moments if not m["dated"]]
    strays = [m for m in moments if m["has_pet"] and m["dated"] and m["before_anchor"]]
    unassigned = [m for m in moments if m["unassigned"]]
    doc = {
        "pets": pets,
        "source": {"rolls": {who: str(root) for who, root in rolls},
                   "about": {who: str(root) for who, root in abouts},
                   "media_files": len(media),
                   "devices": dict(Counter(m["device"] for m in media if m["device"]))},
        "merge": build_merge_report(moments, media, [who for who, _ in rolls]),
        "stats": {"media_with_pet": len(pet_media), "moments": len(moments),
                  "moments_with_people": sum(1 for m in moments
                                             if m["has_pet"] and m["with_people"]),
                  "undated_moments": len(undated),
                  "undated_media": sum(m["media_count"] for m in undated),
                  "before_anchor_moments": len(strays),
                  "before_anchor_media": sum(m["media_count"] for m in strays),
                  "unassigned_moments": len(unassigned),
                  "unassigned_media": sum(m["media_count"] for m in unassigned),
                  "needs_review_moments": sum(1 for m in moments if m["needs_review"]),
                  "assigned_by": dict(Counter(
                      a["assigned_by"] for m in moments for a in m["appearances"]))},
        "moments": moments, "media": media,
    }
    before = None
    if args.out.exists():
        try:
            before = json.loads(args.out.read_text())
        except Exception:
            pass
    doc["digest"] = build_digest(doc, before, now if media_scanned else "")
    args.out.write_text(json.dumps(doc, indent=1))
    args.out.with_name("digest.json").write_text(json.dumps(doc["digest"], indent=1))

    s = doc["stats"]
    print(f"\n{len(media)} files -> {s['moments']} moments")
    print(f"An animal in {len(pet_media)} files ({len(pet_media)/max(len(media),1):.0%})")
    print(f"Undated (no EXIF, no date in filename): {s['undated_media']} files "
          f"in {s['undated_moments']} moments — held out of the timeline")

    print(f"\nPETS")
    for p in pets:
        tag = "sparse, no timeline" if p["sparse"] else (
            f"{len(p['eras'])} eras, {len(p['milestones'])} milestones, "
            f"anchor {p['anchor']} ({p['anchor_source']})")
        print(f"  {p['name']:10s} {p['moments']:5d} moments, {p['media']:5d} files  — {tag}")
        if p["before_anchor_moments"]:
            print(f"             {p['before_anchor_moments']} before the anchor, held out")
    both = [m for m in moments if len(m["appearances"]) > 1]
    print(f"  moments with more than one pet: {len(both)}")
    print(f"  assignment source: {s['assigned_by']}")
    if s["needs_review_moments"]:
        print(f"  NEEDS REVIEW: {s['needs_review_moments']} moments rest on an album "
              f"alone — an album is ~32% wrong (D23)")
    if s["unassigned_moments"]:
        print(f"  UNASSIGNED: {s['unassigned_moments']} moments "
              f"({s['unassigned_media']} files) — nobody said which pet")

    if strays:
        print(f"\nBefore an anchor: {s['before_anchor_media']} files "
              f"in {len(strays)} moment(s) — held out, likely another animal")
        for m in strays[:5]:
            print(f"    {m['date']}  {m['hero']}  ({', '.join(m['contributors'])})")

    dg = doc["digest"]
    if dg.get("new_media") or dg.get("moments"):
        print(f"\nTHIS IMPORT")
        if dg["new_media"]:
            by = ", ".join(f"{k} {v}" for k, v in dg["new_by_contributor"].items())
            print(f"  {dg['new_media']} new files ({by}) covering "
                  f"{dg['covering'][0]} to {dg['covering'][1]}")
        mo = dg.get("moments")
        if mo:
            print(f"  moments {mo['before']} -> {mo['after']}: {mo['unchanged']} unchanged, "
                  f"{mo['reclustered']} re-clustered, {mo['new']} new")
        for pid, ch in dg.get("pets", {}).items():
            if ch.get("added"):
                print(f"  {pid}: added, {ch['moments']} moments")
                continue
            bits = []
            if "moments" in ch:
                bits.append(f"moments {ch['moments'][0]} -> {ch['moments'][1]}")
            if "anchor_derived" in ch:
                bits.append(f"derived anchor {ch['anchor_derived'][0]} -> {ch['anchor_derived'][1]}")
            if "eras" in ch:
                bits.append(f"eras {ch['eras'][0]} -> {ch['eras'][1]}")
            if ch.get("milestones_changed"):
                bits.append(f"{len(ch['milestones_changed'])} milestone(s) changed")
            print(f"  {pid}: {', '.join(bits)}")
        if "days" in dg and dg["days"]["before"] != dg["days"]["after"]:
            print(f"  days with photos {dg['days']['before']} -> {dg['days']['after']}")

    mg = doc["merge"]
    print(f"\nMERGE — {len(rolls)} roll(s), {mg['shared_copies']} shared copies skipped")
    for who, r in mg["per_roll"].items():
        print(f"  {who:10s} {r['media']:5d} pet photos, {r['moments']:4d} moments, "
              f"{r['days_only_theirs']:3d} days only they have, from {r['earliest']}")
    print(f"  co-attended moments: {mg['co_attended_moments']}  "
          f"days both were shooting: {mg['days_shared']}/{mg['days_total']}")
    if cache:
        print(f"\ndetection cache: {cache.rate}")
    print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()
