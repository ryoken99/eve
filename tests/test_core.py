from __future__ import annotations

import unittest

from computer.monitors import virtual_bounds
from core.self_report import functional_self_report
from core.paths import SKILLS_DIR, WORKSPACE_DIR
from core.personality_engine import score_options
from learning.skill_learning_loop import run_skill_learning_loop, skill_result_successful
from app.eve_codex import _format_interface_message, _safe_profile_name, normalize_speaker, speaker_role, natural_browser_target, relevant_entity_memory
from memory.memory_manager import context_bundle
from memory.sandro_profile_builder import build_sandro_core_memory
from dream.dream_cycle import run_dream_cycle
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

    def test_auth_profile_names_are_filesystem_safe(self):
        self.assertEqual(_safe_profile_name(" Minha Conta Principal "), "minha-conta-principal")
        self.assertEqual(_safe_profile_name("../outra conta!"), "outra-conta")
        self.assertEqual(_safe_profile_name(""), "default")

    def test_codex_instructor_has_separate_chat_role(self):
        self.assertEqual(normalize_speaker("instrutor"), "codex")
        self.assertEqual(speaker_role("codex"), "codex_instructor")
        self.assertEqual(speaker_role("sandro"), "user")

    def test_interface_message_format_marks_source(self):
        text = _format_interface_message({"source": "codex_instructor", "timestamp": "2026-05-08T00:00:00Z", "content": "ola"})
        self.assertIn("codex_instructor -> Eve", text)
        self.assertIn("ola", text)

    def test_sandro_core_memory_enters_context(self):
        build_sandro_core_memory()
        bundle = context_bundle(20000)
        self.assertIn("Sandro Core Memory", bundle)
        self.assertIn("Sandro tem 26 anos", bundle)
        self.assertIn("faixa azul nas duas artes", bundle)
        self.assertIn("Carlos e o mestre no Pinhal Novo", bundle)
        self.assertIn("The Magic Way - Juan Tamariz", bundle)
        self.assertIn("Kuroko no Basket", bundle)
        self.assertIn("drag=a", bundle)

    def test_functional_self_report_does_not_claim_consciousness(self):
        report = functional_self_report("unit-test")
        self.assertIn("nao e prova de consciencia subjectiva", report["claim_boundary"])
        self.assertIn("caution", report["functional_state"])

    def test_dream_cycle_creates_auditable_outputs(self):
        payload = run_dream_cycle("2099-01-01")
        self.assertIn("dream_report", payload)
        self.assertIn("self_report", payload)
        self.assertIn("long_term", payload["promotion_rules"])


if __name__ == "__main__":
    unittest.main()
