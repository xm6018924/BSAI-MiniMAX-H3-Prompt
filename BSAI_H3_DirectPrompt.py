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
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False, False, False, False, False, False)
    DESCRIPTION = """
BSAI H3 直通模式节点 / Direct Prompt Node
独立于模板节点，互不干扰。
- 纯文本直通输出
- 支持语音输入（本地离线Vosk识别）
- 支持本地LLM融合自定义修改
"""

    @staticmethod
    def _apply_direct_smart_rules(p):
        """直通智能规则：当输入含“参考视频N做动作 / 无配音无旁白”等中文指令时，
        在输出最前面注入动作参考与静音锁定头，保证下游 H3 按动作参考+静音理解，
        而不是把动作指令误当旁白。用户原文完整保留在下文。"""
        if not p:
            return p
        import re as _re
        low = p.lower()
        has_motion = bool(_re.search(
            r"参考视频|动作参考|模仿.*动作|按.*视频.*动作|视频\s*\d+\s*[中里]的?人?物|"
            r"motion\s*reference|reference\s*video", low))
        has_silent = bool(_re.search(
            r"[无不]配音|[无不]旁白|[无不]说话|[无不]发声|[无不]出声|无配乐|静音|无声|silent|"
            r"no\s*voice|no\s*narration|no\s*dialogue|without\s*(voice|narration|dialogue)", low))
        # 先剔除否定静音短语再测肯定旁白意图，避免“无配音无旁白”被误判为旁白。
        _noise = _re.sub(r"[无不]配音|[无不]旁白|[无不]说话|[无不]发声|[无不]出声|无配乐|静音|无声", "", low)
        has_narr = bool(_re.search(
            r"旁白|配音|口播|台词|说出|念出|朗读|voice\s*over|narration|narrate|speak|say\b|dialogue|字幕", _noise))
        if (has_motion or has_silent) and not has_narr:
            parts = []
            if has_motion:
                vids = _re.findall(r"参考视频\s*(\d+)|视频\s*(\d+)\s*[中里]的?人?物?", p)
                v = next((x[0] or x[1] for x in vids if any(x)), "N")
                parts.append(
                    f"[ACTION REFERENCE / 动作参考] <Video {v}> is the ONLY motion source for the "
                    f"character from <Picture 1> — copy the motion EXACTLY frame by frame as described "
                    f"below; <Picture 1> is the ONLY appearance source — copy the face/appearance EXACTLY. "
                    f"视频{v}为唯一动作参考，按下方描述逐帧照抄动作；图1为唯一外观参考，面部/外观照抄。"
                )
            if has_silent:
                parts.append(
                    "[SILENT / 无配音无旁白] NO voice-over, NO narration, NO dialogue — the character "
                    "is completely silent; overall_soundscape: ambient sounds ONLY; non_diegetic_music: N/A. "
                    "全程无配音无旁白，角色不出声，仅环境声。"
                )
            p = " ".join(parts) + "\n\n" + p
        return p

    def process(self, prompt, user_customization="", narration=""):
        # ComfyUI 新版不再把插件目录加入 sys.path，顶层绝对导入会失败，
        # 因此依次尝试 绝对导入 → 相对导入，保证在真实 ComfyUI 与独立测试中均可运行。
        try:
            from BSAI_H3_PromptTemplate import (
                _merge_custom, _append_custom, _inject_narration,
            )
        except ImportError:
            from .BSAI_H3_PromptTemplate import (
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
        # ── 直通智能规则：动作参考 / 静音锁定（防止下游把动作指令当旁白）──
        p = self._apply_direct_smart_rules(p)
        result = (p, "直通模式 | Direct Mode", "Direct / 直通", "Direct H3 prompt / 直通 H3 提示词", 0, "")
        # 返回 ui + result：ui 部分会触发前端 executed 事件并显示在节点上，
        # result 部分作为真实下游数据（与普通 tuple 返回完全一致）。
        return {
            "ui": {"text": [p]},
            "result": result,
        }


NODE_CLASS_MAPPINGS = {
    "BSAI_H3_DirectPrompt": BSAI_H3_DirectPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_H3_DirectPrompt": "BSAI H3 Direct Prompt (直通模式)",
}
