# ComfyUI + FLUX Local Image Pipeline

A scriptable local batch-generate → pick → refine workflow for ComfyUI, built for
running against your own GPU instead of a hosted service. Two commands:

```
python generate.py --prompt "..." --batch 4                # -> ./drafts/*.png
python refine.py --image ./drafts/pick.png --prompt "..."  # -> ./final/*.png
```

Runs **FLUX.2 Klein 4B** (Apache 2.0, fits in 24 GB, 4-step drafts).

## Status

The workflow JSON here is derived from the FLUX.2 graphs that ship inside
ComfyUI itself (`comfyui_workflow_templates_json/templates/image_flux2_*.json`),
with every node's inputs checked against the live `/object_info` of the running
server — not hand-guessed. The scripts compile and the JSON validates.

Still to confirm on a real run: an end-to-end `generate.py` → `refine.py` pass
with weights present.

## This machine

| Thing | Value |
|---|---|
| ComfyUI | `D:\Creative\AI\ComfyUI` (v0.33.0), served at `http://127.0.0.1:8188` |
| Pipeline venv | `D:\Creative\AI\comfy_pipeline-venv` |
| GPU | RTX 4090, 24 GB |
| Torch | 2.7.1+cu128, CUDA available |

Everything heavy lives on `D:` deliberately — models, caches, and outputs don't
need OneDrive backup. Only this repo stays on `C:`.

> **Downloading large files on this machine — read before pulling weights.**
> Two separate problems bite here, and neither reports an error:
>
> 1. `hf download` writes **zero bytes** using its default Xet transfer backend.
>    Set `HF_HUB_DISABLE_XET=1` to fall back to plain HTTPS.
> 2. Even with Xet disabled, this connection reliably drops at ~330 MB, and
>    `hf download` **does not resume** — on failure it abandons the partial file
>    and restarts from zero into a fresh temp file. It will spin forever,
>    re-fetching the same first third of a file. (Observed: 3.1 GB of traffic for
>    1 GB of progress, three orphaned `.incomplete` files for one blob.)
>
> Use `curl` with `-C -` for anything over a few hundred MB. It resumes into the
> same file and walks straight through the drops:
>
> ```powershell
> curl.exe -L -C - --retry 20 --retry-delay 5 --retry-all-errors `
>   -o D:\Creative\AI\temp\direct\qwen_3_4b.safetensors `
>   https://huggingface.co/Comfy-Org/flux2-klein/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors
> ```
>
> While curl holds the file open, `dir` and `Get-ChildItem` report **0 bytes** —
> NTFS doesn't flush the directory entry until the handle closes. Check progress
> with curl's own meter or `(New-Object System.IO.FileInfo($path)).Length`.
>
> A token does not help: this line is bandwidth-limited to ~3 MB/s in aggregate
> (verified — a second concurrent stream only got 0.88 MB/s while the first ran),
> not rate-limited by Hugging Face.

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

