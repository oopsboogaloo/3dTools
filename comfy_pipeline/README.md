# ComfyUI + FLUX Local Image Pipeline

A scriptable local batch-generate → pick → refine workflow for ComfyUI, built for
running against your own GPU instead of a hosted service. Two commands:

```
python generate.py --prompt "..." --negative "..." --batch 4   # -> ./drafts/*.png
python refine.py --image ./drafts/pick.png --prompt "..."      # -> ./final/*.png
```

## What's actually verified here vs. what you still need to run

This pipeline was built in a sandboxed cloud container with **no GPU, no ComfyUI
install, and no downloaded model weights** — it cannot run image generation or
talk to `nvidia-smi`. What's in this directory is the code scaffold from the
build spec: the client, the two CLI scripts, and hand-authored API-format
workflow JSON matching ComfyUI's standard published FLUX graph. It has **not**
been run end-to-end against a live ComfyUI server.

Before you rely on this, you need to do on your own machine, in order:

1. Steps 1–2 below (install ComfyUI, confirm the 4090 is detected, get a model).
2. **The manual single-image test the spec calls out** — generate one image via
   the ComfyUI web UI. This proves the install and model paths are sound before
   any script touches them.
3. Re-export the workflow via ComfyUI's "Save (API Format)" button (Settings →
   Dev Mode) and diff it against `workflows/batch_generate_api.json`. Node
   class names (`UNETLoader`, `DualCLIPLoader`, `FluxGuidance`, etc.) and default
   values can differ depending on your ComfyUI version and which model variant
   you loaded — the JSON here is a best-effort starting point, not a captured
   export from a real run. Keep the `_meta.title` values (`positive_prompt`,
   `negative_prompt`, `empty_latent`, `batch_sampler`, `flux_guidance`,
   `save_batch` / and the refine equivalents) since the scripts look nodes up by
   title, not by id.
4. Step 6 below (`generate.py` then `refine.py` against a real prompt, watching
   `nvidia-smi`).

## Step 1 — Install ComfyUI

Confirm your OS first (`ver` on Windows, `uname -a` on Linux/macOS) and check
CUDA is current — you said this machine already runs llama.cpp/Qwen3 and
Blender-via-MCP, so drivers are likely fine, but confirm with `nvidia-smi`
before assuming.

**Windows (PowerShell):**
```powershell
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# ComfyUI's requirements.txt pulls a CUDA build of torch on most setups; if
# `python main.py` logs a CPU-only device, reinstall torch explicitly per
# https://pytorch.org/get-started/locally/ for your CUDA version first.
python main.py
```

**Linux:**
```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Confirm:
- The startup log shows your RTX 4090 and its VRAM.
- `curl http://127.0.0.1:8188/system_stats` returns JSON (not connection refused).

## Step 2 — Get a model

**Licensing — check this before generating anything for paid work:**

| Model | License | Commercial use (Illumicrate, Baldman Games, Mighty Merch, paid commissions) |
|---|---|---|
| FLUX.2 [dev] | Non-commercial | **Not allowed.** Fine for personal Selovast/Deadlands worldbuilding, not for anything sold. |
| FLUX.2 [klein] (distilled, ~19.6GB) | Check the specific license on release — historically FLUX's distilled/schnell tier has been more permissive than `[dev]`, but verify before assuming it's commercial-safe. | Verify per release. |
| Qwen-Image 2.0 | Apache 2.0 | **Allowed.** Prefer this for anything that might end up in a paid commission, and for map labels/signage where you need legible in-image text. |

