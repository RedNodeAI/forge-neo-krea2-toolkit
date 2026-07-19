# Krea 2 Moodboard + Identity Edit for Forge Neo

Two features for the **Krea 2 (K2)** model in [SD WebUI Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo),
built on a full native **Qwen3-VL** vision-encoder integration:

## 🎨 Krea2 Moodboard
Drop reference images into a gallery — generations inherit their **style / vibe** (like krea.ai's
Moodboard). Training-free. Controls:
- **Vibe strength** — 1.0 raw reference, lower = purer extract
- **Vibe extract** — `style` (palette/texture/mood; subjects fade) or `subject` (composition survives,
  style is whitened away so your prompt controls the look)
- **Reference processing** — full image / quadrant crops / fine 4×4 tiles (tiles = strongest
  composition-scrambling, style-only transfer)
- **Style directive**, **Indirect vibe** (refs hidden from the image model — structurally cannot copy
  pose/subject), image tokens before/after prompt
- Multiple references are packed into ONE vision span → they blend into a joint vibe (and can't
  trigger grid/collage outputs)

## 👤 Krea2 Identity Edit
Instruction-based, identity-preserving editing via community **krea2_edit LoRAs**
([krea2_identity_edit](https://civitai.com/models/2761113), weights also on
[HF conradlocke/krea2-identity-edit](https://huggingface.co/conradlocke/krea2-identity-edit)). Port of
[ComfyUI-Krea2Edit](https://github.com/lbouaraba/comfyui-krea2edit): dual conditioning —
VAE source tokens at RoPE frame 1 (appearance) + image-grounded Qwen3-VL instruction encoding
(semantics), grounded negative for CFG > 1, `grounding_px` likeness↔obedience dial, two-ref support,
aspect-ratio handling (match source / crop source to your AR / **fit**).

**v1.2 dials** (matching the LoRA's v1.2 release):
- **ref_boost** — reference-fidelity dial: multiplies target→reference attention (1.0 = off; the LoRA
  author suggests 2–6). Separate `ref_boost (scene)` slider for the first image in two-ref setups.
- **fit source to output (v1.2)** AR mode — the source is fitted in *pixel space* to your output
  resolution before VAE-encoding: blur-proof (latents are never resized), keeps your chosen AR
  (no more matching the source's), and matches the v1.2 LoRA's training geometry. The older
  match/crop modes remain for v1/v1.1 weights.
- **Auto face-ref prep (2-pass)** — one toggle that rebuilds the subject reference before editing:
  pass 1 extracts the clean, unobstructed person (hats/glasses/hands/props removed, matte natural
  skin), pass 2 makes a front-facing identity headshot from it. Cached per reference image (content
  hash) so it never re-runs for the same picture.

**The two compose**: enable both to take identity from the edit source and style from the moodboard.

## Requirements

1. **Forge Neo** (neo branch). This bundle was built and tested against a July-2026 neo build —
   see INSTALL.md for how the backend part is applied.
2. **Qwen3-VL-4B text encoder with vision weights** in your Text Encoder dropdown:
   [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2) → `text_encoders/qwen3vl_4b_bf16.safetensors`
   (the `fp8_scaled` variant also works — its vision tower is bf16 inside). Console logs
   `Detected Qwen3-VL-4B (vision) text encoder` when correct.
3. For Identity Edit: a krea2_edit LoRA at strength 1.0 (download from its civitai page — not bundled).

## What's in this bundle

| Item | What | Install |
|---|---|---|
| `extensions/` | the two UI extensions | copy into `<forge>/extensions/` |
| `krea2-features-backend.patch` | one ~680-line `git apply` patch for 4 backend files (activates Neo's dormant native Qwen3-VL path + the feature hooks; fixes a latent emphasis crash on image-spliced prompts) | `git apply` from `<forge>` |

Targets **current Forge Neo (neo branch, July 2026+)** — Neo's own Krea 2 support is required (it ships
the Qwen3-VL encoder this builds on). See **INSTALL.md** for step-by-step instructions.

## Quick settings reference

- Moodboard "Krea vibe": extract **style**, strength 0.5, **fine tiles 4×4**, directive on, position after
- Identity Edit: **Euler / Simple**; Turbo 8 steps CFG 1 (most edits; v1.2 LoRA: 8–12 steps — 8 favors
  composition, 12 face detail) or Raw 20–40 steps CFG 3 (removals); ≤2MP; grounding_px 768 (1024+ for
  people); with the v1.2 LoRA use AR mode **fit** and try ref_boost 2–6
- Prompting edits: describe only what changes; anchor with "this person"; one edit per pass

## Credits & License

- [Haoming02](https://github.com/Haoming02) — SD WebUI Forge Neo (this bundle's host application)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) — Qwen3-VL model code ported from `qwen35.py` /
  `qwen3vl.py` / `llama.py` (source URLs in file headers, following Forge Neo's existing porting convention)
- [lbouaraba/ComfyUI-Krea2Edit](https://github.com/lbouaraba/comfyui-krea2edit) (Apache-2.0) — the
  identity-edit dual-conditioning recipe and DiT in-context forward this port implements; and the
  krea2_identity_edit LoRA
- ethanfel (ComfyUI-Krea2TextEncoder) & ostris — validated K2 vision-conditioning recipes
- Krea.ai — Krea 2 (weights under the Krea 2 Community License; the LoRA is a Derivative Model — see its page)

Code in this bundle is distributed under the same license as SD WebUI Forge Neo (AGPL-3.0).
Not affiliated with Krea.ai, Haoming02, or the LoRA author.
