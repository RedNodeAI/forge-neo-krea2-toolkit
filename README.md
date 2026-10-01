# Krea 2 Moodboard + Identity Edit for Forge Neo

Two features for the **Krea 2 (K2)** model in [SD WebUI Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo),
built on a full native **Qwen3-VL** vision-encoder integration.

**On Civitai** (release zips + showcase):
[civitai.com/models/2794961](https://civitai.com/models/2794961/krea-2-moodboard-identity-edit-comfyui-nodes-forge-neo)
· ComfyUI sibling: [ComfyUI-Krea2Moodboard](https://github.com/RedNodeAI/ComfyUI-Krea2Moodboard)

⚡ **Plug and play**: one backend patch + two extensions, everything in the normal txt2img UI —
no ComfyUI, no node graphs, no dependency stack.

> **v3.0, October 2026:** Forge Neo 2.28 added its own Krea 2 edit and vision support, which broke
> the July patch. The patches are rebuilt on top of Neo's native support: the full patch needs Neo
> 2.29.1 or newer, an Identity Edit only patch covers 2.28 to 2.29.0, and the July bundle lives in
> `legacy/` for older builds. See INSTALL.md.

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

1. **Forge Neo** (neo branch), 2.29.1 or newer for the full bundle. INSTALL.md lists the patch for older builds.
2. **Qwen3-VL-4B text encoder with vision weights** in your Text Encoder dropdown:
   [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2) → `text_encoders/qwen3vl_4b_bf16.safetensors`
   (the `fp8_scaled` variant also works).
3. For Identity Edit: a krea2_edit LoRA at strength 1.0 (download from its civitai page, not bundled).

## What's in this bundle

| Item | What | Install |
|---|---|---|
| `extensions/` | the Moodboard and Identity Edit extensions | copy into `<forge>/extensions/` |
| `krea2-features-backend.patch` | 4-file `git apply` patch for Neo 2.29.1+: the Moodboard (packed references, native Qwen3-VL processing, strength / extract / indirect) and Identity Edit (ref_boost, fit geometry, grounding_px, grounded negative) on top of Neo's native Krea 2 support | `git apply` from `<forge>` |
| `krea2-identity-edit-backend.patch` | 2-file Identity Edit only patch for Neo 2.28 to 2.29.0 | `git apply` from `<forge>` |
| `legacy/` | the July 2026 bundle for Neo before 2.28 | see INSTALL.md |

See **INSTALL.md** for step-by-step instructions.

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
