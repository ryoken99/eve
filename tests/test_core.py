from __future__ import annotations

import unittest

from computer.monitors import virtual_bounds
from core.paths import SKILLS_DIR, WORKSPACE_DIR
from core.personality_engine import score_options
from learning.skill_learning_loop import run_skill_learning_loop, skill_result_successful
from app.eve_codex import natural_browser_target, relevant_entity_memory
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
            run_skill("trusted/x_publish_text_learning")

    def test_skill_learning_loop_corrects_and_promotes(self):
        draft = SKILLS_DIR / "draft" / "unit_learning_loop.json"
        trusted = SKILLS_DIR / "trusted" / "unit_learning_loop.json"
        workspace_file = WORKSPACE_DIR / "unit_learning_loop.txt"
        for path in (draft, trusted, workspace_file):
            if path.exists():
                path.unlink()
        draft.write_text(
            """{
  "name": "unit_learning_loop",
  "description": "Unit test skill that starts broken and is corrected by the learning loop.",
  "risk_level": "low",
  "permissions": [],
  "steps": [
    {
      "action": "write_file",
      "content": "loop learned"
    }
  ],
  "success_check": ["file_written"],
  "version": 1,
  "status": "draft",
  "created_at": "2026-05-06T00:00:00Z",
  "updated_at": "2026-05-06T00:00:00Z"
}
""",
            encoding="utf-8",
        )
        result = run_skill_learning_loop(
            "draft/unit_learning_loop",
            max_attempts=2,
            corrections=[
                {
                    "action": "set_step_field",
                    "match_action": "write_file",
                    "field": "path",
                    "value": "unit_learning_loop.txt",
                }
            ],
            promote_on_success=True,
            success_note="Unit learning loop corrected a missing path and promoted the skill.",
        )
        self.assertEqual(result["status"], "success")
        self.assertFalse(draft.exists())
        self.assertTrue(trusted.exists())
        self.assertEqual(workspace_file.read_text(encoding="utf-8"), "loop learned")
        trusted.unlink()
        workspace_file.unlink()

    def test_skill_result_success_detects_nested_failure(self):
        self.assertFalse(skill_result_successful({"result": {"status": "needs_review"}}))
        self.assertTrue(skill_result_successful({"result": {"status": "published"}}))

    def test_personal_memory_expands_age_and_karate_queries(self):
        age_rows = relevant_entity_memory("qual e a minha idade?", limit=8)
        self.assertTrue(any("24-year-old" in row.get("excerpt", "") or "24 anos" in row.get("excerpt", "") for row in age_rows))
        karate_rows = relevant_entity_memory("que faixa sou no karate?", limit=8)
        self.assertTrue(any("karate" in row.get("excerpt", "").lower() or "faixa branca" in row.get("excerpt", "").lower() for row in karate_rows))

    def test_natural_browser_target(self):
        self.assertEqual(natural_browser_target("abre o navegador"), "https://www.google.com")
        self.assertEqual(natural_browser_target("abre o x.com"), "x.com")
        self.assertIsNone(natural_browser_target("/browser https://x.com"))


if __name__ == "__main__":
    unittest.main()
