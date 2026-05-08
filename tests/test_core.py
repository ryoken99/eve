from __future__ import annotations

import unittest

from computer.monitors import virtual_bounds
from tools.browser_human import browser_launch_args
from core.self_report import functional_self_report
from core.paths import SKILLS_DIR, WORKSPACE_DIR
from core.personality_engine import score_options
from learning.skill_learning_loop import run_skill_learning_loop, skill_result_successful
from app.eve_codex import _format_interface_message, _safe_profile_name, active_loop_mode, build_loop_prompt, loop_message_limit, normalize_speaker, parse_loop_status, speaker_display_name, speaker_role, natural_browser_target, relevant_entity_memory
from memory.memory_manager import context_bundle
from memory.sandro_profile_builder import build_sandro_core_memory
from dream.dream_cycle import run_dream_cycle
from memory.semantic_vector.vector_store import add_document, search
from security.permission_manager import check_action, check_command
from security.safety_modes import set_safety_mode
from research.technology_watcher import classify_research_item
from learning.skill_manager import run_skill
from tools.web_research import build_research_report_from_pages, candidate_article_links, extract_links, recent_enough_for_query
from core.mission_control import (
    add_checkpoint,
    append_mission_log,
    create_mission,
    list_missions,
    load_mission,
    next_step,
    update_step,
)
from autonomy.autonomy_director import build_autonomy_prompt, run_autonomy_cycle
from autonomy.autonomous_executor import execute_autonomous_backlog, execute_autonomous_mission
from autonomy.token_gate import decide_llm_call, record_llm_call
from autonomy.autonomy_reporter import run_autonomy_report_cycle


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

    def test_browser_launch_args_can_target_monitor(self):
        config = {
            "chrome_path": "chrome.exe",
            "profile_directory": "Profile 2",
            "user_data_dir": "",
            "new_window": True,
            "target_monitor_index": 2,
        }
        monitors = [{"index": 2, "left": 0, "top": 0, "width": 1920, "height": 1080}]
        args = browser_launch_args("https://example.com", config=config, monitors=monitors)
        self.assertIn("--window-position=40,40", args)
        self.assertIn("--window-size=1840,1000", args)

    def test_auth_profile_names_are_filesystem_safe(self):
        self.assertEqual(_safe_profile_name(" Minha Conta Principal "), "minha-conta-principal")
        self.assertEqual(_safe_profile_name("../outra conta!"), "outra-conta")
        self.assertEqual(_safe_profile_name(""), "default")

    def test_codex_instructor_has_separate_chat_role(self):
        self.assertEqual(normalize_speaker("instrutor"), "codex")
        self.assertEqual(speaker_role("codex"), "codex_instructor")
        self.assertEqual(speaker_display_name("codex"), "Codex")
        self.assertEqual(speaker_role("sandro"), "user")

    def test_interface_message_format_marks_source(self):
        text = _format_interface_message({"source": "Eve", "target": "Codex", "timestamp": "2026-05-08T00:00:00Z", "content": "ola"})
        self.assertIn("Eve -> Codex", text)
        self.assertIn("ola", text)

    def test_codex_eve_loop_defaults_to_mode_1(self):
        self.assertEqual(active_loop_mode(), "1")
        self.assertEqual(loop_message_limit("1"), 10)
        self.assertEqual(loop_message_limit("2"), 25)
        self.assertIsNone(loop_message_limit("3"))

    def test_codex_eve_loop_prompt_and_status_parser(self):
        prompt = build_loop_prompt("testar autonomia", step=1, message_count=0, limit=10)
        self.assertIn("Objectivo: testar autonomia", prompt)
        self.assertEqual(parse_loop_status("ok\nLOOP_STATUS: complete"), "complete")
        self.assertEqual(parse_loop_status("exemplo: LOOP_STATUS: complete\nmas ainda nao"), "blocked")
        self.assertEqual(parse_loop_status("preciso de autorizacao"), "blocked")

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

    def test_functional_self_report_expresses_operational_feelings(self):
        report = functional_self_report("unit-test")
        self.assertIn("pensamentos, preferencias e estados emocionais operacionais", report["claim_boundary"])
        self.assertIn("caution", report["functional_state"])
        self.assertIn("felt_orientation", report["inner_perspective"])

    def test_dream_cycle_creates_auditable_outputs(self):
        payload = run_dream_cycle("2099-01-01")
        self.assertIn("dream_report", payload)
        self.assertIn("self_report", payload)
        self.assertIn("long_term", payload["promotion_rules"])

    def test_web_research_report_separates_facts_from_interpretation(self):
        pages = [
            {
                "url": "https://example.com/research/a",
                "title": "Paper A",
                "date": "2026-05-01",
                "text": "Paper A introduces a benchmark. Key findings include stronger evidence tracking.",
            }
        ]
        report = build_research_report_from_pages("recent papers", pages)
        self.assertEqual(report["query"], "recent papers")
        self.assertIn("source_facts", report)
        self.assertIn("eve_interpretation", report)
        self.assertEqual(report["source_facts"][0]["title"], "Paper A")
        self.assertIn("evidence tracking", report["source_facts"][0]["claim"])
        self.assertEqual(report["source_facts"][0]["url"], "https://example.com/research/a")
        self.assertGreaterEqual(report["source_facts"][0]["confidence"], 0.7)
        self.assertIn("auditavel", report["eve_interpretation"][0]["summary"].lower())

    def test_web_research_extract_links_keeps_allowed_domain(self):
        html = '<a href="/research/a">A</a><a href="https://other.test/x">X</a>'
        links = extract_links(html, "https://example.com/research", allowed_domains=["example.com"])
        self.assertEqual(links, ["https://example.com/research/a"])

    def test_web_research_prefers_article_links_over_navigation(self):
        links = [
            "https://www.anthropic.com/research",
            "https://www.anthropic.com/",
            "https://www.anthropic.com/research/team/alignment",
            "https://www.anthropic.com/research/natural-language-autoencoders",
            "https://www.anthropic.com/research/teaching-claude-why",
        ]
        self.assertEqual(
            candidate_article_links(links),
            [
                "https://www.anthropic.com/research/natural-language-autoencoders",
                "https://www.anthropic.com/research/teaching-claude-why",
            ],
        )

    def test_web_research_last_three_months_filters_old_dates(self):
        self.assertTrue(recent_enough_for_query("last 3 months papers", "Apr 2, 2026", now="2026-05-08"))
        self.assertFalse(recent_enough_for_query("last 3 months papers", "Dec 18, 2025", now="2026-05-08"))
        self.assertTrue(recent_enough_for_query("papers", "Dec 18, 2025", now="2026-05-08"))

    def test_mission_control_creates_and_resumes_auditable_mission(self):
        mission = create_mission(
            "unit mission control",
            plan=["abrir fonte", "criar resumo"],
            permissions=["control_browser"],
        )
        self.assertEqual(mission["status"], "draft")
        self.assertEqual(mission["next_step"]["description"], "abrir fonte")
        append_mission_log(mission["id"], "test", "started")
        update_step(mission["id"], 0, "done", note="fonte aberta")
        add_checkpoint(mission["id"], "after_source", {"url": "https://example.com"})
        loaded = load_mission(mission["id"])
        self.assertEqual(loaded["steps"][0]["status"], "done")
        self.assertTrue(any(entry["message"] == "started" for entry in loaded["logs"]))
        self.assertEqual(loaded["checkpoints"][-1]["name"], "after_source")
        self.assertEqual(next_step(loaded)["description"], "criar resumo")
        self.assertTrue(any(item["id"] == mission["id"] for item in list_missions()))

    def test_autonomy_director_creates_low_risk_proposed_missions(self):
        result = run_autonomy_cycle(
            triggers=["no_active_work"],
            max_new_missions=2,
            call_llm=False,
            cycle_name="unit_autonomy",
        )
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["llm_called"])
        self.assertEqual(result["token_decision"]["prompt_type"], "none")
        self.assertLessEqual(len(result["created_missions"]), 2)
        self.assertTrue(result["created_missions"])
        self.assertTrue(all(item["status"] == "proposed" for item in result["created_missions"]))
        self.assertTrue(all(item["risk"] == "low" for item in result["impulses"][: len(result["created_missions"])]))

    def test_autonomy_prompt_marks_no_sensitive_execution(self):
        prompt = build_autonomy_prompt(
            [{"kind": "self_review", "title": "Daily self review", "risk": "low", "reason": "test"}],
            cycle_name="unit",
        )
        self.assertIn("Nao executes acoes sensiveis", prompt)
        self.assertIn("Daily self review", prompt)

    def test_autonomous_executor_completes_low_risk_self_review_and_notifies(self):
        mission = create_mission(
            "Unit autonomous self review",
            plan=["rever estado", "registar relatorio"],
            permissions=["read_memory", "write_memory"],
            status="proposed",
            source="autonomy:unit:self_review",
        )
        result = execute_autonomous_mission(mission["id"], notify_chat=True)
        self.assertEqual(result["status"], "done")
        loaded = load_mission(mission["id"])
        self.assertEqual(loaded["status"], "done")
        self.assertTrue(loaded["checkpoints"])
        self.assertIn("chat_message", result)

    def test_autonomous_backlog_executes_only_allowed_proposed_missions(self):
        allowed = create_mission(
            "Unit allowed autonomous memory hygiene",
            plan=["rever memoria"],
            permissions=["read_memory"],
            status="proposed",
            source="autonomy:unit:memory_hygiene",
        )
        blocked = create_mission(
            "Unit unsupported mission",
            plan=["fazer algo"],
            permissions=[],
            status="proposed",
            source="manual",
        )
        result = execute_autonomous_backlog(max_missions=1, notify_chat=False)
        self.assertTrue(any(item["id"] == allowed["id"] for item in result["executed"]))
        self.assertEqual(load_mission(allowed["id"])["status"], "done")
        self.assertEqual(load_mission(blocked["id"])["status"], "proposed")

    def test_token_gate_calls_llm_for_repeated_error(self):
        context = {
            "impulses": [{"kind": "error_review", "risk": "low"}],
            "recent_errors": [
                {"error_type": "ModuleNotFoundError", "error_text": "No module named x"},
                {"error_type": "ModuleNotFoundError", "error_text": "No module named x"},
            ],
            "call_history": [],
            "now": "2026-05-08T10:00:00Z",
        }
        decision = decide_llm_call(context)
        self.assertTrue(decision["should_call_llm"])
        self.assertEqual(decision["prompt_type"], "error_analysis")
        self.assertIn("erro repetido", decision["reason"])

    def test_token_gate_blocks_cooldown_and_budget(self):
        context = {
            "impulses": [{"kind": "error_review", "risk": "low"}],
            "recent_errors": [
                {"error_type": "ValueError", "error_text": "bad"},
                {"error_type": "ValueError", "error_text": "bad"},
            ],
            "call_history": [{"timestamp": "2026-05-08T09:55:00Z", "prompt_type": "error_analysis"}],
            "now": "2026-05-08T10:00:00Z",
            "cooldown_minutes": 30,
        }
        self.assertFalse(decide_llm_call(context)["should_call_llm"])
        budget_context = dict(context)
        budget_context["call_history"] = [
            {"timestamp": "2026-05-08T08:00:00Z", "prompt_type": "x"},
            {"timestamp": "2026-05-08T09:00:00Z", "prompt_type": "x"},
        ]
        budget_context["daily_budget"] = 2
        self.assertFalse(decide_llm_call(budget_context)["should_call_llm"])

    def test_token_gate_record_llm_call_is_auditable(self):
        path = record_llm_call("unit_test", {"reason": "test", "prompt_type": "unit"}, result={"returncode": 0})
        self.assertTrue(path.exists())
        self.assertIn("unit_test", path.read_text(encoding="utf-8"))

    def test_autonomy_report_cycle_publishes_visible_summary(self):
        result = run_autonomy_report_cycle(cycle_name="unit_report", call_llm=False, max_new_missions=1, execute_max=1)
        self.assertEqual(result["status"], "ok")
        self.assertIn("Token Gate", result["summary"])
        self.assertIn("Tokens gastos", result["summary"])
        self.assertTrue(result["report_path"].endswith(".md"))


if __name__ == "__main__":
    unittest.main()
