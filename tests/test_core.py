from __future__ import annotations

import unittest

from computer.monitors import virtual_bounds
from core.personality_engine import score_options
from memory.semantic_vector.vector_store import add_document, search
from security.permission_manager import check_action, check_command
from security.safety_modes import set_safety_mode
from research.technology_watcher import classify_research_item
from learning.skill_manager import run_skill


class EveCoreTests(unittest.TestCase):
    def tearDown(self):
        set_safety_mode("safe_mode", "test cleanup")

    def test_safety_modes_gate_commands(self):
        set_safety_mode("safe_mode", "test")
        self.assertFalse(check_command("Remove-Item x").allowed)
        set_safety_mode("unrestricted_mode", "test")
        self.assertTrue(check_command("Remove-Item x").allowed)
        self.assertTrue(check_action("admin").allowed)

    def test_virtual_bounds_shape(self):
        bounds = virtual_bounds()
        self.assertIn("width", bounds)
        self.assertIn("height", bounds)

    def test_vector_search(self):
        add_document("unit-test", "A Eve controla rato teclado e browser por visao.")
        rows = search("rato teclado browser", limit=1)
        self.assertTrue(rows)

    def test_research_classifier(self):
        result = classify_research_item("New agent benchmark", "Tool using agents and automation")
        self.assertTrue(result["useful"])

    def test_personality_scoring(self):
        rows = score_options(["melhorar OCR", "limpar ficheiros"])
        self.assertEqual(rows[0]["option"], "melhorar OCR")

    def test_publish_skill_requires_approval(self):
        with self.assertRaises(PermissionError):
            run_skill("draft/x_publish_text_learning")


if __name__ == "__main__":
    unittest.main()
