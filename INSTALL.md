**Installation for current Forge Neo (neo branch, 2.28 and newer)**

`<forge>` is your Forge Neo root folder (it has `webui.bat`, `backend/` and `extensions/` in it).

This bundle now ships Identity Edit only. Forge Neo 2.28 added its own Krea 2 edit and vision support,
so the patch is small and builds on top of it. The Moodboard has not been ported yet; see the legacy
section at the bottom.

**1. Backend patch (2 files, about 200 lines)**

From `<forge>`:

```
git apply --verbose "path/to/krea2-identity-edit-backend.patch"
```

It only touches `backend/diffusion_engine/krea.py` and `backend/nn/krea.py`. It adds ref_boost, the fit
geometry, the grounding_px cap and the grounded negative on top of Neo's native Krea 2 reference path.
Other models are not affected.

If you applied the old `krea2-features-backend.patch` before, undo it first with
`git checkout -- backend` from `<forge>`, then update Neo and apply the new one.

If `git apply` still reports conflicts, open an issue with your Neo version and commit.

**2. Extension**

Copy `extensions/sd-forge-krea2-edit` into `<forge>/extensions/`. If you have the old
`sd-forge-krea2-moodboard` extension installed, remove it; it needs the old patch.

**3. Text encoder**

[Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2), `text_encoders/qwen3vl_4b_bf16.safetensors`
(or `fp8_scaled`) into `<forge>/models/text_encoder/`, selected in the VAE / Text Encoder dropdown with
your Krea 2 checkpoint.

**4. The edit LoRA**

A krea2_edit LoRA at strength 1.0, for example [krea2_identity_edit](https://civitai.com/models/2761113)
(not bundled; weights also on [HF conradlocke/krea2-identity-edit](https://huggingface.co/conradlocke/krea2-identity-edit)).
With the v1.2 LoRA use AR mode "fit source to output (v1.2)", 8 to 12 steps on Turbo, and try
ref_boost 2 to 6.

You do not need Neo's own "[Krea2] Enable Reference" setting for this extension. It works with the
setting on or off.

**5. Restart the WebUI**

The Krea2 Identity Edit accordion appears in txt2img and img2img.

**Legacy: Forge Neo before 2.28**

The `legacy/` folder keeps the July 2026 bundle: the old 4-file patch, the Moodboard extension and
the Identity Edit extension that matches it. Use it only on a Neo build from July or August 2026; it
does not apply to 2.28 or newer.
