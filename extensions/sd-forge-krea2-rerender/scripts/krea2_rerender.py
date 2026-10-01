import math

import gradio as gr
import numpy as np
import torch
from PIL import Image

from modules import images, scripts, sd_models
from modules.api import api
from modules.processing import StableDiffusionProcessing, StableDiffusionProcessingImg2Img
from modules.shared import device, opts
from modules.ui_components import InputAccordion

info = """
<b>Krea 2 Re-render</b>: the picture is rendered again from itself, through an ai-toolkit edit LoRA such as
<b>Anything2Real</b>. Add the LoRA to your prompt (<code>&lt;lora:...:1&gt;</code>); the instruction below replaces
the prompt text. In img2img the img2img picture is the source when the box is empty, and denoise below 1 keeps
part of it.<br>
<b>Requires:</b> the qwen3vl_4b (vision) text encoder and the Krea 2 toolkit backend patch.
"""

WANT = "transform the image to realistic photograph"
REF_MODES = ["KV cache (kv_cache LoRAs, Anything2Real)", "t=0 in sequence (other ai-toolkit edit LoRAs)"]
VL_AREA = 384 * 384  # what the vision encoder sees, as in ai-toolkit training
REF_AREA = 1024 * 1024  # the reference latent carries the detail


class Krea2Rerender(scripts.Script):
    sorting_priority = 532

    def __init__(self):
        self.cached_parameters: list = None
        self.armed: torch.Tensor = None
        self.armed_mode: str = "kv"
        self.armed_instruction: str = WANT

    def title(self):
        return "Krea2 Re-render"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with InputAccordion(value=False, label=self.title()) as enable:
            gr.HTML(info)
            source = gr.Image(
                label="Source image" + (" (empty = the img2img picture)" if is_img2img else ""),
                type="pil",
                sources=["upload", "clipboard"],
                height=300,
                elem_id=self.elem_id("rerender_source"),
            )
            instruction = gr.Textbox(
                value=WANT,
                lines=2,
                label="Instruction",
                info="Replaces the prompt text for the re-render. LoRA tags in the prompt still apply",
                elem_id=self.elem_id("rerender_instruction"),
            )
            ref_mode = gr.Radio(
                choices=REF_MODES,
                value=REF_MODES[0],
                label="Reference mode",
                info="How the LoRA was trained. KV cache: the reference is computed once at t=0 and only attends to itself (Anything2Real). t=0 in sequence: the reference rides along at t=0",
                elem_id=self.elem_id("rerender_mode"),
            )
            with gr.Row():
                saturation = gr.Slider(
                    minimum=-100,
                    maximum=0,
                    step=1,
                    value=-20,
                    label="Saturation",
                    info="Colour cut on the source before it is read, as in the recipe",
                    elem_id=self.elem_id("rerender_saturation"),
                )
                longest = gr.Slider(
                    minimum=512,
                    maximum=2048,
                    step=64,
                    value=1536,
                    label="Longest side",
                    info="The output is the source's shape at this size",
                    elem_id=self.elem_id("rerender_longest"),
                )
                round_to = gr.Dropdown(
                    choices=["16", "64", "512"],
                    value="512",
                    label="Round to",
                    info="Output sides snap to this; the source is center-cropped to match",
                    elem_id=self.elem_id("rerender_round"),
                )
            recipe = gr.Checkbox(
                value=True,
                label="Use the recipe sampling",
                info="Euler, Beta scheduler at 0.5 / 0.7 (beta57), 8 steps, CFG 1. Off keeps your own sampler settings",
                elem_id=self.elem_id("rerender_recipe"),
            )

        return [enable, source, instruction, ref_mode, saturation, longest, round_to, recipe]

    def _source(self, p, source):
        if source is not None:
            return self.to_pil(source)
        if isinstance(p, StableDiffusionProcessingImg2Img) and getattr(p, "init_images", None):
            return self.to_pil(p.init_images[0])
        return None

    def before_process(self, p: StableDiffusionProcessing, enable: bool, source, instruction: str = WANT, ref_mode: str = REF_MODES[0], saturation: float = -20, longest: int = 1536, round_to: str = "512", recipe: bool = True):
        if not enable:
            return
        img = self._source(p, source)
        if img is None:
            return
        w, h = self.target_size(img, int(longest), int(round_to))
        p.width, p.height = w, h
        if recipe:
            p.sampler_name = "Euler"
            p.scheduler = "Beta"
            p.steps = 8
            p.cfg_scale = 1.0
            p.override_settings["beta_dist_alpha"] = 0.5
            p.override_settings["beta_dist_beta"] = 0.7

    def process(self, p: StableDiffusionProcessing, enable: bool, source, instruction: str = WANT, ref_mode: str = REF_MODES[0], saturation: float = -20, longest: int = 1536, round_to: str = "512", recipe: bool = True):
        img = self._source(p, source) if enable else None
        if img is None or not hasattr(p.sd_model, "arm_edit"):
            if self.cached_parameters is not None:
                self.cached_parameters = None
                self.armed = None
                self.bust_cond_caches(p)
                if hasattr(p.sd_model, "clear_edit"):
                    p.sd_model.clear_edit(release_refs=True)
            return

        self.armed_mode = "t0" if str(ref_mode).startswith("t=0") else "kv"
        self.armed_instruction = (instruction or "").strip() or WANT
        prepared = self.prepare(img, float(saturation), p.width, p.height)

        p.extra_generation_params["Krea2 Re-render"] = f"{self.armed_mode}, saturation {saturation:g}, {p.width}x{p.height}, instruction: {self.armed_instruction}"

        key = [str(sd_models.model_data.forge_loading_parameters), self.armed_mode, self.armed_instruction, float(saturation), p.width, p.height, self.hash_image(prepared)]
        self.bust_cond_caches(p)
        if self.cached_parameters != key or self.armed is None:
            self.cached_parameters = key
            arr = np.array(prepared, dtype=np.float32) / 255.0
            self.armed = torch.from_numpy(arr).to(device=device, dtype=torch.float32).unsqueeze(0)

    def arm(self, p: StableDiffusionProcessing):
        if self.armed is not None and hasattr(p.sd_model, "arm_edit"):
            p.sd_model.arm_edit(
                [self.armed],
                ref_mode=self.armed_mode,
                picture_labels=True,
                vl_area=VL_AREA,
                ref_area=REF_AREA,
                instruction=self.armed_instruction,
            )

    def process_batch(self, p: StableDiffusionProcessing, *args, **kwargs):
        self.arm(p)

    def before_hr(self, p: StableDiffusionProcessing, *args):
        self.arm(p)

    def postprocess(self, p: StableDiffusionProcessing, processed, *args):
        if self.armed is not None and hasattr(p.sd_model, "clear_edit"):
            p.sd_model.clear_edit(release_refs=True)

    @staticmethod
    def target_size(img: Image.Image, longest: int, snap: int) -> tuple[int, int]:
        """The source's shape scaled so its longest side is `longest`, sides snapped to `snap`."""
        sw, sh = img.size
        scale = longest / max(sw, sh)
        return max(snap, round(sw * scale / snap) * snap), max(snap, round(sh * scale / snap) * snap)

    @staticmethod
    def prepare(img: Image.Image, saturation: float, width: int, height: int) -> Image.Image:
        """Desaturate, center-crop to the output's aspect ratio, resize to the output size (lanczos)."""
        img = images.flatten(img, opts.img2img_background_color).convert("RGB")
        amount = max(0.0, -saturation) / 100.0
        if amount > 0:
            arr = np.asarray(img, dtype=np.float32)
            lum = arr[..., 0] * 0.2126 + arr[..., 1] * 0.7152 + arr[..., 2] * 0.0722
            arr = arr * (1.0 - amount) + lum[..., None] * amount
            img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        sw, sh = img.size
        target = width / height
        if abs(sw / sh - target) > 1e-3:
            if sw / sh > target:
                nw = max(1, round(sh * target))
                left = (sw - nw) // 2
                img = img.crop((left, 0, left + nw, sh))
            else:
                nh = max(1, round(sw / target))
                top = (sh - nh) // 2
                img = img.crop((0, top, sw, top + nh))
        return img.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def bust_cond_caches(p: StableDiffusionProcessing):
        # class-level shared cache lists: clear IN PLACE
        for name in ("cached_c", "cached_uc", "cached_hr_c", "cached_hr_uc"):
            cache = getattr(p, name, None)
            if isinstance(cache, list):
                for i in range(len(cache)):
                    cache[i] = None

    @staticmethod
    def to_pil(img) -> Image.Image:
        if isinstance(img, str):
            return api.decode_base64_to_image(img)
        if isinstance(img, np.ndarray):
            return Image.fromarray(img)
        return img

    @staticmethod
    def hash_image(img: Image.Image) -> int:
        img = img.resize((64, 64), Image.Resampling.LANCZOS).convert("L")
        return hash(str(list(img.getdata())))
