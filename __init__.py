# BSAI MiniMax H3 Prompt - ComfyUI Custom Node
# GitHub: https://github.com/xm6018924/BSAI-MiniMAX-H3-Prompt

from .BSAI_MiniMAX_H3_Prompt import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Merge AV Latent nodes (concat/separate for MiniMax-H3)
try:
    from .BSAI_PT_H3_AVLatent import NODE_CLASS_MAPPINGS as _AV_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as _AV_DISPLAY
    NODE_CLASS_MAPPINGS.update(_AV_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(_AV_DISPLAY)
except Exception:
    pass

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']