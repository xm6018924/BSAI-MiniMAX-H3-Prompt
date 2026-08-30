"""
Test suite for anime_to_live_action (I2V) template.
Updated for v2 - concise edge-to-center transition pattern.
"""
import os
import sys
import json
import unittest

_NODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE_JSON = os.path.join(_NODE_DIR, "templates", "prompt_templates.json")
_PREVIEW_DIR = os.path.join(_NODE_DIR, "web", "previews")

TEMPLATE_ID = "anime_to_live_action"


def _find_template(data, tid):
    for cat in data.get("categories", []):
        for sub in cat.get("subcategories", []):
            for tpl in sub.get("templates", []):
                if tpl.get("id") == tid:
                    return tpl, cat["name"], sub["name"]
    return None, None, None


class TestAnimeToLiveAction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(_TEMPLATE_JSON, encoding="utf-8") as f:
            cls.data = json.load(f)
        cls.template, cls.cat, cls.sub = _find_template(cls.data, TEMPLATE_ID)

    # ── 1. JSON validity ──
    def test_01_valid_json(self):
        self.assertIsNotNone(self.template, "Template not found in JSON")
        self.assertIsInstance(self.template, dict)

    def test_02_template_in_right_category(self):
        self.assertEqual(self.cat, "图生视频")
        self.assertEqual(self.sub, "风格迁移类")

    # ── 2. Required fields ──
    def test_03_required_fields(self):
        required = ["id", "name", "name_en", "description", "preview",
                     "generation_mode", "duration", "needs_image", "tags", "prompt"]
        for field in required:
            self.assertIn(field, self.template, f"Missing field: {field}")

    def test_04_tags_nonempty(self):
        self.assertGreater(len(self.template["tags"]), 0, "Tags should not be empty")

    def test_05_duration_positive(self):
        self.assertGreater(self.template["duration"], 0, "Duration should be > 0")

    def test_06_needs_image_true(self):
        self.assertTrue(self.template["needs_image"], "Should need_image=True for I2V")

    # ── 3. Preview file ──
    def test_07_preview_file_exists(self):
        preview = self.template.get("preview", "")
        self.assertTrue(preview, "Preview filename should not be empty")
        fpath = os.path.join(_PREVIEW_DIR, preview)
        self.assertTrue(os.path.isfile(fpath), f"Preview file not found: {fpath}")

    def test_08_preview_file_size_reasonable(self):
        preview = self.template["preview"]
        fpath = os.path.join(_PREVIEW_DIR, preview)
        size = os.path.getsize(fpath)
        self.assertGreater(size, 5 * 1024, "Preview should be > 5KB")
        self.assertLess(size, 5 * 1024 * 1024, "Preview should be < 5MB")

    # ── 4. H3 I2VA SKILL compliance ──
    def test_09_i2va_first_line_instruction(self):
        prompt = self.template["prompt"]
        self.assertTrue(
            prompt.startswith("For the target video, at 0.00 seconds"),
            "Prompt must start with the standard I2VA first-frame alignment instruction"
        )
        self.assertIn("<Picture 1>", prompt[:150])
        self.assertIn("fully referenced", prompt[:200])

    def test_10_three_core_fields(self):
        prompt = self.template["prompt"]
        self.assertIn("integrated_multimodal_description:", prompt)
        self.assertIn("overall_soundscape:", prompt)
        self.assertIn("non_diegetic_music:", prompt)

    def test_11_shot_timeline_structure(self):
        prompt = self.template["prompt"]
        self.assertIn("[Shot 1]", prompt)
        self.assertIn("[Shot 2]", prompt)
        self.assertRegex(prompt, r"\[0-\d+s\]", "Should have time range for Shot 1")
        # Shot 2 time marker: "At 00:04.000 [4-8s]" (MM:SS.sss format followed by range)
        self.assertRegex(prompt, r"At \d{2}:\d{2}\.\d{3}.*\[\d+-\d+s\]",
                         "Should have shot 2 time marker with MM:SS.sss format")

    # ── 5. Key photorealism keywords ──
    def test_12_skin_realism(self):
        prompt = self.template["prompt"].lower()
        self.assertIn("skin", prompt)
        self.assertIn("pores", prompt)

    def test_13_eye_realism(self):
        prompt = self.template["prompt"].lower()
        self.assertIn("eyes", prompt)
        self.assertIn("human", prompt)

    def test_14_hair_realism(self):
        prompt = self.template["prompt"].lower()
        self.assertIn("hair", prompt)
        self.assertIn("individual strands", prompt)

    def test_15_cinema_quality_keywords(self):
        prompt = self.template["prompt"].lower()
        quality_keywords = ["8k", "85mm", "depth of field", "bokeh"]
        for kw in quality_keywords:
            self.assertIn(kw, prompt, f"Missing quality keyword: {kw}")

    def test_16_identity_preservation(self):
        prompt = self.template["prompt"].lower()
        self.assertIn("same person", prompt)
        self.assertIn("preserved", prompt)
        self.assertIn("hair color", prompt)
        self.assertIn("eye color", prompt)

    def test_17_transition_mechanism(self):
        prompt = self.template["prompt"].lower()
        # Edge-to-center transition pattern (proven to work)
        self.assertIn("edges", prompt)
        self.assertIn("spreads", prompt)
        self.assertIn("transformation", prompt)

    # ── 6. Node integration ──
    def test_18_node_module_exists(self):
        # Just verify the node file exists and is valid Python
        node_file = os.path.join(_NODE_DIR, "BSAI_H3_PromptTemplate.py")
        self.assertTrue(os.path.isfile(node_file), "Node file should exist")
        # Basic syntax check
        with open(node_file, encoding="utf-8") as f:
            source = f.read()
        compile(source, node_file, "exec")  # Will raise SyntaxError if invalid

    def test_19_external_prompt_action_override(self):
        prompt = self.template["prompt"]
        # Should have an action section that external prompts can customize
        # (at minimum, describe character movement in shot 2)
        self.assertIn("blink", prompt.lower())
        self.assertIn("head", prompt.lower())


if __name__ == "__main__":
    print(f"Template ID : {TEMPLATE_ID}")
    print(f"Template JSON: {_TEMPLATE_JSON}")
    print(f"Preview file : {_PREVIEW_DIR}")
    print("-" * 70)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnimeToLiveAction)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 70)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"  Result: {passed}/{total} tests passed")
    print(f"  Status: {'ALL PASSED ✓' if failed == 0 else 'FAILED ✗'}")
    print("=" * 70)

    sys.exit(0 if failed == 0 else 1)
