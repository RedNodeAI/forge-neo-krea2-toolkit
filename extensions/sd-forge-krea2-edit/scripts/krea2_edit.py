import math

import gradio as gr
import numpy as np
import torch
from PIL import Image

from modules import images, scripts, sd_models
from modules.api import api
from modules.processing import StableDiffusionProcessing
from modules.shared import device, opts
from modules.ui_components import InputAccordion

info = """
<b>Krea 2 Identity Edit</b> — instruction-based, identity-preserving editing for K2.<br>
Give it a source image and write the edit instruction as your <b>prompt</b> ("create a photo of this person at a night market").<br>
<b>Requires:</b> the qwen3vl_4b (vision) text encoder <b>and</b> a krea2_edit LoRA
(e.g. <code>krea2_identity_edit_v1</code>) loaded at strength 1.0.<br>
Recommended: Turbo 8 steps / CFG 1 for most edits; Raw 20 steps / CFG 3 for removals. Generate at &le;2MP.
"""


class Krea2Edit(scripts.Script):
    sorting_priority = 531

    def __init__(self):
        self.cached_parameters: list[str | int] = None
        self.armed_tensors: list[torch.Tensor] = None
        self.armed_grounding: int = 768

    def title(self):
        return "Krea2 Identity Edit"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with InputAccordion(value=False, label=self.title()) as enable:
            gr.HTML(info)
            with gr.Row():
                source = gr.Image(
                    label="Source image",
                    type="pil",
                    sources=["upload", "clipboard"],
                    height=300,
                    elem_id=self.elem_id("edit_source"),
                )
                source_b = gr.Image(
                    label="2nd reference (two-ref LoRAs: scene first, subject here)",
                    type="pil",
                    sources=["upload", "clipboard"],
                    height=300,
                    elem_id=self.elem_id("edit_source_b"),
                )
            grounding_px = gr.Slider(
                minimum=0,
                maximum=2048,
                step=64,
                value=768,
                label="grounding_px",
                info="caps the longest side fed to Qwen3-VL. Lower = stronger edit adherence; higher = stronger identity/likeness (768 balanced, 1024+ for people, 0 = native)",
                elem_id=self.elem_id("edit_grounding"),
            )
            ar_mode = gr.Radio(
                choices=["match source (resize output)", "crop source to output AR", "off"],
                value="match source (resize output)",
                label="Aspect ratio handling",
                info="training pairs are same-size, so source and output ARs must agree: either the output adopts the source's AR at your target resolution, or the source is center-cropped to your chosen output AR",
                elem_id=self.elem_id("edit_ar_mode"),
            )

        return [enable, source, source_b, grounding_px, ar_mode]

    def process(self, p: StableDiffusionProcessing, enable: bool, source, source_b, grounding_px: int = 768, ar_mode: str = "match source (resize output)"):
        if not (enable and source is not None and hasattr(p.sd_model, "arm_edit")):
            if self.cached_parameters is not None:
                self.cached_parameters = None
                self.armed_tensors = None
                self.bust_cond_caches(p)
                if hasattr(p.sd_model, "clear_edit"):
                    p.sd_model.clear_edit()
            return

        if not p.sd_model.moodboard_available:
            message = "[Krea2 Edit] The loaded text encoder is text-only. Select the qwen3vl_4b (vision) text encoder."
            print(message)
            try:
                gr.Warning(message)
            except Exception:
                pass
            return

        sources = [self.to_pil(source)]
        if source_b is not None:
            sources.append(self.to_pil(source_b))
        self.armed_grounding = int(grounding_px)

        mode = str(ar_mode)
        if mode.startswith("match"):
            sw, sh = sources[0].size
            scale = math.sqrt((p.width * p.height) / (sw * sh))
            p.width = max(64, round(sw * scale / 64) * 64)
            p.height = max(64, round(sh * scale / 64) * 64)
        elif mode.startswith("crop"):
            sources = [self.crop_to_ar(img, p.width, p.height) for img in sources]

        hashes = [self.hash_image(img) for img in sources]
        p.extra_generation_params["Krea2 Edit"] = (
            f"{len(sources)} source(s) [{', '.join(f'{h & 0xFFFFFF:06x}' for h in hashes)}], grounding_px {self.armed_grounding}, AR {mode.split(' ')[0]}"
        )

        cache: list[str | int] = [str(sd_models.model_data.forge_loading_parameters), self.armed_grounding, mode, p.width, p.height]
        cache.extend(hashes)

        # Always bust while enabled: conds must be recomputed with the armed sources every run.
        self.bust_cond_caches(p)

        if self.cached_parameters != cache or self.armed_tensors is None:
            self.cached_parameters = cache

            tensors = []
            for img in sources:
                image = images.flatten(img, opts.img2img_background_color)
                image = np.array(image, dtype=np.float32) / 255.0
                image = torch.from_numpy(image).to(device=device, dtype=torch.float32)
                tensors.append(image.unsqueeze(0))  # (1, H, W, C), 0..1

            self.armed_tensors = tensors

    def arm(self, p: StableDiffusionProcessing):
        if self.armed_tensors is not None and hasattr(p.sd_model, "arm_edit"):
            p.sd_model.arm_edit(self.armed_tensors, grounding_px=self.armed_grounding)

    def process_batch(self, p: StableDiffusionProcessing, *args, **kwargs):
        self.arm(p)

    def before_hr(self, p: StableDiffusionProcessing, *args):
        self.arm(p)

    def postprocess(self, p: StableDiffusionProcessing, processed, *args):
        if self.armed_tensors is not None and hasattr(p.sd_model, "clear_edit"):
            p.sd_model.clear_edit()
            from backend.args import dynamic_args
            dynamic_args["ref_latents"].clear()

    @staticmethod
    def bust_cond_caches(p: StableDiffusionProcessing):
        # Clear the class-level shared cache lists IN PLACE (see sd-forge-krea2-moodboard).
        for name in ("cached_c", "cached_uc", "cached_hr_c", "cached_hr_uc"):
            cache = getattr(p, name, None)
            if isinstance(cache, list):
                for i in range(len(cache)):
                    cache[i] = None

    @staticmethod
    def crop_to_ar(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Center-crop the image to the target aspect ratio (no resize — the DiT handles scale)."""
        sw, sh = img.size
        target = target_w / target_h
        if abs(sw / sh - target) < 1e-3:
            return img
        if sw / sh > target:  # source wider than target -> crop width
            new_w = max(1, round(sh * target))
            left = (sw - new_w) // 2
            return img.crop((left, 0, left + new_w, sh))
        new_h = max(1, round(sw / target))  # source taller -> crop height
        top = (sh - new_h) // 2
        return img.crop((0, top, sw, top + new_h))

    @staticmethod
    def to_pil(img) -> Image.Image:
        if isinstance(img, str):
            return api.decode_base64_to_image(img)
        if isinstance(img, np.ndarray):
            return Image.fromarray(img)
        return img

    @staticmethod
    def hash_image(img: Image.Image) -> int:
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        img = img.convert("L")
        return hash(str(list(img.getdata())))