Download whichever you choose into ComfyUI's model folders. FLUX splits its
weights (unlike SDXL's single checkpoint file), so the layout is:

```
ComfyUI/models/unet/           flux2-dev-fp8.safetensors   (or the klein GGUF/quantized variant)
ComfyUI/models/clip/           clip_l.safetensors, t5xxl_fp8_e4m3fn.safetensors
ComfyUI/models/vae/            ae.safetensors
```

Exact filenames vary by where you download from — update `unet_name`,
`clip_name1`/`clip_name2`, and `vae_name` in the workflow JSON (or pass them as
new CLI flags if you extend the scripts) to match whatever you actually
downloaded. **Do the manual single-image generation in the ComfyUI web UI
before running any script** — this is the spec's explicit checkpoint and it's
the fastest way to catch a wrong model path.

## Step 3 & 4 — The two workflows

`workflows/batch_generate_api.json` — CheckpointLoader-equivalent (`UNETLoader`
+ `DualCLIPLoader` + `VAELoader`) → positive/negative `CLIPTextEncode` →
`FluxGuidance` → `EmptyLatentImage` (batch_size=4) → `KSampler` → `VAEDecode` →
`SaveImage`.

`workflows/refine_upscale_api.json` — `LoadImage` → `VAEEncode` →
`LatentUpscaleBy` → second `KSampler` at low denoise → `VAEDecode` →
`SaveImage`.

Every node the scripts touch has a stable `_meta.title` so they're addressable
by name rather than by fragile numeric id — this is exactly the "give text
encode nodes unique titles" advice from the spec, extended to every node the
scripts patch.

If you build these graphs by hand in the ComfyUI UI instead of trusting the
checked-in JSON, use the same titles so the scripts don't need any changes.

## Step 5 — Setup

```bash
cd comfy_pipeline
python -m venv venv          # a separate venv from ComfyUI's own — this only needs `websocket-client`
source venv/bin/activate      # or venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

`generate.py` and `refine.py` talk to ComfyUI's HTTP + websocket API directly
(`/prompt`, `/history`, `/view`, `/upload/image`, `/ws`) rather than through the
`comfy_api_simplified` wrapper, so there's one fewer dependency to debug and the
websocket handling (see below) is fully visible in `client.py`.

### generate.py

```bash
python generate.py \
  --prompt "a weathered Deadlands bounty hunter, dusty coat, cinematic lighting, matte painting" \
  --negative "blurry, extra fingers, watermark, text" \
  --batch 4
```

Submits the batch workflow, waits for all 4 to finish, downloads them to
`./drafts/` as `{timestamp}_{prompt-slug}_seed{seed}_{index}.png`, and prints
the file paths. Send those thumbnails to Claude in chat to review/pick, per the
spec's v1 scope (no picker UI yet).

### refine.py

```bash
python refine.py \
  --image ./drafts/20260818_143012_weathered_deadlands_bounty_hunter_seed123_2.png \
  --prompt "a weathered Deadlands bounty hunter, dusty coat, cinematic lighting, matte painting" \
  --denoise 0.4
```

Uploads the chosen draft to ComfyUI, runs it through the low-denoise
upscale pass, and saves the result to `./final/` with the same
timestamp+prompt+seed naming convention.

Both scripts accept `--host`/`--port` if ComfyUI runs on another machine on
your LAN, and `--seed` to reproduce a specific result.

## Step 6 — Verify end to end (do this on your machine, not skippable)

1. `python main.py` in the ComfyUI venv, leave it running.
2. In a second terminal: run `generate.py` with a real Deadlands or Selovast
   prompt. Confirm 4 distinct images land in `./drafts/`.
3. Pick one, run `refine.py` on it. Confirm a higher-res image lands in
   `./final/`.
4. Watch `nvidia-smi -l 1` in a third terminal across both calls — VRAM should
   climb during generation and drop back down once each script exits (each
   script makes one blocking call per run and exits after downloading, it
   doesn't hold the model loaded between invocations beyond what ComfyUI
   itself caches).

**On OOM / node failures:** ComfyUI reports these as an `execution_error`
message on the websocket, not an HTTP error — a script that only checks the
`/prompt` response would queue successfully and then hang forever. `client.py`'s
`ComfyClient.run()` listens for `execution_error` explicitly and raises
`ComfyExecutionError` with the failing node and message as soon as it arrives;
both scripts catch that and print a clear error (with an OOM-specific hint)
instead of hanging. If you hit this in practice, lower `--batch`,
`--width`/`--height`, or `--upscale-by` first.

## Not in v1 (per spec, intentionally skipped)

- Picker UI — drop `./drafts/*.png` into a Claude chat instead.
- Multi-GPU / queue workers — single 4090, one job at a time.
- LoRA training for a consistent Selovast/cartography house style — worth
  doing later, out of scope here.

## Layout

```
comfy_pipeline/
  client.py             ComfyUI HTTP + websocket client
  workflow_utils.py      load/patch workflow JSON by node title
  generate.py             batch-of-4 CLI
  refine.py                refine/upscale CLI
  workflows/
    batch_generate_api.json
    refine_upscale_api.json
  drafts/                 generate.py output (gitignored)
  final/                    refine.py output (gitignored)
```