**This pipeline runs FLUX.2 Klein 4B**, from the ungated
[`Comfy-Org/flux2-klein`](https://huggingface.co/Comfy-Org/flux2-klein) repo.
No Hugging Face token is needed — the repo is public, so `hf download` works
unauthenticated.

| Model | License | Commercial use |
|---|---|---|
| **FLUX.2 [klein] 4B** | **Apache 2.0** | **Allowed** — including paid commissions. |
| FLUX.2 [dev] | Non-commercial | Not allowed for anything sold. |
| Qwen-Image 2.0 | Apache 2.0 | Allowed. Still the better pick for legible in-image text (map labels, signage). |

Klein being Apache 2.0 is the reason it's the default here: it removes the
commercial/non-commercial split entirely. It also *fits in 24 GB*, where FLUX.2
[dev] does not — dev is 33 GB of weights plus a 17 GB text encoder, so on a 4090
it offloads to system RAM and takes minutes per image. Klein runs in seconds.

Klein ships in two variants, and the difference matters:

| Variant | Steps | CFG | Negative prompt | Use for |
|---|---|---|---|---|
| `flux-2-klein-4b` (distilled) | 4 | 1.0 | **Ignored** — cfg 1.0 means no classifier-free guidance | Fast drafts |
| `flux-2-klein-base-4b` (base) | 20 | 5.0 | Works | Refine pass, or drafts needing a negative |

`generate.py --model distilled|base` switches between them and sets matching
step/CFG defaults; `refine.py` uses base. If you pass `--negative` at cfg 1.0
the script warns you rather than silently ignoring it.

### Downloading the weights

```powershell
$env:HF_HOME='D:\Creative\AI\huggingface'
$env:HF_HUB_DISABLE_XET='1'          # required — see note above
hf download Comfy-Org/flux2-klein `
  split_files/diffusion_models/flux-2-klein-4b.safetensors `
  split_files/diffusion_models/flux-2-klein-base-4b.safetensors `
  split_files/text_encoders/qwen_3_4b.safetensors `
  split_files/vae/flux2-vae.safetensors `
  --local-dir D:\Creative\AI\temp\hf-stage
```

Then move each file into the folder ComfyUI expects (note `diffusion_models`,
**not** `unet`, and `text_encoders`, **not** `clip`, for FLUX.2):

```
D:\Creative\AI\ComfyUI\models\diffusion_models\   flux-2-klein-4b.safetensors
                                                  flux-2-klein-base-4b.safetensors
D:\Creative\AI\ComfyUI\models\text_encoders\      qwen_3_4b.safetensors
D:\Creative\AI\ComfyUI\models\vae\                flux2-vae.safetensors
```

Restart ComfyUI (or hit refresh in the web UI) so the new files appear in the
node dropdowns.

## Prompting Klein — what we learned on the first real run

Measured on the 4090, 1024², batch of 4:

| Run | Time |
|---|---|
| First batch (cold, loads 15 GB of weights) | 13.8s |
| Subsequent batches (weights resident) | 7.7s |
| Refine to 1536² | 5.2s |

Peak VRAM 13.8 GB of 24.5 GB — no offloading, plenty of headroom for batch 8 or
2048².

**Prompt specificity matters far more than step count.** The same model at the
same 4 steps went from "mammoth standing on a saucer with a *human* in the
cockpit" to a correct render purely by naming the relationship and the era.
Klein follows explicit spatial and stylistic instructions well, but fills gaps
with clichés when you leave them open:

- Say **"seated inside the cockpit"**, not "piloting" — "piloting" alone gets you
  an animal standing on the hull.
- Say what it's doing with its hands/trunk (**"gripping the controls with its
  trunk"**) or it won't interact with anything.
- Name the design language explicitly (**"1960s atomic age polished chrome, fins,
  glowing dial readouts"**). "60s sci-fi vibe" alone drifts toward rusted
  dieselpunk.
- Name the background (**"orbiting a blue planet"**) or you get a generic
  starfield.

## Resolution ceilings — measured, not guessed

VRAM is **not** the limiting factor. Klein was trained around 1024² and loses
spatial coherence well before it runs out of memory:

| Res | Time | Peak VRAM | Result |
|---|---|---|---|
| 1024² | 2.1s | | sharp, correct |
| 1536² | 4.3s | | sharp |
| 2048² | 8.9s | | good, slight anatomy drift |
| 2560² | 14.8s | | coherent, but subject drifts (tusks vanish) |
| 3072² | 37.9s | 17.2 GB | structure collapsing |
| 3584² | 55.4s | 22.7 GB | mush |
| 4096² | 124.4s | 24.0 GB | **total mush** — no subject at all |

4096² never OOM'd. It ran to completion and returned blue fog. Don't read a
successful exit as a usable image.

**Chained refine does not dodge this.** It's tempting to assume that upscaling a
coherent 1536² image protects it — it doesn't, because `refine.py` runs the
diffusion pass *at the target resolution* and hits the same wall. Verified:
1536 → 2304 → 3456 collapsed at the final step.

**The chain is still the best quality path, up to the ceiling.** The 2304² chain
step produced better results than any native generation:

```
generate.py (1024²)  ->  refine.py x1.5 (1536²)  ->  refine.py x1.5 (2304²)
```

Stop at ~2304². Past that, switch to `upscale.py`.

## Step 7 — upscale.py (beyond the diffusion ceiling)

`upscale.py` runs an ESRGAN-family model — purely convolutional, no diffusion. It
has no resolution ceiling and *cannot* reinvent the subject, so structure survives
exactly. Use it when you want more pixels rather than more detail.

```powershell
D:\Creative\AI\comfy_pipeline-venv\Scripts\python.exe upscale.py `
  --image D:\Creative\AI\outputs\final\pick.png --scale 4
```

Verified: 2304² → **9216²** in 18.3s. At 1:1 individual guard hairs resolve
cleanly, chrome edges stay hard, LED segments show no ringing or haloing.

The model is a fixed 4×; other `--scale` values run the 4× then resample by the
remainder with lanczos.

**Upscaler licensing matters as much as the base model.** The popular
`4x-UltraSharp` is **CC-BY-NC-SA — non-commercial**, which would undo the whole
reason for choosing Apache-2.0 Klein. This pipeline defaults to
**`RealESRGAN_x4.pth` (BSD-3-Clause)**, which is commercial-safe. Other
commercial-safe options if you want to compare: BSRGAN and SwinIR (both
Apache-2.0), from the MIT-licensed `uwg/upscaler` repo.

**Known model bias, and the trap in fixing it.** Klein blends bear anatomy into
mammoths — round ears and clawed **bear paws** instead of columnar elephant feet,
consistently across seeds. Adding `bear, bear paws, claws` to the negative prompt
with `--model base` does fix the paws.

But it also **removes the shaggy coat**, leaving a short-haired elephant. Klein's
"woolly/shaggy" concept is evidently entangled with "bear", so suppressing one
suppresses the other. Negative prompts here are a blunt instrument — check what
else went missing, don't just check that the target artefact is gone.

The two variants trade off, and neither wins outright:

| | distilled (cfg 1.0) | base (cfg 3–5) |
|---|---|---|
| Look | cinematic, photoreal, filmic | cleaner, glossier, product-render |
| Fur | shaggy, well-formed | short-haired, wool lost to the negative |
| Feet | bear paws | correct, columnar |
| Speed | 7.7s / 4 images | 54.6s / 4 images |

cfg 5.0 oversaturates noticeably; **cfg 3.0 is the better default** for base.

A useful hybrid: generate on `base` to get anatomy right, then `refine.py
--model distilled --denoise 0.35` to put the photoreal texture back. Tested and
it does recover most of the filmic quality while keeping the corrected feet.

For pure aesthetics though, the best single result in testing was still the
all-distilled chain at 2304².

## Step 3 & 4 — The two workflows

FLUX.2 does **not** use the classic `KSampler` / `DualCLIPLoader` /
`FluxGuidance` graph that FLUX.1 did. The real graph is:

`workflows/batch_generate_api.json` — `UNETLoader` + `CLIPLoader` (single
encoder, `type: flux2`) + `VAELoader` → positive/negative `CLIPTextEncode` →
`CFGGuider` → `SamplerCustomAdvanced`, fed by `RandomNoise`, `KSamplerSelect`,
`Flux2Scheduler`, and `EmptyFlux2LatentImage` (batch_size=4) → `VAEDecode` →
`SaveImage`.

`workflows/refine_upscale_api.json` — same backbone, but `LoadImage` →
`VAEEncode` → `LatentUpscaleBy` supplies the latent, and `SplitSigmasDenoise`
takes the tail of the sigma schedule to get a partial denoise.

Three things that are easy to get wrong:

- **There is no `denoise` input.** `SamplerCustomAdvanced` denoises whatever
  schedule it's handed, so img2img strength comes from `SplitSigmasDenoise`,
  taking output slot **1** (`low_sigmas`).
- **Resolution is set in two places.** `EmptyFlux2LatentImage` sizes the latent,
  but `Flux2Scheduler` *also* takes width/height because it picks its sigma
  shift from the resolution. They must agree. `refine.py` computes the
  post-upscale size for the scheduler rather than passing the source size.
- **`weight_dtype` is `default`, not `fp8_e4m3fn`,** even for fp8 checkpoints —
  the quantisation is already baked into the file.

Every node the scripts touch has a stable `_meta.title` so they're addressable
by name rather than by fragile numeric id. The titles in use are
`unet_loader`, `clip_loader`, `vae_loader`, `positive_prompt`,
`negative_prompt`, `guider`, `sampler_select`, `scheduler`, `empty_latent`,
`noise_seed`, `batch_sampler`, `save_batch` — plus `load_source_image`,
`vae_encode`, `latent_upscale`, `denoise_split`, `refine_sampler`, and
`save_final` in the refine graph.

If you rebuild these graphs in the ComfyUI UI and re-export via **Save (API
Format)** (Settings → enable Dev Mode), re-apply those titles so the scripts
keep working.

## Step 5 — Setup

The pipeline venv is separate from ComfyUI's own and needs only
`websocket-client` and `Pillow`:

```powershell
D:\Creative\AI\comfy_pipeline-venv\Scripts\python.exe -m pip install -r requirements.txt
```

`generate.py` and `refine.py` talk to ComfyUI's HTTP + websocket API directly
(`/prompt`, `/history`, `/view`, `/upload/image`, `/ws`) rather than through the
`comfy_api_simplified` wrapper, so there's one fewer dependency to debug and the
websocket handling (see below) is fully visible in `client.py`.

### generate.py

```powershell
D:\Creative\AI\comfy_pipeline-venv\Scripts\python.exe generate.py `
  --prompt "a weathered Deadlands bounty hunter, dusty coat, cinematic lighting, matte painting" `
  --batch 4
```

Submits the batch workflow, waits for all 4 to finish, downloads them to
`./drafts/` as `{timestamp}_{prompt-slug}_seed{seed}_{index}.png`, and prints
the file paths. Send those thumbnails to Claude in chat to review/pick (no
picker UI in v1).

Defaults to the distilled model at 4 steps. For a negative prompt you need the
base model:

```powershell
... generate.py --model base --prompt "..." --negative "blurry, watermark, text" --batch 4
```

### refine.py

```powershell
D:\Creative\AI\comfy_pipeline-venv\Scripts\python.exe refine.py `
  --image .\drafts\20260819_143012_weathered_deadlands_bounty_hunter_seed123_2.png `
  --prompt "a weathered Deadlands bounty hunter, dusty coat, cinematic lighting, matte painting" `
  --denoise 0.4
```

Uploads the chosen draft to ComfyUI, runs it through the low-denoise upscale
pass, and saves the result to `./final/` with the same timestamp+prompt+seed
naming convention. It reads the source image's dimensions so the Flux2 scheduler
is given the post-upscale size.

Defaults to `--model base` (20 steps, cfg 5.0) since the refine pass is where
negative prompts and extra detail actually pay off. Pass `--model distilled` for
a quick low-effort pass.

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
comfy_pipeline/            (on C:, in OneDrive — backed up)
  client.py                ComfyUI HTTP + websocket client
  workflow_utils.py        load/patch workflow JSON by node title; model presets
  generate.py              batch-of-4 CLI
  refine.py                diffusion refine/upscale CLI (has a coherence ceiling)
  upscale.py               ESRGAN upscale CLI (no ceiling, structure-preserving)
  workflows/
    batch_generate_api.json
    refine_upscale_api.json
    upscale_api.json

D:\Creative\AI\outputs\    (on D: — NOT backed up)
  drafts\                  generate.py output
  final\                   refine.py output
```

Generated images go to `D:` rather than next to the code, so they never sync to
OneDrive. Override the root with the `COMFY_PIPELINE_OUT` environment variable,
or per-run with `--out-dir`. If the configured drive doesn't exist (e.g. the repo
is cloned on another machine), both scripts fall back to `drafts/` and `final/`
beside the code, so nothing breaks.
