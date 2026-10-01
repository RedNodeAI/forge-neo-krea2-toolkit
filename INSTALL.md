**Installation for current Forge Neo (neo branch)**

`<forge>` is your Forge Neo root folder (it has `webui.bat`, `backend/` and `extensions/` in it).
Check your version at the bottom of the WebUI page.

Forge Neo added its own Krea 2 edit and vision support in 2.28, which broke the July 2026 patch.
The patches here are rebuilt on top of Neo's native support.

**1. Backend patch**

Pick the one for your Neo version and run it from `<forge>`:

| Neo version | Patch | Gives you |
|---|---|---|
| 2.29.1 and newer | `krea2-features-backend.patch` (4 files) | Moodboard, Identity Edit and Re-render |
| 2.28 to 2.29.0 | `krea2-identity-edit-backend.patch` (2 files) | Identity Edit only (or update Neo for the Moodboard and Re-render) |
| before 2.28 | `legacy/krea2-features-backend-july2026.patch` | Moodboard and Identity Edit, July 2026 build |

```
git apply --verbose "path/to/krea2-features-backend.patch"
```

The patches only touch Krea 2 and Qwen3-VL code. Other models are not affected. The Moodboard's
native vision processing (DeepStack and 3-axis positions) only switches on while a Moodboard encode
runs; everything else keeps Neo's own behaviour.

If you applied an older patch before, undo it first with `git checkout -- backend` from `<forge>`,
then update Neo and apply the new one.

If `git apply` still reports conflicts, open an issue with your Neo version and commit.

**2. Extensions**

Copy the three folders from `extensions/` into `<forge>/extensions/`. With the Identity Edit patch, copy
only `sd-forge-krea2-edit`. With the legacy patch, use the extensions in `legacy/extensions/`.

**3. Text encoder**

[Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2), `text_encoders/qwen3vl_4b_bf16.safetensors`
(or `fp8_scaled`) into `<forge>/models/text_encoder/`, selected in the VAE / Text Encoder dropdown with
your Krea 2 checkpoint.

**4. The edit LoRA (Identity Edit only)**

A krea2_edit LoRA at strength 1.0, for example [krea2_identity_edit](https://civitai.com/models/2761113)
(not bundled; weights also on [HF conradlocke/krea2-identity-edit](https://huggingface.co/conradlocke/krea2-identity-edit)).
With the v1.2 LoRA use AR mode "fit source to output (v1.2)", 8 to 12 steps on Turbo, and try
ref_boost 2 to 6.

You do not need Neo's own "[Krea2] Enable Reference" setting for these extensions. They work with the
setting on or off.

**5. For Re-render**

An ai-toolkit Krea 2 edit LoRA, for example Anything2Real (not bundled), in your prompt at strength 1.0.
Keep "Use the recipe sampling" on and the Reference mode on KV cache for Anything2Real.

**6. Restart the WebUI**

The Krea2 Moodboard, Krea2 Identity Edit and Krea2 Re-render accordions appear in txt2img and img2img. The Moodboard
settings live under Settings, Krea2 Moodboard.
