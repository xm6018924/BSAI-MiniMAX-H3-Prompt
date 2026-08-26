"""
BSAI H3 Prompt Template Node

One-click ready-to-use H3 prompt templates.
Categorized by generation mode (I2VA/T2VA/FL2VA/Ref2VA) with subcategories
and specific templates. Includes GIF preview support via JS frontend.

Template data: templates/prompt_templates.json
"""

import os
import json

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_JSON = os.path.join(_THIS_DIR, "templates", "prompt_templates.json")


def _load_templates():
    try:
        with open(_TEMPLATE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"categories": []}


_TEMPLATE_CACHE = None


def _get_template_data():
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None:
        _TEMPLATE_CACHE = _load_templates()
    return _TEMPLATE_CACHE


def _find_template(label):
    if not label or label.startswith("("):
        return None
    data = _get_template_data()
    for cat in data.get("categories", []):
        for sub in cat.get("subcategories", []):
            for tpl in sub.get("templates", []):
                full = f"{cat['name']} > {sub['name']} > {tpl['name']}"
                if full == label:
                    return tpl
    return None


# ── Multi-select merging (H3 SKILL three-field composition) ──
_LABEL_SEP = "|||"


def _split_prompt(prompt):
    """Split a template prompt into H3 sections: header, desc, sound, music."""
    p = prompt or ""
    out = {"header": "", "desc": "", "sound": "", "music": ""}
    idx = p.find("integrated_multimodal_description:")
    if idx < 0:
        out["header"] = p.strip()
        return out
    out["header"] = p[:idx].strip()
    body = p[idx:]
    nxt = body.find("overall_soundscape:")
    if nxt < 0:
        nxt = len(body)
    out["desc"] = body[len("integrated_multimodal_description:"):nxt].strip()
    if nxt < len(body):
        tail = body[nxt:]
        m2 = tail.find("non_diegetic_music:")
        if m2 < 0:
            out["sound"] = tail[len("overall_soundscape:"):].strip()
        else:
            out["sound"] = tail[len("overall_soundscape:"):m2].strip()
            out["music"] = tail[m2 + len("non_diegetic_music:"):].strip()
    return out


def _is_na(s):
    return not s or s.strip().upper() in ("", "N/A", "NA", "无")


def _merge_template_prompts(tpls):
    """Merge multiple template prompts into ONE coherent H3 prompt.
    Base = first template (scene/action), overlays = extra camera/directive templates."""
    if not tpls:
        return ""
    if len(tpls) == 1:
        return tpls[0].get("prompt", "")
    base = _split_prompt(tpls[0].get("prompt", ""))
    desc = base["desc"]
    sound = base["sound"]
    music = base["music"]
    for t in tpls[1:]:
        sec = _split_prompt(t.get("prompt", ""))
        label = f"{t.get('name','')} | {t.get('name_en','')}"
        if sec["desc"]:
            desc += f"\n\n# Overlay 叠加模板: {label}\n{sec['desc']}"
        if not _is_na(sec["sound"]):
            if _is_na(sound):
                sound = sec["sound"]
            else:
                sound += "\n" + sec["sound"]
        if _is_na(music) and not _is_na(sec["music"]):
            music = sec["music"]
    parts = []
    if base["header"]:
        parts.append(base["header"])
    parts.append("integrated_multimodal_description: \n" + (desc or "N/A"))
    parts.append("overall_soundscape: \n" + (sound or "N/A"))
    parts.append("non_diegetic_music: \n" + (music or "N/A"))
    return "\n\n".join(parts)


class BSAI_H3_PromptTemplate:
    """One-click H3 prompt template selector with categorized templates and GIF preview."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "template_select": (
                    "STRING",
                    {
                        "default": "(None / 自定义 / Custom)",
                        "tooltip": "Selected via visual template browser below / 通过下方可视化模板浏览器选择\nClick templates to stack (multi-select), separated by ||| / 点击模板叠加多选，以 ||| 分隔\nCombined into one H3 prompt / 合并输出为一个 H3 提示词",
                    },
                ),
                "user_customization": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "Optional: append custom modifications to the selected template / 可选：在选中模板后追加自定义修改\nThis text will be appended to the prompt output / 此文本将追加到提示词输出中",
                    },
                ),
            },
            "optional": {
                "external_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "forceInput": True,
                        "tooltip": "External prompt text input port / 外部提示词文本输入端口\nConnect from another node to modify or supplement the template prompt / 可从其他节点连接外部文本，用于修改或补充模板提示词\nThis text is appended to the prompt output / 此文本将追加到提示词输出中",
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
    FUNCTION = "get_template"
    CATEGORY = "BSAI"
    OUTPUT_IS_LIST = (False, False, False, False, False, False)
    DESCRIPTION = """
