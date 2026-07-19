# Civitai post draft — paste into the model description

**Suggested post setup**: type "Other" (or "Workflows" if you prefer), name
"Krea 2 Moodboard + Identity Edit for Forge Neo", tags: krea 2, forge, tool, style transfer, image editing.
Attach the release zip AND link the GitHub repo. Add your own A/B showcase images (moodboard on/off,
identity edit source→result — prompts embedded).

---

## Krea 2 Moodboard + Identity Edit — for SD WebUI Forge Neo

Two features that bring krea.ai-style **vibe transfer** and **identity-preserving editing** to the
Krea 2 (K2) model in [Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo) —
no ComfyUI needed.

### 🎨 Moodboard
Drop reference images into a gallery — generations inherit their **style/vibe**. Training-free, built on
K2's native Qwen3-VL vision conditioning:
- **Vibe strength** + **extract mode** (style ↔ subject: keep the palette/texture/mood, or keep the
  subject and let your prompt restyle it)
- **Style crops** (scramble composition so only style transfers), **indirect mode** (references are
  hidden from the image model — structurally cannot copy poses)
- Multiple references blend into one joint vibe (packed vision span — no grid/collage artifacts)

### 👤 Identity Edit
Instruction-based editing with the community [krea2_identity_edit LoRA](https://civitai.com/models/2761113)
(port of [ComfyUI-Krea2Edit](https://github.com/lbouaraba/comfyui-krea2edit)):
*"create a photo of this person at a night market"* — same face, same outfit, relit to the new scene.
- Dual conditioning: in-context VAE tokens (RoPE frame 1) + image-grounded instruction encoding
- Grounded negative (needed for CFG > 1 recipes), `grounding_px` likeness↔obedience dial, two-ref support,
  aspect-ratio handling (match source, crop source to your output AR, or the new **fit**)
- **v1.2 support**: `ref_boost` reference-fidelity dial (try 2–6) and the **fit** geometry — sources are
  fitted in pixel space to your output resolution (blur-proof, no more AR-matching requirement,
  matches the v1.2 LoRA's training)
- **Composes with the Moodboard**: identity from the edit source + style from the moodboard in one gen

### Install (short version)
1. `git apply krea2-features-backend.patch` from your Forge Neo root (current neo branch)
2. Copy the two folders from `extensions/` into `extensions/`
3. Text encoder: [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2) `qwen3vl_4b_bf16.safetensors`
   (or fp8_scaled) in the VAE/Text Encoder dropdown next to your K2 checkpoint
4. For editing: the identity-edit LoRA at strength 1.0 · Euler/Simple · Turbo 8 steps CFG 1 (most edits;
   v1.2 LoRA: 8–12 steps) or Raw 20–40 steps CFG 3 (removals) · ≤2MP

Full details in the bundled README/INSTALL and on GitHub:
- Forge Neo: **https://github.com/RedNodeAI/forge-neo-krea2-toolkit**
- ComfyUI nodes (moodboard + identity edit + fusion, with ready-made example workflows): **https://github.com/RedNodeAI/ComfyUI-Krea2Moodboard**

### Workflows included (ComfyUI)
- **Basic moodboard t2i** and **identity edit + moodboard fusion** — lean examples, core nodes + the
  pack only, ready to run.
- **Krea_Workflow_Public** — the full production pipeline (JoyCaption auto-captioning of your
  references, wildcards, fusion, AR handling, upscale pass). Needs ~12 common node packs — the full
  dependency table is in the GitHub README; everything installs via ComfyUI-Manager.

### Credits
[Haoming02](https://github.com/Haoming02) (Forge Neo) · [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
(Qwen3-VL ports) · [lbouaraba](https://github.com/lbouaraba/comfyui-krea2edit) (identity-edit recipe +
LoRA, Apache-2.0) · ethanfel & ostris (K2 vision-conditioning recipes) · Krea.ai (Krea 2, Community License)

Code: AGPL-3.0 (same as Forge Neo). Not affiliated with Krea.ai, Haoming02, or the LoRA author.
No model weights are redistributed here — download them from their linked sources.
