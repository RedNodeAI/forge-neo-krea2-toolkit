# Krea2 Moodboard (Forge Neo)

Recreates krea.ai's **Moodboard** for the Krea 2 (K2) model: drop reference images into a gallery and
generations inherit their style/vibe. Training-free — images are encoded by the Qwen3-VL-4B vision tower and
spliced into K2's native conditioning stream as **one packed vision span** (all references' tokens inside a
single `<|vision_start|><|image_pad|><|vision_end|>` block). K2 was never trained with multi-reference
inputs: both `Picture N:` labels *and* repeated bare blocks read as "an image containing N pictures" and
produce grid/collage outputs, so a single structural image reference is the only grid-safe form — and it
makes multiple references blend into one joint vibe.

This transfers **style, not content**: palette, lighting, texture, mood — not subjects or composition.

## Requirements

- A Krea 2 checkpoint.
- The **Qwen3-VL-4B text encoder with vision weights**:
  [`Comfy-Org/Krea-2`](https://huggingface.co/Comfy-Org/Krea-2) → `text_encoders/qwen3vl_4b_bf16.safetensors`
  (~8.9 GB), placed in a text-encoder folder (e.g. `models/text_encoder`) and selected in the
  **Text Encoder** dropdown alongside the K2 checkpoint. The console logs
  `Detected Qwen3-VL-4B (vision) text encoder` when it loads correctly.
  (bf16 is the supported file; fp8_scaled is untested.)

## Usage

1. Open the **Krea2 Moodboard** accordion (txt2img or img2img), enable it, add 1–10 reference images.
2. Set **Vibe strength** and **Vibe extract**: `1.0` feeds the raw reference detail to the model in both
   modes. Lowering strength purifies whichever aspect is selected:
   - **style / vibe**: spans collapse toward a style-statistics signature (mean and ±std tokens —
     palette, texture contrast, mood); subjects fade. `0.4–0.6` is the Krea-like sweet spot.
   - **subject / concept**: spans are whitened — style statistics are removed while the token
     structure (subjects, objects, composition) survives; your prompt controls the look.
   Magnitude isn't scaled (RMSNorms would erase that) — the slider controls information content.
3. **Image tokens position**: `before prompt` lets the prompt tokens *see* the images (stronger, can pull
   subject/content); `after prompt` keeps the prompt image-blind (subtler, style-leaning).
4. **Reference processing**: `full image` keeps everything the encoder sees; `quadrant crops (2x2)`
   scrambles composition but each crop can still show recognizable subjects; `fine tiles (4x4)` leaves
   mostly texture/palette-level content — **subjects are largely never encoded at all**, the strongest
   subject-leak fix.
5. **Style directive** (default on): adds *"style/palette/lighting/texture/mood from the references,
   subjects and composition from the text alone"* next to the vision span. K2 follows its conditioning
   text descriptively.
6. **Indirect vibe**: the image model never sees the reference tokens — they are deleted from the final
   conditioning after the text encoder ran. Style arrives only through how the references
   re-contextualized your prompt tokens inside the LLM; copying pose/subject from reference tokens is
   structurally impossible. Subtler effect; forces `before prompt`.
7. Generate. The infotext records image count + hashes + all knob values (images themselves are not
   restorable from infotext).

### Tuning ladder

| Step | Extract | Strength | Position | Ref processing | Directive | Indirect |
|---|---|---|---|---|---|---|
| Raw reference (near edit behavior) | either | 1.0 | before | full image | off | off |
| Subject transfer, prompt-controlled style | **subject** | 0.4–0.6 | before | full image | on | off |
| Balanced style | style | 0.6 | before | quadrants 2x2 | on | off |
| Krea-style vibe | style | 0.5 | after | **fine tiles 4x4** | on | off |
| Maximum style-only | style | 0.4 | (forced before) | fine tiles 4x4 | on | **on** |

Notes: subject extract wants **full image** (crops destroy the subject); the directive text automatically
matches the selected extract mode.

## Settings (Settings → Krea2 Moodboard)

- **Vision encoder pixel budget**: `384` (~144 vision tokens/image, fast — default) or `1024`
  (up to ~1024 tokens/image, never upscales; more detail pickup but slower sampling with many images).
- **Native Qwen3-VL image processing**: on = full DeepStack injection + 3-axis mrope (closest to how the
  encoder was trained); off = ComfyUI-parity splice-only mode (what community nodes use). A/B both — they
  produce different flavors of style transfer.

## Notes / limitations

- Reference images influence only the **positive** prompt conditioning.
- Prompt emphasis `(...)` and prompt-editing `[a:b:N]` are not supported together with the moodboard
  (same envelope as Qwen-Image edit); switching text-encoder files slightly changes text-only outputs
  because the VL encoder uses its trained rope (theta 5e6) — this matches ComfyUI's K2 behavior.
- Changing rope: with the VL encoder loaded but moodboard disabled, K2 behaves as ComfyUI's K2 does.
- GGUF/mmproj variants of the VL encoder are not supported yet.