One-click H3 prompt template selector / 一键式 H3 提示词模板选择器

Categorized templates: I2VA / T2VA / FL2VA / Ref2VA + Expression + Growth + Timelapse + Combat + Cinematic
分类模板：图生视频 / 文生视频 / 首尾帧生成 / 多模态融合 + 人物表情 + 生长类 + 延时摄影 + 武打对打 + 电影运镜

Features / 功能特点:
- Visual template browser with search / 可视化模板浏览器，支持搜索
- Cascading selection: Category > Subcategory > Template / 级联选择：分类 > 子类 > 模板
- Multi-select stacking: combine 2+ templates (e.g. combat + camera move) into one H3 prompt / 多选叠加：组合 2+ 个模板（如武打+运镜）合并为一个 H3 提示词
- GIF/WebP preview on the right panel / 右侧预览动画
- Optional user customization textarea / 可选的补充修改文本框
- External prompt text input port (external_prompt) for modify/supplement / 外部提示词文本输入端口（external_prompt），用于修改或补充
- Bilingual template names (中文 | English) / 模板名称中英双语对照
- 46 expression & micro-expression templates / 46个表情与微表情模板
- All new templates follow MiniMax H3 prompt SKILL rules / 新增模板严格遵循 MiniMax H3 提示词 SKILL 规则
"""

    def get_template(self, template_select, user_customization="", external_prompt=""):
        # Support multi-select: labels joined by "|||", e.g. "武打打斗模板 > 多图成战类 > 贴身缠斗 ||| 电影运镜模板 > 跟随与环绕类 > 环绕镜头"
        labels = [x.strip() for x in (template_select or "").split(_LABEL_SEP) if x.strip()]
        tpls = []
        for lbl in labels:
            t = _find_template(lbl)
            if t is not None:
                tpls.append(t)

        # Collect extra instruction sections (external port first, then textarea)
        extra_sections = []
        ext = (external_prompt or "").strip()
        if ext:
            extra_sections.append("--- External Prompt / 外部提示词 ---\n" + ext)
        cust = (user_customization or "").strip()
        if cust:
            extra_sections.append("--- User Customization / 用户自定义 ---\n" + cust)
        extra_text = "\n\n".join(extra_sections)

        if not tpls:
            custom_text = (template_select or "").strip()
            if custom_text and not custom_text.startswith("("):
                prompt = custom_text
            else:
                prompt = ""
            if extra_text:
                prompt = (prompt + "\n\n" if prompt.strip() else "") + extra_text
            return (prompt, "Custom / 自定义", "System Recommended / 系统推荐", "Custom prompt / 自定义提示词", 0, "")

        # Merge all selected templates into one coherent H3 prompt
        prompt = _merge_template_prompts(tpls)

        if extra_text:
            prompt = prompt + "\n\n" + extra_text

        primary = tpls[0]
        # Bilingual merged name list: "贴身缠斗 | Close Grappling + 环绕镜头 | Orbit (Arc Shot)"
        name_label = " + ".join(
            f"{t.get('name','')} | {t.get('name_en','')}" if t.get("name_en") else t.get("name", "")
            for t in tpls
        )
        mode = primary.get("generation_mode", "System Recommended / 系统推荐")
        if len(tpls) > 1:
            mode = f"{mode} | 多模板叠加 Multi-Stack"
        desc = primary.get("description", "")
        if len(tpls) > 1:
            desc += " | 叠加 Overlay: " + " + ".join(t.get("name", "") for t in tpls[1:])
        duration = int(primary.get("duration", 0))
        preview = primary.get("preview", "")

        return (prompt, name_label, mode, desc, duration, preview)

    @classmethod
    def IS_CHANGED(s, template_select, user_customization="", external_prompt=""):
        return float("nan")


NODE_CLASS_MAPPINGS = {
    "BSAI_H3_PromptTemplate": BSAI_H3_PromptTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_H3_PromptTemplate": "BSAI H3 Prompt Template (提示词模板)",
}
