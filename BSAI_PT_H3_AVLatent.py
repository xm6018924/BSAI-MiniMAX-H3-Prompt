class PT_H3ConcatAVLatent:
    """Concatenate video and audio latents into a single AV latent."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video_latent": ("LATENT",),
                "audio_latent": ("LATENT",),
            }
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("av_latent",)
    FUNCTION = "concat"
    CATEGORY = "BSAI-Nodes/MiniMax-H3"

    def concat(self, video_latent, audio_latent):
        out = dict(video_latent)
        out["audio_samples"] = audio_latent["samples"]
        return (out,)


class PT_H3SeparateAVLatent:
    """Separate an AV latent back into video and audio latents."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "av_latent": ("LATENT",),
            }
        }

    RETURN_TYPES = ("LATENT", "LATENT")
    RETURN_NAMES = ("video_latent", "audio_latent")
    FUNCTION = "split"
    CATEGORY = "BSAI-Nodes/MiniMax-H3"

    def split(self, av_latent):
        video = {k: v for k, v in av_latent.items() if k != "audio_samples"}
        audio = {"samples": av_latent["audio_samples"]}
        return (video, audio)


NODE_CLASS_MAPPINGS = {
    "PT_H3ConcatAVLatent": PT_H3ConcatAVLatent,
    "PT_H3SeparateAVLatent": PT_H3SeparateAVLatent,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PT_H3ConcatAVLatent": "BSAI PT_H3 Concat AV Latent",
    "PT_H3SeparateAVLatent": "BSAI PT_H3 Separate AV Latent",
}
