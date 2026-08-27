#!/usr/bin/env python3
"""Reference / mood image set for *This Is Not An Exorcism* (Ivy Fang, Illumicrate).

PRIVATE reference only -- Chloe draws from these, they are not shown to the client.
The deliverable is a torn-blueprint case illustration; this set generates the
underlying imagery that populates and sets the tone for that collage: the house,
Taika's altar, the hauntings, and the collage-fodder objects.

Same pipeline primitives as build_set.py (client.py + workflows/batch_generate_api.json),
but a self-contained manifest so the Dino Weird West set is untouched.

    python tinae_refs.py                      # everything outstanding
    python tinae_refs.py --dry-run            # print prompts, generate nothing
    python tinae_refs.py --section altar      # one section only
    python tinae_refs.py --only altar_full the_seance
    python tinae_refs.py --force --only ...   # re-roll
    python tinae_refs.py --reroll             # one-shot reroll of rejects

Drafts land in <root>/refs/<slug>/. Pick winners by eye, then run filmgrain.py /
refine.py on the keepers as usual.

--reroll reads <root>/refs/verdicts.json, written during review:

    {
      "shed_spectre": {
        "verdict": "reject",
        "reason": "figure rendered opaque, not translucent",
        "prompt": "<optional full prompt override; omitted = same prompt, new seed>"
      }
    }

Every entry with verdict "reject" and no "rerolled" flag is regenerated ONCE.
Pass-1 drafts are moved to <slug>/_rejected_<stamp>/ first, then the entry is
stamped rerolled:true so it never auto-loops again. A still-bad pass 2 is a
manual --force problem, not the script's.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from client import ComfyClient, ComfyClientError, ComfyExecutionError
from workflow_utils import MODEL_PRESETS, find_node_by_title, load_workflow, random_seed, set_text

HERE = Path(__file__).resolve().parent
WIDTH = HEIGHT = 1024
BATCH = 6

# Two shared treatments, applied verbatim so the set reads as one body of work.
SCENE = (
    "cinematic film still, 35mm anamorphic, moody low-key naturalistic lighting, "
    "warm practical light sources against cold blue shadow, autumnal palette of ochre "
    "gold rust brown and desaturated teal-grey, shallow depth of field, soft "
    "photographic grain, quiet unsettling atmosphere, contemporary setting, "
    "photorealistic, muted colour grade"
)
OBJECT = (
    "still life photograph, close macro shot on a dark weathered wood surface, single "
    "warm raking light from one side, deep shadow, shallow depth of field, fine tactile "
    "detail, muted desaturated colour, photorealistic"
)
STYLE = {"scene": SCENE, "object": OBJECT}

# section, slug, kind, prompt (subject-specific part only; STYLE[kind] is appended)
MANIFEST = [
    # --- The house: Poppy Creek B&B -------------------------------------------
    ("house", "house_exterior_dusk", "scene",
     "a large old timber bed and breakfast house at dusk in autumn, dated peeling "
     "paint, wooden clapboard siding visibly bowed and warped in several places, "
     "overgrown thorny rose bushes crowding the porch with grey spiderwebs strung "
     "between them, handmade wooden windchimes hanging still from the porch eaves, "
     "crusted abandoned birds nests under the roof overhang, a ring of trees in deep "
     "red and orange autumn leaves around the property, no flowers in bloom, warm "
     "light glowing in one downstairs window and the rest of the house dark, low "
     "ground mist"),
    ("house", "house_porch_detail", "scene",
     "close view of a weathered wooden porch, several handmade wooden and shell "
     "windchimes hanging from the eaves, dead brown rose bushes below the rail thick "
     "with grey webs and garden spiders, paint peeling off the clapboard wall in long "
     "curls, a screen door slightly ajar, late afternoon raking side light, dust in "
     "the air"),
    ("house", "common_room_warm", "scene",
     "the interior common room of a large log cabin retreat, golden honey-toned wood "
     "panelling on every wall, a big rough stone hearth with a low fire, several worn "
     "brown leather armchairs around it, tall windows letting in warm evening sun, "
     "wide plank floorboards, cosy and lived-in, a faint sense of being watched from "
     "just out of frame"),
    ("house", "common_room_cold", "scene",
     "the same large log-panelled common room but cold and empty at night, no fire in "
     "the stone hearth, brown leather armchairs pushed at odd angles and one knocked "
     "over, long hard shadows, thin blue moonlight through tall windows, wide plank "
     "floorboards, still air, deeply unsettling, nobody present"),
    ("house", "kitchen_dining_warm", "scene",
     "a big rustic farmhouse kitchen with a long wooden dining table set for twelve "
     "guests, mismatched vases of hand-picked wildflowers on the windowsills, warm "
     "hanging lamplight, golden wood cabinets, plates and cutlery laid neatly, steam "
     "rising from serving dishes, one empty chair at the head of the table, faintly "
     "ominous"),
    ("house", "greenhouse_dusk", "scene",
     "a small old glass greenhouse in an overgrown autumn garden at dusk, panes "
     "fogged and streaked with condensation, dense dark overgrown plants pressing "
     "against the glass from inside, a single dim warm light glowing within, wet "
     "grass, bare trees, quiet menace"),

    # --- Taika's altar ------------------------------------------------------------
    ("altar", "altar_full", "scene",
     "a small three-tier wooden ancestor altar built against a bedroom wall beside a "
     "door, wide enough to sit on, two fat short red candles burning low, a framed "
     "black and white photograph propped at the centre, a golden pewter incense "
     "burner with handles carved as dragon heads, thin joss sticks smoking, strips of "
     "bright yellow paper printed with vertical black brush characters and red seal "
     "stamps, a small plate of glossy fruit, a jade pendant on red twine, a wooden "
     "fish-shaped percussion block with a small mallet, a string of dark wooden "
     "prayer beads, three small bronze deity statues, warm candlelight, deep shadow "
     "around it, reverent and quiet"),
    ("altar", "altar_hand", "scene",
     "a single pale bare human hand and forearm reaching out of deep darkness toward "
     "the lower tier of a candlelit wooden altar, fingers spread just short of "
     "touching a plate of fruit, two low red candles, incense smoke, the rest of the "
     "room black, tense and still, only one arm visible"),
    ("altar", "bronze_deities", "object",
     "three small aged bronze deity figurines standing in a row on dark wood, lit by "
     "a single warm candle flame, one a calm robed female figure holding a small "
     "vase, one a stern seated crowned judge holding a tablet, one a fierce youthful "
     "boy warrior holding a spear, patinated metal, shallow focus, deep black "
     "background"),
    ("altar", "beach_photo", "object",
     "an old slightly overexposed black and white snapshot in a plain wooden frame, "
     "showing a young man of about eighteen standing ankle-deep in breaking sea surf, "
     "wind blowing his hair across his face, holding up a sand-flecked seashell "
     "toward the camera, grinning, bright hazy sky, the print curling slightly at one "
     "corner, resting on dark wood"),
    ("altar", "plastic_fruit_incense", "object",
     "a cheap plate of glossy artificial plastic fruit, an apple an orange and a "
     "bunch of grapes, beside a smoking stick of real incense in a small brass "
     "holder, warm candlelight, dark background, shallow focus, the fake fruit "
     "slightly too shiny and uniform, quiet irony"),

    # --- Hauntings --------------------------------------------------------------
    ("haunting", "bathroom_blood_shower", "scene",
     "a small dated domestic bathroom, white wall tiles, a shower head running dark "
     "red blood instead of water, blood sheeting down the tiles and pooling in the "
     "bathtub, cold overhead light, faint steam, no people, horror"),
    ("haunting", "bathtub_drowning", "scene",
     "looking down into a full bathtub, the pale face and long dark hair of a "
     "drowning person suspended just under the surface of the water, hands drifting, "
     "the water distorting the image, cold blue bathroom light, quiet and terrible"),
    ("haunting", "ceiling_scuttler", "scene",
     "low angle looking straight up at the ceiling of a dim bedroom, the dark "
     "silhouette of a thin human figure pressed against the ceiling on all fours as "
     "if crawling across it, backlit by an open doorway, features lost in shadow, "
     "seen entirely in silhouette, deep contrast, wrongness"),
    ("haunting", "kitchen_bloody_footprints", "scene",
     "a trail of wet dark red bare human footprints crossing pale wooden kitchen "
     "floorboards, leading away from camera toward a dark doorway, low warm light, "
     "long shadows, nobody in frame, dread"),
    ("haunting", "bedroom_carcrash_vision", "scene",
     "a quiet ordinary bedroom at night with a made bed and floral wallpaper, but a "
     "violent car crash bleeds through the scene like a double exposure, harsh white "
     "headlight glare, shattered windscreen glass hanging in the air, twisted metal, "
     "the two images overlapping, disorienting, cold light"),
    ("haunting", "the_seance", "scene",
     "a long farmhouse dining table in candlelight, several seated people joining "
     "hands in a ring around a single lit candle at the centre, faces half lit and "
     "half in shadow, eyes closed, one empty chair with its own place setting, warm "
     "gloom, tense stillness, wide shot"),
    ("haunting", "shed_spectre", "scene",
     "the dark interior of a cluttered garden shed at night, hand tools and clay pots "
     "on the walls, a tall indistinct pale translucent human figure standing "
     "motionless among them, edges dissolving into the dark, a thin shaft of moonlight "
     "through the doorway, cold and silent"),
    ("haunting", "driveway_spectre_headlights", "scene",
     "a curved gravel driveway at night lined with autumn trees, a tall indistinct "
     "pale translucent human figure standing motionless in the middle of the drive, "
     "edges dissolving into the dark, caught in the white beam of car headlights, a "
     "long shadow thrown behind it, fog"),

    # --- Objects / collage fodder --------------------------------------------------
    ("objects", "talismans_yellow_paper", "object",
     "several strips of bright golden-yellow paper laid on dark wood, each brush "
     "painted with a vertical column of bold black Chinese characters, red square "
     "seal stamps, an eight-trigram bagua diagram and a yin-yang circle at the top of "
     "each strip, some strips crisp and new, some scorched brown and curling at the "
     "edges, one torn, single warm raking light, deep shadow"),
    ("objects", "torn_blueprint_annotated", "object",
     "a torn and folded architectural floor plan of a house drawn in faded blue line "
     "on off-white paper, coffee ring stains, covered in overlapping handwritten "
     "notes in pencil and in red and black ink, some notes neat and confident, some "
     "frantic and pressed hard enough to tear the paper, a dried bloody handprint "
     "smeared across one corner, pinholes and torn tape residue along the top edge, "
     "one corner ripped away, small crude sketches of frightening figures in the "
     "margins, flat overhead view, single soft light"),
    ("objects", "ghosthunting_kit", "object",
     "an array of amateur ghost-hunting equipment laid out on a scratched wooden "
     "table, a black thermal imaging camera, a full-spectrum night-vision camcorder, "
     "a handheld EMF meter with a needle dial, a small digital voice recorder, a "
     "bright yellow construction LED work lamp on a stand, coiled cables, low warm "
     "side light, deep shadow, documentary still life"),
    ("objects", "bones_dirt", "object",
     "a loose pile of assorted dry bones, both human and animal, mixed with dark "
     "crumbling soil and mud and a few dead dried flowers, on a black surface, single "
     "hard raking light, strong shadows, forensic, unsettling"),
]

SECTIONS = ["house", "altar", "haunting", "objects"]

# slug -> (section, slug, kind, prompt_body), for --reroll lookups.
BY_SLUG = {row[1]: row for row in MANIFEST}

VERDICTS = "refs/verdicts.json"


def build_prompt(kind: str, prompt: str) -> str:
    return f"{prompt}, {STYLE[kind]}"


def draft_dir(root: Path, slug: str) -> Path:
    return root / "refs" / slug


def is_done(root: Path, slug: str, batch: int) -> bool:
    d = draft_dir(root, slug)
    return d.is_dir() and len(list(d.glob("*.png"))) >= batch


def render(client, preset, slug: str, prompt: str, batch: int, out: Path):
    """Queue one batch for `slug` and download it. Returns (seed, saved_paths)."""
    out.mkdir(parents=True, exist_ok=True)
    seed = random_seed()
    wf = load_workflow(HERE / "workflows" / "batch_generate_api.json")
    set_text(wf, "positive_prompt", prompt)
    set_text(wf, "negative_prompt", "")
    wf[find_node_by_title(wf, "unet_loader")]["inputs"]["unet_name"] = preset["unet"]
    wf[find_node_by_title(wf, "empty_latent")]["inputs"].update(
        width=WIDTH, height=HEIGHT, batch_size=batch)
    wf[find_node_by_title(wf, "scheduler")]["inputs"].update(
        steps=preset["steps"], width=WIDTH, height=HEIGHT)
    wf[find_node_by_title(wf, "guider")]["inputs"]["cfg"] = preset["cfg"]
    wf[find_node_by_title(wf, "noise_seed")]["inputs"]["noise_seed"] = seed
    wf[find_node_by_title(wf, "save_batch")]["inputs"]["filename_prefix"] = slug
    history = client.run(wf)
    return seed, client.download_outputs(history, out, slug)


def do_reroll(root: Path, preset: dict, args) -> int:
    vpath = root / VERDICTS
    if not vpath.exists():
        print(f"ERROR: no verdicts file at {vpath}", file=sys.stderr)
        print('Write it during review: {"<slug>": {"verdict": "reject", "reason": '
              '"...", "prompt": "<optional override>"}}', file=sys.stderr)
        return 1
    verdicts = json.loads(vpath.read_text())
    todo = [s for s, v in verdicts.items()
            if isinstance(v, dict) and v.get("verdict") == "reject" and not v.get("rerolled")]
    if not todo:
        print("Nothing to reroll: no rejects, or every reject already rerolled once.")
        return 0
    unknown = [s for s in todo if s not in BY_SLUG]
    if unknown:
        print(f"ERROR: reject slug(s) not in manifest: {', '.join(unknown)}", file=sys.stderr)
        return 1

    client = ComfyClient(host=args.host, port=args.port)
    try:
        client.system_stats()
    except Exception as e:
        print(f"ERROR: could not reach ComfyUI: {e}", file=sys.stderr)
        return 1

    manifest_path = root / "refs" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Rerolling {len(todo)} rejected subject(s), once each: {', '.join(todo)}")

    for i, slug in enumerate(todo, 1):
        section, _, kind, body = BY_SLUG[slug]
        v = verdicts[slug]
        override = v.get("prompt")
        prompt = override or build_prompt(kind, body)
        out = draft_dir(root, slug)

        existing = sorted(out.glob(f"{slug}_*.png"))
        if existing:
            arch = out / f"_rejected_{stamp}"
            arch.mkdir(parents=True, exist_ok=True)
            for f in existing:
                shutil.move(str(f), str(arch / f.name))
            print(f"  [{i}/{len(todo)}] {slug}: archived {len(existing)} pass-1 drafts -> {arch.name}")

        tag = "revised prompt" if override else "reseed"
        print(f"  [{i}/{len(todo)}] {slug} x{args.batch} ({tag}) ... ", end="", flush=True)
        try:
            seed, saved = render(client, preset, slug, prompt, args.batch, out)
        except (ComfyExecutionError, ComfyClientError) as e:
            print(f"FAILED: {e}")
            continue
        print(f"{len(saved)} images (seed {seed})")

        v["rerolled"] = True
        v["reroll_stamp"] = stamp
        v["reroll_seed"] = seed
        if override:
            v["reroll_prompt"] = override
        vpath.write_text(json.dumps(verdicts, indent=2))

        manifest[slug] = dict(section=section, kind=kind, seed=seed, prompt=prompt,
                              files=[f.name for f in saved], rerolled=True)
        manifest_path.write_text(json.dumps(manifest, indent=2))

    print("\nReroll pass complete. Rebuild sheets:  python tinae_sheets.py --only "
          + " ".join(todo))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=r"D:\Creative\AI\outputs\this_is_not_an_exorcism")
    p.add_argument("--only", nargs="*", help="Limit to these slugs.")
    p.add_argument("--section", choices=SECTIONS, help="Limit to one section.")
    p.add_argument("--batch", type=int, default=BATCH)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="Regenerate even if drafts exist.")
    p.add_argument("--reroll", action="store_true",
                   help="One-shot reroll of every verdict=reject in refs/verdicts.json "
                        "not already rerolled. Ignores --only/--section.")
    p.add_argument("--model", choices=sorted(MODEL_PRESETS), default="distilled")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8188)
    args = p.parse_args()

    root = Path(args.root)
    if args.reroll:
        return do_reroll(root, MODEL_PRESETS[args.model], args)

    entries = MANIFEST
    if args.section:
        entries = [e for e in entries if e[0] == args.section]
    if args.only:
        wanted = set(args.only)
        entries = [e for e in entries if e[1] in wanted]
        missing = wanted - {e[1] for e in entries}
        if missing:
            print(f"ERROR: unknown slug(s): {', '.join(sorted(missing))}", file=sys.stderr)
            return 1

    if args.dry_run:
        for section, slug, kind, prompt in entries:
            print(f"--- [{section}] {slug} ({kind})\n{build_prompt(kind, prompt)}\n")
        return 0

    preset = MODEL_PRESETS[args.model]
    client = ComfyClient(host=args.host, port=args.port)
    try:
        client.system_stats()
    except Exception as e:
        print(f"ERROR: could not reach ComfyUI: {e}", file=sys.stderr)
        print("Is `python main.py` running in the ComfyUI venv?", file=sys.stderr)
        return 1

    manifest_path = root / "refs" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    todo = [e for e in entries if args.force or not is_done(root, e[1], args.batch)]
    print(f"{len(todo)} of {len(entries)} subjects to generate "
          f"({len(entries) - len(todo)} already have drafts)")

    failures = []
    started = time.time()
    for i, (section, slug, kind, prompt_body) in enumerate(todo, 1):
        out = draft_dir(root, slug)
        prompt = build_prompt(kind, prompt_body)

        elapsed = time.time() - started
        print(f"[{i}/{len(todo)}] {section}/{slug} x{args.batch} ... ", end="", flush=True)
        try:
            seed, saved = render(client, preset, slug, prompt, args.batch, out)
        except (ComfyExecutionError, ComfyClientError) as e:
            print(f"FAILED: {e}")
            failures.append((slug, str(e)))
            continue
        print(f"{len(saved)} images (seed {seed})  [{elapsed/60:.1f} min elapsed]")

        manifest[slug] = dict(section=section, kind=kind, seed=seed, prompt=prompt,
                              files=[f.name for f in saved])
        manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nDone in {(time.time()-started)/60:.1f} min. Manifest: {manifest_path}")
    if failures:
        print(f"\n{len(failures)} FAILED -- rerun to retry:", file=sys.stderr)
        for slug, err in failures:
            print(f"  {slug}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
