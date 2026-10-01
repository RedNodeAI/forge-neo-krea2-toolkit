import gradio as gr
import numpy as np
import torch
from PIL import Image

from modules import images, scripts, script_callbacks, sd_models, shared
from modules.api import api
from modules.processing import StableDiffusionProcessing
from modules.shared import device, opts
from modules.ui_components import InputAccordion

info = """
<b>Krea 2 Moodboard</b> — reference images set the style/vibe of the generation (like krea.ai's Moodboard).<br>
Images are encoded by the Qwen3-VL vision tower into the K2 conditioning; they transfer <b>style, not content</b>.<br>
<b>Requires:</b> a Krea 2 checkpoint + the <b>qwen3vl_4b</b> text encoder (with vision weights) in the Text Encoder dropdown.
"""


class Krea2Moodboard(scripts.Script):
    sorting_priority = 530

    def __init__(self):
        self.cached_parameters: list[str | int] = None
        self.armed_tensors: list[torch.Tensor] = None
        self.armed_strength: float = 1.0
        self.armed_extract: str = "style"
        self.armed_position: str = "before"
        self.armed_crops: int = 0
        self.armed_style_directive: bool = True
        self.armed_indirect: bool = False

    def title(self):
        return "Krea2 Moodboard"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with InputAccordion(value=False, label=self.title()) as enable:
            gr.HTML(info)
            references = gr.Gallery(
                value=None,
                type="pil",
                interactive=True,
                show_label=False,
                container=False,
                show_download_button=False,
                show_share_button=False,
                label="Moodboard Images",
                min_width=384,
                height=384,
                columns=3,
                rows=1,
                allow_preview=False,
                object_fit="contain",
                elem_id=self.elem_id("moodboard_gallery"),
            )
            strength = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                step=0.05,
                value=0.5,
                label="Vibe strength",
                info="1.0 = raw reference detail; lower = purer extract of whichever aspect is selected below",
                elem_id=self.elem_id("moodboard_strength"),
            )
            extract = gr.Radio(
                choices=["style / vibe", "subject / concept"],
                value="style / vibe",
                label="Vibe extract",
                info="STYLE: lower strength keeps palette/texture/mood, subjects fade. SUBJECT: lower strength keeps subjects/composition, style is whitened away so the prompt controls the look",
                elem_id=self.elem_id("moodboard_extract"),
            )
            position = gr.Radio(
                choices=["before prompt (strong)", "after prompt (subtle)"],
                value="before prompt (strong)",
                label="Image tokens position",
                info="'after prompt' keeps the text tokens image-blind — further reduces subject/content leakage",
                elem_id=self.elem_id("moodboard_position"),
            )
            ref_mode = gr.Radio(
                choices=["full image", "quadrant crops (2x2)", "fine tiles (4x4)"],
                value="full image",
                label="Reference processing",
                info="crops scramble composition; FINE TILES leave mostly texture/palette-level content so subjects are largely never encoded at all — strongest subject-leak fix",
                elem_id=self.elem_id("moodboard_ref_mode"),
            )
            style_directive = gr.Checkbox(
                value=True,
                label="Style directive",
                info="adds 'style/palette/lighting/mood from the references, subjects from the text alone' to the conditioning",
                elem_id=self.elem_id("moodboard_style_directive"),
            )
            indirect = gr.Checkbox(
                value=False,
                label="Indirect vibe (hide refs from the image model)",
                info="the image model never sees the reference tokens — style arrives only through how the references re-contextualize your prompt in the text encoder; structurally cannot copy pose/subject (forces 'before prompt')",
                elem_id=self.elem_id("moodboard_indirect"),
            )

        return [enable, references, strength, extract, position, ref_mode, style_directive, indirect]

    def process(self, p: StableDiffusionProcessing, enable: bool, references: list, strength: float = 1.0, extract: str = "style / vibe", position: str = "before prompt (strong)", ref_mode: str = "full image", style_directive: bool = True, indirect: bool = False):
        if not (enable and references and hasattr(p.sd_model, "arm_moodboard")):
            if self.cached_parameters is not None:
                self.cached_parameters = None
                self.armed_tensors = None
                self.bust_cond_caches(p)
                if hasattr(p.sd_model, "clear_moodboard"):
                    p.sd_model.clear_moodboard()
            return

        if not p.sd_model.moodboard_available:
            message = "[Krea2 Moodboard] The loaded text encoder is text-only. Select the qwen3vl_4b (vision) text encoder to use the moodboard."
            print(message)
            try:
                gr.Warning(message)
            except Exception:
                pass
            return

        references = self.extract_images(references)
        self.armed_strength = float(strength)
        self.armed_extract = "subject" if str(extract).startswith("subject") else "style"
        self.armed_indirect = bool(indirect)
        # Indirect mode needs the prompt tokens to SEE the refs (causal attention) — force "before".
        self.armed_position = "before" if self.armed_indirect else ("after" if str(position).startswith("after") else "before")
        self.armed_crops = 4 if "4x4" in str(ref_mode) else 2 if "2x2" in str(ref_mode) else 0
        self.armed_style_directive = bool(style_directive)

        hashes = [self.hash_image(reference) for reference in references]
        p.extra_generation_params["Krea2 Moodboard"] = (
            f"{len(references)} image(s) [{', '.join(f'{h & 0xFFFFFF:06x}' for h in hashes)}], "
            f"{self.armed_extract} extract, strength {self.armed_strength:g}, {self.armed_position} prompt"
            + (f", {self.armed_crops}x{self.armed_crops} crops" if self.armed_crops else "")
            + (", directive" if self.armed_style_directive else "")
            + (", indirect" if self.armed_indirect else "")
        )

        cache: list[str | int] = [str(sd_models.model_data.forge_loading_parameters), self.armed_strength, self.armed_extract, self.armed_position, self.armed_crops, self.armed_style_directive, self.armed_indirect]
        cache.extend(hashes)

        # Always bust while enabled: conds must be recomputed with the armed images every run
        # (a cache hit would silently reuse conditioning from whatever images were armed last).
        self.bust_cond_caches(p)

        if self.cached_parameters != cache or self.armed_tensors is None:
            self.cached_parameters = cache

            tensors = []
            for reference in references:
                image = images.flatten(reference, opts.img2img_background_color)
                image = np.array(image, dtype=np.float32) / 255.0
                image = torch.from_numpy(image).to(device=device, dtype=torch.float32)
                tensors.append(image.unsqueeze(0))  # (1, H, W, C), 0..1

            self.armed_tensors = tensors

    def arm(self, p: StableDiffusionProcessing):
        if self.armed_tensors is not None and hasattr(p.sd_model, "arm_moodboard"):
            p.sd_model.arm_moodboard(
                self.armed_tensors,
                strength=self.armed_strength,
                position=self.armed_position,
                crops=self.armed_crops,
                style_directive=self.armed_style_directive,
                hide_refs=self.armed_indirect,
                extract=self.armed_extract,
            )

    def process_batch(self, p: StableDiffusionProcessing, *args, **kwargs):
        # Runs before each iteration's setup_conds; re-arm so varying prompts (wildcards) re-encode with images.
        self.arm(p)

    def before_hr(self, p: StableDiffusionProcessing, *args):
        # Hires-fix recomputes conds; re-arm so the moodboard carries into the hires pass.
        self.arm(p)

    def postprocess(self, p: StableDiffusionProcessing, processed, *args):
        # Cond-cache hits skip consumption; never leak armed state into the next run.
        if self.armed_tensors is not None and hasattr(p.sd_model, "clear_moodboard"):
            p.sd_model.clear_moodboard()

    @staticmethod
    def bust_cond_caches(p: StableDiffusionProcessing):
        # Moodboard images are invisible to the cond-cache keys (prompt only), so bust all of them.
        # IMPORTANT: these are class-level lists shared across runs — clear them IN PLACE. Assigning
        # `p.cached_c = [None, None]` would only shadow the shared list for this run and leave the
        # stale conditioning behind for the next one.
        for name in ("cached_c", "cached_uc", "cached_hr_c", "cached_hr_uc"):
            cache = getattr(p, name, None)
            if isinstance(cache, list):
                for i in range(len(cache)):
                    cache[i] = None

    @staticmethod
    def extract_images(gallery: list) -> list[Image.Image]:
        if isinstance(gallery[0], str):
            return [api.decode_base64_to_image(img) for img in gallery]
        return [img for (img, _) in gallery]

    @staticmethod
    def hash_image(img: Image.Image) -> int:
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        img = img.convert("L")
        return hash(str(list(img.getdata())))


def on_ui_settings():
    section = ("krea2_moodboard", "Krea2 Moodboard")
    shared.opts.add_option(
        "krea2_moodboard_vision_budget",
        shared.OptionInfo(
            "384",
            "Vision encoder pixel budget per image",
            gr.Radio,
            {"choices": ["384", "1024"]},
            section=section,
        ).info("384 = ~144 vision tokens/image, fast (Qwen-Image style); 1024 = up to ~1024 tokens/image, never upscales, high detail but slower sampling"),
    )
    shared.opts.add_option(
        "krea2_moodboard_native_vision",
        shared.OptionInfo(
            True,
            "Native Qwen3-VL image processing (DeepStack injection + 3-axis mrope)",
            section=section,
        ).info("disable for ComfyUI-parity mode (splice-only, 1D positions) as used by community K2 style-reference nodes"),
    )


script_callbacks.on_ui_settings(on_ui_settings)
