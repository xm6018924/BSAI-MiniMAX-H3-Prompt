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
                        "tooltip": "Selected via visual template browser below / 通过下方可视化模板浏览器选择\nClick a template to auto-fill this field / 点击模板自动填充此字段",
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

Categorized templates: I2VA / T2VA / FL2VA / Ref2VA + Expression + Growth + Timelapse + Combat
分类模板：图生视频 / 文生视频 / 首尾帧生成 / 多模态融合 + 人物表情 + 生长类 + 延时摄影 + 武打对打

Features / 功能特点:
- Visual template browser with search / 可视化模板浏览器，支持搜索
- Cascading selection: Category > Subcategory > Template / 级联选择：分类 > 子类 > 模板
- GIF preview on the right panel / 右侧 GIF 预览
- Optional user customization textarea / 可选的补充修改文本框
- External prompt text input port (external_prompt) for modify/supplement / 外部提示词文本输入端口（external_prompt），用于修改或补充
- Bilingual template names (中文 | English) / 模板名称中英双语对照
- 46 expression & micro-expression templates / 46个表情与微表情模板
- All new templates follow MiniMax H3 prompt SKILL rules / 新增模板严格遵循 MiniMax H3 提示词 SKILL 规则
"""

    def get_template(self, template_select, user_customization="", external_prompt=""):
        tpl = _find_template(template_select)

        # Collect extra instruction sections (external port first, then textarea)
        extra_sections = []
        ext = (external_prompt or "").strip()
        if ext:
            extra_sections.append("--- External Prompt / 外部提示词 ---\n" + ext)
        cust = (user_customization or "").strip()
        if cust:
            extra_sections.append("--- User Customization / 用户自定义 ---\n" + cust)
        extra_text = "\n\n".join(extra_sections)

        if tpl is None:
            custom_text = (template_select or "").strip()
            if custom_text and not custom_text.startswith("("):
                prompt = custom_text
            else:
                prompt = ""
            if extra_text:
                prompt = (prompt + "\n\n" if prompt.strip() else "") + extra_text
            return (prompt, "Custom / 自定义", "System Recommended / 系统推荐", "Custom prompt / 自定义提示词", 0, "")

        prompt = tpl.get("prompt", "")

        if extra_text:
            prompt = prompt + "\n\n" + extra_text

        name = tpl.get("name", "")
        name_en = tpl.get("name_en", "")
        # Bilingual template name (Chinese | English)
        name_label = f"{name} | {name_en}" if name_en else name
        mode = tpl.get("generation_mode", "System Recommended / 系统推荐")
        desc = tpl.get("description", "")
        duration = int(tpl.get("duration", 0))
        preview = tpl.get("preview", "")

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
