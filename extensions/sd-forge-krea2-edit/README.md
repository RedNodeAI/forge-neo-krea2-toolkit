# Krea2 Identity Edit (Forge Neo)

Instruction-based, identity-preserving image editing for Krea 2, using community **krea2_edit LoRAs**
(e.g. [krea2_identity_edit](https://civitai.com/models/2761113) — v1.2 recommended). Port of the
[ComfyUI-Krea2Edit](https://github.com/lbouaraba/comfyui-krea2edit) node pack.

Give it a source image and write the edit as your prompt: *"create a photo of this person at a night
market"* — same face, same outfit, relit to the new scene.

## How it works (dual conditioning, training-matched)

- **Appearance path**: the source image is VAE-encoded and prepended to the DiT token stream as clean
  in-context tokens at RoPE frame 1 (target = frame 0). The LoRA is trained to preserve frame-1 content.
- **Semantic path**: the instruction is encoded *together with the source image* through Qwen3-VL
  (same machinery as the Krea2 Moodboard extension), so "the man on the left" resolves against the image.
- The **negative prompt is grounded too** (training's unconditional = empty prompt + same image) —
  required for CFG > 1 recipes.

## Requirements

- Krea 2 checkpoint + the **qwen3vl_4b (vision)** text encoder (same as the moodboard).
- A krea2_edit LoRA at **strength 1.0** (e.g. `krea2_identity_edit_v1_2.safetensors` in `models/Lora`).

## Usage

1. Enable **Krea2 Identity Edit** (txt2img), drop the source image, write the instruction as the prompt.
2. Pick an **Aspect ratio handling** mode: `fit source to output (v1.2)` fits the source in pixel
   space to your output resolution before encoding — blur-proof, keeps your AR, matches the v1.2
   LoRA's training geometry (use this with v1.2 weights). For v1/v1.1 weights (same-size training
   pairs): `match source` resizes the output to the source's AR at your target resolution;
   `crop source to output AR` keeps YOUR width/height and center-crops the reference to fit it.
3. Recommended (from the LoRA author): most edits → Turbo, 8 steps, CFG 1 (v1.2 LoRA: 8–12 steps —
   8 favors composition, 12 face detail). Removals → Raw, 20 steps, CFG 3. Generate at ≤2MP.
4. **grounding_px**: lower = stronger edit adherence; higher = stronger identity/likeness
   (768 balanced, 1024+ for people, 0 = native resolution).
5. **ref_boost** (v1.2 dial): multiplies target→reference attention — 1.0 = off, >1 pulls the result
   harder toward the reference's appearance (the LoRA author suggests 2–6). The `ref_boost (scene)`
   slider is the same dial for the first image in two-ref setups.
6. Two-ref LoRAs (experimental upstream): scene image in the first slot, subject in the second.

## Notes

- Uses txt2img (the target starts from pure noise — the source enters only through the conditioning).
- **Combining with the Moodboard**: enable BOTH accordions to fuse them — identity/subject from the
  edit source, style/vibe from the moodboard images. The moodboard's blocks ride in front of the edit
  conditioning on the positive side (its strength/extract/indirect settings apply to its own span only;
  the edit grounding span is never touched), the negative stays edit-only so the style lives in the CFG
  guidance delta. Recommended moodboard config for this: style extract, full image, indirect ON,
  directive ON.
- The infotext records source hashes + grounding_px (sources are not restorable from infotext).
