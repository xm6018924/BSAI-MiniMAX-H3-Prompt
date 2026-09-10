"""
BSAI H3 Direct Prompt Node (直通模式独立节点)

与BSAI_H3_PromptTemplate完全分离，避免直通模式的隐藏值污染模板节点。
功能：纯文本直通输出 + 语音输入 + 本地LLM融合自定义修改。
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class BSAI_H3_DirectPrompt:
    """Direct mode / 直通模式 — 独立节点，输出纯文本提示词。

    与模板节点完全分离，互不干扰。
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "H3 提示词直通输出 / Direct H3 prompt output\n输入完整的 H3 提示词，直接输出到下游 / Input a complete H3 prompt, output directly",
                    },
                ),
            },
            "optional": {
                "user_customization": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "可选：自定义修改（本地LLM融合到提示词中）/ Optional: customization merged via local LLM",
                    },
                ),
                "narration": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "画面旁白台词 (可选) / Voice-over narration (optional)",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = (
        "prompt_output (提示词输出)",
        "template_name (模板名称)",
        "generation_mode (生成模式)",
        "description (描述)",
        "video_duration (视频时长)",
        "preview_file (预览文件)",
    )
    FUNCTION = "process"
    CATEGORY = "BSAI"
    OUTPUT_IS_LIST = (False, False, False, False, False, False)
    DESCRIPTION = """
BSAI H3 直通模式节点 / Direct Prompt Node
独立于模板节点，互不干扰。
- 纯文本直通输出
- 支持语音输入（本地离线Vosk识别）
- 支持本地LLM融合自定义修改
"""

    def process(self, prompt, user_customization="", narration=""):
        from BSAI_H3_PromptTemplate import (
            _merge_custom, _append_custom, _inject_narration,
        )
        p = (prompt or "").strip()
        cust = (user_customization or "").strip()
        if cust:
            try:
                merged, _ = _merge_custom(p, cust) if p.strip() else ("", None)
                if merged and merged.strip() and merged != p:
                    p = merged
                else:
                    p = _append_custom(p, cust)
            except Exception:
                p = _append_custom(p, cust)
        p = _inject_narration(p, narration)
        return (p, "直通模式 | Direct Mode", "Direct / 直通", "Direct H3 prompt / 直通 H3 提示词", 0, "")


NODE_CLASS_MAPPINGS = {
    "BSAI_H3_DirectPrompt": BSAI_H3_DirectPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_H3_DirectPrompt": "BSAI H3 Direct Prompt (直通模式)",
}
