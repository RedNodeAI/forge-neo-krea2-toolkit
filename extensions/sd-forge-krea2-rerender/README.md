**Krea2 Re-render** (Forge Neo extension)

Renders a picture again from itself through an ai-toolkit Krea 2 edit LoRA, for example Anything2Real
(illustration in, photograph out). It is the Forge Neo version of the Re-render tab in RedNode Studio for ComfyUI.

How it works: the source is desaturated, cropped and sized to the output, read by Qwen3-VL at 384x384 area under
a "Picture 1:" label, and VAE-encoded at up to 1 MP as the reference. The reference is conditioned at t=0 the way
ai-toolkit trains these LoRAs:

- **KV cache**: the reference runs once at t=0, attending only to itself, and its keys and values join every
  step's attention. For LoRAs trained with ai-toolkit's kv_cache option, Anything2Real among them.
- **t=0 in sequence**: the reference rides in the sequence at t=0. For other ai-toolkit edit LoRAs.

**Use**

1. Put the LoRA in your prompt at strength 1.0, for example `<lora:anything2real:1>`.
2. Open Krea2 Re-render, drop the source in (in img2img, leave it empty to use the img2img picture).
3. Keep "Use the recipe sampling" on: Euler, Beta at 0.5 / 0.7, 8 steps, CFG 1.
4. Generate. In img2img, denoise below 1 keeps part of the source.

The instruction replaces the prompt text; the default is "transform the image to realistic photograph".
Saturation -20, longest side 1536 and rounding 512 are the recipe's values.

Needs the Krea 2 toolkit backend patch (`krea2-features-backend.patch`) and the qwen3vl_4b text encoder with its
vision weights.
