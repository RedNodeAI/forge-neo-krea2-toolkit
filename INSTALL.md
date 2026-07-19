# Installation (targets current Forge Neo, `neo` branch, July 2026+)

`<forge>` = your Forge Neo root folder (contains `webui.bat`, `backend/`, `extensions/`).

## 1. Backend patch (one file, ~680 lines)

From `<forge>`:

```
git apply --verbose "path/to/krea2-features-backend.patch"
```

Touches only: `backend/nn/llm/llama.py`, `backend/text_processing/qwen3vl_engine.py`,
`backend/nn/krea.py`, `backend/diffusion_engine/krea.py` — all K2/Qwen3-VL paths; other models
are unaffected. (It also activates Neo's dormant native Qwen3-VL processing — deepstack +
interleaved mrope — and fixes a latent emphasis crash on image-spliced prompts.)

If `git apply` reports conflicts, your Neo predates/postdates this bundle — check for a newer
release or apply the hunks by hand.

## 2. Extensions

Copy both folders from `extensions/` into `<forge>/extensions/`.

## 3. Text encoder

[Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2) → `text_encoders/qwen3vl_4b_bf16.safetensors`
(or `fp8_scaled`) into `<forge>/models/text_encoder/`, selected in the VAE/Text Encoder dropdown with
your Krea 2 checkpoint.

## 4. For Identity Edit

A krea2_edit LoRA at strength 1.0, e.g. [krea2_identity_edit](https://civitai.com/models/2761113)
(not bundled; weights also on [HF conradlocke/krea2-identity-edit](https://huggingface.co/conradlocke/krea2-identity-edit)).
With the **v1.2** LoRA, use AR mode "fit source to output (v1.2)", 8–12 steps on Turbo, and try
ref_boost 2–6.

## 5. Restart the WebUI

Both accordions appear in txt2img/img2img. The moodboard settings live under
Settings → Krea2 Moodboard.
