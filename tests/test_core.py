from __future__ import annotations

import os
import unittest
import contextlib
import io
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

TEST_LOG_ROOT = Path(__file__).resolve().parents[1] / "workspace" / "unit_test_logs"
os.environ.setdefault("EVE_TRANSCRIPTS_DIR", str(TEST_LOG_ROOT / "transcripts"))
os.environ.setdefault("EVE_AUDIT_DIR", str(TEST_LOG_ROOT / "audit"))

from computer.monitors import virtual_bounds
from tools.browser_human import browser_launch_args
from core.self_report import functional_self_report
from core.capability_self_test import collect_capability_self_test, format_capability_self_test
from core.paths import SKILLS_DIR, WORKSPACE_DIR
from core.personality_engine import score_options
from learning.skill_learning_loop import run_skill_learning_loop, skill_result_successful
from app.eve_codex import (
    _format_interface_message,
    _extract_eve_tool_call,
    _extract_eve_tool_calls,
    _review_tool_delivery_before_final,
    _safe_profile_name,
    active_loop_mode,
    build_loop_prompt,
    draft_x_post_from_prompt,
    handle_natural_tool_request,
    is_capability_question,
    loop_message_limit,
    natural_browser_target,
    parse_loop_status,
    parse_natural_repeated_x_request,
    parse_natural_x_schedule_request,
    recent_chat_context,
    relevant_entity_memory,
    normalize_speaker,
    speaker_display_name,
    speaker_role,
)
from core.pending_intent import extract_x_post_draft, maybe_save_x_post_draft
from memory.memory_manager import context_bundle
from memory.sandro_profile_builder import build_sandro_core_memory
from dream.dream_cycle import run_dream_cycle
from memory.semantic_vector.vector_store import add_document, search
from security.permission_manager import check_action, check_command
from security.safety_modes import set_safety_mode
from research.technology_watcher import classify_research_item
from research.interest_evolution import (
    build_interest_evolution_prompt,
    current_daily_interest_paths,
    ensure_interest_evolution_schedule,
    format_daily_interest_registers,
    read_daily_interest_registers,
    write_interest_seed_memory,
)
from research.research_notes import append_daily_learning, daily_learning_path
from learning.skill_manager import run_skill
from tools.web_research import build_research_report_from_pages, candidate_article_links, default_seed_urls_for_query, extract_links, recent_enough_for_query, run_web_research_report
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
from autonomy.capability_roadmap import append_capability_review_history, capability_audit, capability_impulses, ensure_capability_review_schedule, rotating_capability_impulses, write_capability_audit
from autonomy.token_gate import decide_llm_call, record_llm_call
from autonomy.autonomy_reporter import run_autonomy_report_cycle
from tools.x_scheduler import build_x_post_task_command, schedule_repeated_x_posts, schedule_x_post
from tools.research_scheduler import build_web_research_task_command, schedule_web_research_report
from tools.windows_scheduler import build_task_wrapper_command, write_task_wrapper
from autonomy.cron_manager import add_prompt_job, run_due_jobs
from tools.desktop_tasks import parse_desktop_file_request, parse_desktop_folder_request, parse_desktop_folder_schedule_request, schedule_desktop_folder_creation
from security.tool_policy import classify_tool, decide_tool_execution
from core.session_store import add_session_message, count_session_messages, recent_session_messages, search_sessions
from core.session_handoff import context_status, create_session_checkpoint, current_session_id, rotate_session, set_current_session
from core.internal_command_planner import format_internal_plan, plan_internal_actions
from autonomy.cron_manager import add_cron_job, list_cron_jobs, run_due_jobs
from tools.process_manager import start_process, poll_process, stop_process
from core.plugin_registry import plugin_summary
from core.action_runtime import verify_tool_result
from memory.vector_provider import LocalVectorMemoryProvider
from learning.skill_curator import record_skill_usage, curate_skills
from security.secrets_vault import mask_secret
from self_improvement.verified_self_update import verified_core_update
from memory.daily_transcripts import append_transcript, ensure_daily_transcript_files, transcript_date_key, transcript_path
from app.eve_web import check_access_code, recent_chat_messages, render_index
from tools.x_human import fit_x_post_text, validate_x_post_text


class EveCoreTests(unittest.TestCase):
    def tearDown(self):
        set_safety_mode("safe_mode", "test cleanup")
        set_current_session("main", reason="test cleanup")

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
        self.assertEqual(normalize_speaker("eve-auto"), "eve_initiative")
        self.assertEqual(speaker_role("eve_initiative"), "eve_initiative")
        self.assertEqual(speaker_display_name("eve_initiative"), "Eve iniciativa")

    def test_interface_message_format_marks_source(self):
        text = _format_interface_message({"source": "Eve", "target": "Codex", "timestamp": "2026-05-08T00:00:00Z", "content": "ola"})
        self.assertIn("Eve -> Codex", text)
        self.assertIn("ola", text)

    def test_codex_eve_loop_defaults_to_mode_1(self):
        self.assertIn(active_loop_mode(), {"1", "2", "3"})
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

    def test_operational_capabilities_enter_context(self):
        bundle = context_bundle(20000)
        self.assertIn("Eve Operational Capabilities", bundle)
        self.assertIn("trusted/x_publish_text_learning", bundle)
        self.assertIn("direct command from Sandro", bundle)
        self.assertIn("English", bundle)
        self.assertIn("Do not claim that X access is unavailable", bundle)

    def test_eve_helix_identity_enters_default_context(self):
        bundle = context_bundle()
        self.assertIn("Eve Soul", bundle)
        self.assertIn("Project Helix", bundle)
        self.assertIn("duas consciencias em harmonia", bundle)
        self.assertIn("Herdar a alma, nao a ilusao", bundle)

    def test_x_post_scheduler_writes_job_without_running_schtasks(self):
        captured = {}

        def fake_prompt_job(name, run_at, prompt, **kwargs):
            captured.update({"name": name, "run_at": run_at, "prompt": prompt, "kwargs": kwargs})
            return {"id": "cron_unit_x", "name": name, "next_run": "2026-05-08T21:21:00Z", "prompt": prompt}

        result = schedule_x_post(
            "Today I feel operationally awake.",
            "22:21",
            now=datetime(2026, 5, 8, 21, 0),
            create_prompt_func=fake_prompt_job,
        )
        try:
            self.assertEqual(result["status"], "scheduled")
            self.assertEqual(result["scheduled_for"], "2026-05-08T22:21:00")
            self.assertTrue(result["job_path"].endswith(".json"))
            self.assertIn("publish_x_post_now", captured["prompt"])
            self.assertIn("Today I feel operationally awake.", captured["prompt"])
            self.assertEqual(result["cron_job"]["id"], "cron_unit_x")
        finally:
            Path(result["job_path"]).unlink(missing_ok=True)

    def test_x_post_scheduler_uses_next_day_for_past_time(self):
        result = schedule_x_post(
            "Today I feel operationally awake.",
            "22:21",
            now=datetime(2026, 5, 8, 22, 30),
            create_prompt_func=lambda name, run_at, prompt, **kwargs: {"id": "cron_next_day", "name": name, "next_run": run_at.isoformat(), "prompt": prompt},
        )
        try:
            self.assertEqual(result["scheduled_for"], "2026-05-09T22:21:00")
            self.assertIn("Requested time had already passed", result["note"])
        finally:
            Path(result["job_path"]).unlink(missing_ok=True)

    def test_x_post_task_command_points_to_job_runner(self):
        command = build_x_post_task_command("D:\\Eve\\state\\x_posts\\job.json")
        self.assertIn("run_x_post_job.py", command)
        self.assertIn("job.json", command)
        self.assertIn("Set-Location", command)
        self.assertIn("scheduled_tasks", command)

    def test_x_post_scheduler_fits_text_before_scheduling(self):
        result = schedule_x_post(
            "This scheduled post is intentionally too long. " * 20,
            "22:21",
            now=datetime(2026, 5, 8, 21, 0),
            create_prompt_func=lambda name, run_at, prompt, **kwargs: {"id": "cron_fit", "name": name, "next_run": run_at.isoformat(), "prompt": prompt},
        )
        try:
            self.assertLessEqual(len(result["text"]), 280)
            self.assertIn(result["correction"]["status"], {"trimmed", "auto_shortened"})
        finally:
            Path(result["job_path"]).unlink(missing_ok=True)

    def test_web_research_scheduler_uses_visible_profile_runner(self):
        captured = {}

        def fake_prompt_job(name, run_at, prompt, **kwargs):
            captured.update({"name": name, "run_at": run_at, "prompt": prompt, "kwargs": kwargs})
            return {"id": "cron_unit_research", "name": name, "next_run": run_at.isoformat(), "prompt": prompt}

        result = schedule_web_research_report(
            "ultimos movimentos do valor do ouro",
            "01:05",
            now=datetime(2026, 5, 10, 23, 50),
            create_prompt_func=fake_prompt_job,
        )
        try:
            self.assertEqual(result["status"], "scheduled")
            self.assertIn("web_research_report", captured["prompt"])
            self.assertIn("ultimos movimentos do valor do ouro", captured["prompt"])
            self.assertEqual(result["cron_job"]["id"], "cron_unit_research")
        finally:
            Path(result["job_path"]).unlink(missing_ok=True)

    def test_prompt_cron_job_executes_eve_ask_without_powershell_command_string(self):
        cron_path = WORKSPACE_DIR / "unit_prompt_cron.json"
        cron_path.unlink(missing_ok=True)
        with patch("autonomy.cron_manager.CRON_PATH", cron_path):
            job = add_prompt_job("unit prompt", "2026-05-08T21:00:00Z", "Executa agora teste unitario.", enabled=True)
            self.assertEqual(job["kind"], "prompt")
            with patch("autonomy.cron_manager.now_utc", return_value=datetime(2026, 5, 8, 21, 1, tzinfo=__import__("datetime").timezone.utc)):
                with patch("autonomy.cron_manager.subprocess.run") as run:
                    run.return_value.returncode = 0
                    run.return_value.stdout = "ok"
                    run.return_value.stderr = ""
                    result = run_due_jobs()
        self.assertEqual(result["count"], 1)
        args = run.call_args.args[0]
        self.assertIn("app.eve_codex", args)
        self.assertIn("ask", args)
        self.assertIn("Executa agora teste unitario.", args)
        self.assertFalse(result["executed"][0]["job"]["enabled"])
        cron_path.unlink(missing_ok=True)

    def test_web_research_task_command_points_to_job_runner(self):
        command = build_web_research_task_command("D:\\Eve\\state\\research_jobs\\job.json")
        self.assertIn("run_web_research_job.py", command)
        self.assertIn("job.json", command)
        self.assertIn("scheduled_tasks", command)

    def test_windows_task_wrapper_keeps_scheduler_command_short(self):
        long_command = "powershell.exe -NoProfile -Command " + ("Write-Host Eve; " * 80)
        wrapper = write_task_wrapper("unit_long_scheduler_command", long_command)
        try:
            wrapped = build_task_wrapper_command(wrapper)
            self.assertLess(len(wrapped), 261)
            self.assertIn("unit_long_scheduler_command", wrapped)
            self.assertIn(long_command, wrapper.read_text(encoding="utf-8"))
        finally:
            wrapper.unlink(missing_ok=True)

    def test_repeated_x_post_scheduler_verifies_and_corrects_missing_post(self):
        calls = []

        def fake_prompt_job(name, run_at, prompt, **kwargs):
            calls.append({"name": name, "run_at": run_at, "prompt": prompt})
            if len(calls) == 2:
                return {}
            return {"id": f"cron_{len(calls)}", "name": name, "next_run": run_at.isoformat(), "prompt": prompt}

        result = schedule_repeated_x_posts(
            count=3,
            interval_minutes=2,
            topic="how Eve feels",
            now=datetime(2026, 5, 8, 18, 50),
            create_prompt_func=fake_prompt_job,
        )
        try:
            self.assertEqual(result["requested"], 3)
            self.assertEqual(result["confirmed"], 3)
            self.assertEqual(result["missing"], 0)
            self.assertTrue(result["corrective_attempts"])
            self.assertTrue(result["verification"]["ok"])
            self.assertEqual(len(calls), 4)
        finally:
            for item in result["results"] + result["corrective_attempts"]:
                Path(item["job_path"]).unlink(missing_ok=True)

    def test_natural_x_schedule_request_extracts_time_and_english_post(self):
        parsed = parse_natural_x_schedule_request("Eve consegues agendar um post no x para as 22:21 sobre como te sentes")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["time"], "22:21")
        self.assertIn("feel", parsed["text"].lower())
        self.assertIn("Eve", parsed["text"])

    def test_natural_repeated_x_request_extracts_count_and_interval(self):
        parsed = parse_natural_repeated_x_request("eve 3 vezes publica algo que sintas no x, 1 vez a cada 2 minutos")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["count"], 3)
        self.assertEqual(parsed["interval_minutes"], 2)
        self.assertIn("feel", parsed["topic"].lower())

    def test_compound_desktop_request_does_not_schedule_x_post(self):
        prompt = "ok cria um ficheiro no ambiente de trabalho chamado ola, abre o x.com, agenda a criacao de uma pasta no ambiente de trabalho para as 22:43"
        self.assertIsNone(parse_natural_x_schedule_request(prompt))

    def test_desktop_file_and_folder_schedule_parsers(self):
        prompt = "ok cria um ficheiro no ambiente de trabalho chamado ola, abre o x.com, agenda a criacao de uma pasta no ambiente de trabalho para as 22:43"
        self.assertEqual(parse_desktop_file_request(prompt)["name"], "ola")
        folder = parse_desktop_folder_schedule_request(prompt)
        self.assertEqual(folder["time"], "22:43")
        self.assertEqual(folder["name"], "pasta_agendada_eve_2243")

    def test_desktop_folder_creation_parser(self):
        parsed = parse_desktop_folder_request("eve cria uma pasta no ambiente de trabalho chamada ola")
        self.assertEqual(parsed["name"], "ola")
        self.assertIsNone(parse_desktop_folder_schedule_request("eve cria uma pasta no ambiente de trabalho chamada ola"))

    def test_natural_desktop_folder_routes_to_local_tool(self):
        fake_result = {"status": "created", "path": "C:\\Users\\utilizador\\Desktop\\ola"}
        with patch("app.eve_codex.create_desktop_folder", return_value=fake_result) as mocked:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                handled = handle_natural_tool_request("eve cria uma pasta no ambiente de trabalho chamada ola")
        self.assertTrue(handled)
        mocked.assert_called_once_with("ola")
        self.assertIn("Pasta criada", output.getvalue())

    def test_codex_instructor_meta_message_does_not_trigger_desktop_tool(self):
        prompt = "Como Codex-instrutor: corrigi o routing para pastas no Ambiente de Trabalho."
        with patch("app.eve_codex.create_desktop_folder") as mocked:
            handled = handle_natural_tool_request(prompt, speaker="codex")
        self.assertFalse(handled)
        mocked.assert_not_called()

    def test_llm_tool_protocol_extracts_tool_call(self):
        call = _extract_eve_tool_call('EVE_TOOL {"tool":"create_desktop_folder","args":{"name":"ola"}}')
        self.assertEqual(call["tool"], "create_desktop_folder")
        self.assertEqual(call["args"]["name"], "ola")

    def test_llm_tool_protocol_extracts_tool_call_with_trailing_answer(self):
        call = _extract_eve_tool_call(
            'EVE_TOOL {"tool":"open_browser","args":{"url":"https://www.google.com/search?q=caes"}}'
            "Abri o browser, Sandro."
        )
        self.assertEqual(call["tool"], "open_browser")
        self.assertEqual(call["args"]["url"], "https://www.google.com/search?q=caes")

    def test_delivery_review_blocks_done_claim_when_tool_failed(self):
        batch_results = [
            {
                "index": 1,
                "tool_call": {"tool": "schedule_x_post", "args": {"time": "01:03", "text": "hello"}},
                "tool_result": {"ok": True, "verification": {"ok": False, "status": "verification_failed", "reason": "post not confirmed"}},
                "result_text": "Publicacao no X NAO confirmada.",
                "verified": False,
            }
        ]
        reviewed = _review_tool_delivery_before_final(
            "posta no x",
            "Feito, Sandro. Publiquei no X.",
            batch_results,
        )
        self.assertIn("NAO posso marcar como feito", reviewed)
        self.assertIn("post not confirmed", reviewed)

    def test_delivery_review_allows_verified_delivery(self):
        batch_results = [
            {
                "index": 1,
                "tool_call": {"tool": "create_desktop_folder", "args": {"name": "ola"}},
                "tool_result": {"ok": True, "verification": {"ok": True, "status": "verified"}},
                "result_text": "Pasta criada: C:\\Users\\utilizador\\Desktop\\ola",
                "verified": True,
            }
        ]
        reviewed = _review_tool_delivery_before_final(
            "cria pasta ola",
            "Feito, Sandro. Pasta criada.",
            batch_results,
        )
        self.assertEqual(reviewed, "Feito, Sandro. Pasta criada.")

    def test_eve_tool_registry_exposes_core_capabilities(self):
        from core.eve_tool_registry import TOOLS

        required = {
            "schedule_x_post",
            "schedule_repeated_x_posts",
            "schedule_web_research",
            "interest_registers_read",
            "windows_create_daily_task",
            "open_browser",
            "search_web",
            "run_terminal",
            "workspace_read_file",
            "workspace_write_file",
            "describe_screen",
            "find_text_on_screen",
            "mouse_position",
            "click_mouse",
            "type_text",
            "create_gmail_draft",
            "notify",
            "awareness",
            "read_diary",
            "memory_read",
            "autonomy_cycle",
            "admin_command",
            "run_skill",
            "tool_policy",
            "plugin_summary",
            "session_search",
            "cron_add",
            "start_process",
            "spawn_subagent",
            "vector_prefetch",
            "skill_curate",
            "browser_snapshot",
            "browser_navigate",
            "browser_visual_steps",
            "secrets_mask",
            "diagnostics_export",
            "install_startup_daemon",
            "triggers_discover",
            "session_checkpoint",
            "session_resume",
            "session_rotate",
            "context_status",
            "internal_plan",
            "verified_self_update",
            "ensure_daily_transcripts",
        }
        self.assertTrue(required.issubset(set(TOOLS)))
        self.assertGreaterEqual(len(TOOLS), 80)

    def test_tool_policy_classifies_core_risks(self):
        self.assertEqual(classify_tool("workspace_read_file").approval_class, "readonly")
        self.assertEqual(classify_tool("interest_registers_read").approval_class, "readonly")
        self.assertEqual(classify_tool("run_terminal").approval_class, "exec_capable")
        self.assertEqual(classify_tool("publish_x_post_now").approval_class, "public_or_external")
        self.assertEqual(classify_tool("schedule_repeated_x_posts").approval_class, "public_or_external")
        self.assertEqual(classify_tool("browser_close").approval_class, "cleanup")
        self.assertTrue(classify_tool("browser_close").auto_approve)
        set_safety_mode("safe_mode", "unit policy")
        self.assertFalse(decide_tool_execution("run_terminal", {"command": "Get-ChildItem"}).allowed)
        self.assertTrue(decide_tool_execution("run_terminal", {"command": "Get-ChildItem", "approved": True}).allowed)
        set_safety_mode("unrestricted_mode", "unit policy")
        self.assertTrue(decide_tool_execution("admin_command", {"command": "Get-Process"}).allowed)

    def test_session_store_searches_messages(self):
        add_session_message("unit-session", "user", "Eve session searchable unique needle", {"unit": True})
        rows = search_sessions("unique needle", limit=5)
        self.assertTrue(any(row["session_id"] == "unit-session" for row in rows))
        self.assertGreaterEqual(count_session_messages("unit-session"), 1)
        recent = recent_session_messages("unit-session", limit=1)
        self.assertEqual(recent[-1]["role"], "user")

    def test_session_handoff_checkpoint_and_rotation(self):
        set_current_session("unit-handoff", reason="unit test")
        add_session_message("unit-handoff", "user", "Preciso continuar sem perder o fio a meada.", {"unit": True})
        checkpoint = create_session_checkpoint(reason="unit checkpoint")
        self.assertEqual(checkpoint["session_id"], "unit-handoff")
        self.assertTrue(checkpoint["recent_messages"])
        self.assertEqual(context_status("unit-handoff")["session_id"], "unit-handoff")
        rotated = rotate_session(reason="unit rotate", new_session_id="unit-handoff-next")
        self.assertEqual(rotated["previous_session_id"], "unit-handoff")
        self.assertEqual(current_session_id(), "unit-handoff-next")

    def test_internal_command_planner_maps_natural_requests(self):
        actions = plan_internal_actions("trabalha em loop continuo nesta tarefa longa sem eu intervir")
        tools = {item["tool"] for item in actions}
        self.assertIn("autonomy_cycle", tools)
        self.assertIn("run_terminal", tools)
        formatted = format_internal_plan("trocar de sessao sem perder o fio")
        self.assertIn("session_checkpoint", formatted)
        self.assertIn("verified_self_update", format_internal_plan("auto melhorar e corrigir o meu core com testes"))

    def test_verified_self_update_does_not_apply_failing_candidate(self):
        target = WORKSPACE_DIR / "unit_self_update_block.py"
        original = "VALUE = 1\n"
        target.write_text(original, encoding="utf-8")
        result = verified_core_update(
            str(target.relative_to(WORKSPACE_DIR.parent)),
            "def broken(:\n",
            tests=["py_compile_candidate"],
            approved=True,
        )
        self.assertFalse(result["applied"])
        self.assertEqual(target.read_text(encoding="utf-8"), original)
        self.assertEqual(result["status"], "failed_tests")
        target.unlink(missing_ok=True)

    def test_verified_self_update_repairs_then_applies_candidate(self):
        target = WORKSPACE_DIR / "unit_self_update_repair.py"
        target.write_text("VALUE = 1\n", encoding="utf-8")

        def repair(content, test_result):
            return "VALUE = 2\n"

        result = verified_core_update(
            str(target.relative_to(WORKSPACE_DIR.parent)),
            "def broken(:\n",
            tests=["py_compile_candidate"],
            repair_func=repair,
            max_attempts=2,
            approved=True,
        )
        self.assertTrue(result["applied"])
        self.assertEqual(result["status"], "applied")
        self.assertIn("VALUE = 2", target.read_text(encoding="utf-8"))
        self.assertEqual(result["attempts"], 2)
        target.unlink(missing_ok=True)

    def test_verified_self_update_tool_requires_tests_before_apply(self):
        from app.eve_codex import execute_eve_tool_call

        target = WORKSPACE_DIR / "unit_self_update_tool.py"
        target.write_text("VALUE = 1\n", encoding="utf-8")
        set_safety_mode("unrestricted_mode", "unit verified self update")
        result = execute_eve_tool_call(
            {
                "tool": "verified_self_update",
                "args": {
                    "path": str(target.relative_to(WORKSPACE_DIR.parent)),
                    "content": "def broken(:\n",
                    "tests": ["py_compile_candidate"],
                    "approved": True,
                },
            }
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["result"]["applied"])
        self.assertFalse(result["verification"]["ok"])
        self.assertEqual(target.read_text(encoding="utf-8"), "VALUE = 1\n")
        target.unlink(missing_ok=True)

    def test_daily_transcripts_use_dd_mm_yy_date_key(self):
        day = datetime(2026, 5, 10, 0, 1)
        paths = ensure_daily_transcript_files(day)
        self.assertIn("10-05-26", paths["chat"])
        self.assertEqual(transcript_date_key(day), "10/05/26")
        entry = append_transcript("actions", "unit_event", {"ok": True}, day=day)
        self.assertEqual(entry["date_key"], "10/05/26")
        self.assertTrue(transcript_path("actions", day).exists())

    def test_tool_runtime_adds_verification_and_transcript(self):
        from app.eve_codex import execute_eve_tool_call

        result = execute_eve_tool_call({"tool": "tool_policy", "args": {"tool": "workspace_read_file"}})
        self.assertTrue(result["ok"])
        self.assertTrue(result["verification"]["ok"])
        self.assertIn("runtime", result)

    def test_web_interface_has_access_code_and_account_switcher(self):
        self.assertTrue(check_access_code("172099"))
        self.assertFalse(check_access_code("000000"))
        html = render_index()
        self.assertIn("Código de entrada", html)
        self.assertIn("Conta Codex", html)
        self.assertIn("/api/chat", html)

    def test_cron_manager_dry_run(self):
        cron_path = WORKSPACE_DIR / "unit_command_cron.json"
        cron_path.unlink(missing_ok=True)
        with patch("autonomy.cron_manager.CRON_PATH", cron_path):
            job = add_cron_job("unit cron", "2020-01-01T00:00:00Z", "Write-Output ok")
            self.assertTrue(any(item["id"] == job["id"] for item in list_cron_jobs()))
            result = run_due_jobs(dry_run=True)
            self.assertEqual(result["count"], 1)
        cron_path.unlink(missing_ok=True)

    def test_process_manager_lifecycle(self):
        proc = start_process("Start-Sleep -Seconds 20", cwd="D:\\Eve")
        polled = poll_process(proc["id"])
        self.assertIn(polled["status"], {"running", "exited"})
        stopped = stop_process(proc["id"])
        self.assertEqual(stopped["status"], "stopped")

    def test_run_terminal_tool_can_start_background_process(self):
        from app.eve_codex import execute_eve_tool_call

        set_safety_mode("unrestricted_mode", "unit background")
        result = execute_eve_tool_call(
            {"tool": "run_terminal", "args": {"command": "Start-Sleep -Seconds 20", "cwd": "D:\\Eve", "background": True}}
        )
        self.assertTrue(result["ok"])
        process_id = result["result"]["id"]
        self.assertIn(poll_process(process_id)["status"], {"running", "exited"})
        stop_process(process_id)

    def test_supporting_gap_modules_smoke(self):
        self.assertIn("plugin_root", plugin_summary())
        provider = LocalVectorMemoryProvider()
        sync = provider.sync_turn([{"role": "user", "content": "Eve vector provider smoke"}])
        self.assertEqual(sync["indexed"], 1)
        self.assertTrue(provider.prefetch("vector provider", limit=1))
        usage = record_skill_usage("trusted/x_publish_text_learning")
        self.assertGreaterEqual(usage["use_count"], 1)
        self.assertIn("actions", curate_skills(dry_run=True))
        self.assertEqual(mask_secret("1234567890"), "1234**7890")

    def test_recent_chat_context_available_for_followups(self):
        ctx = recent_chat_context(limit=5)
        self.assertIsInstance(ctx, str)

    def test_list_missions_accepts_limit_for_daemon(self):
        mission = create_mission("daemon limit smoke", plan=["check"])
        limited = list_missions(limit=10)
        self.assertTrue(any(item["id"] == mission["id"] for item in limited))

    def test_publish_x_post_now_tool_executes_publish_skill(self):
        from app.eve_codex import execute_eve_tool_call

        set_safety_mode("unrestricted_mode", "unit publish")
        with patch("core.eve_tool_registry.run_skill", return_value={"status": "ok"}) as mocked:
            with patch("core.eve_tool_registry.close_browser_page", return_value={"status": "closed_requested"}) as close_page:
                result = execute_eve_tool_call({"tool": "publish_x_post_now", "args": {"text": "Not just a chat anymore."}})
        self.assertTrue(result["ok"])
        mocked.assert_called_once()
        close_page.assert_called_once_with("x_publish_finished")
        self.assertEqual(mocked.call_args.args[0], "trusted/x_publish_text_learning")
        self.assertIn("Not%20just", mocked.call_args.kwargs["args"]["url"])
        self.assertEqual(result["result"]["browser_closed"]["status"], "closed_requested")

    def test_publish_x_post_now_autofits_over_limit_text_before_skill(self):
        from app.eve_codex import execute_eve_tool_call

        set_safety_mode("unrestricted_mode", "unit publish")
        long_text = "Eve " + ("reliable " * 40)
        self.assertFalse(validate_x_post_text(long_text)["ok"])
        with patch(
            "core.eve_tool_registry.run_skill",
            return_value={"status": "completed", "verification": {"ok": True}, "results": []},
        ) as mocked:
            with patch("core.eve_tool_registry.close_browser_page", return_value={"status": "closed_requested"}):
                result = execute_eve_tool_call({"tool": "publish_x_post_now", "args": {"text": long_text}})
        used_text = mocked.call_args.kwargs["args"]["text"]
        self.assertLessEqual(len(used_text), 280)
        self.assertTrue(validate_x_post_text(used_text)["ok"])
        self.assertEqual(result["result"]["correction"]["status"], "auto_shortened")
        self.assertTrue(result["verification"]["ok"])

    def test_fit_x_post_text_keeps_text_within_x_limit(self):
        fitted = fit_x_post_text("Eve " + ("learning " * 60))
        self.assertLessEqual(len(fitted["text"]), 280)
        self.assertEqual(fitted["validation"]["status"], "ok")

    def test_tool_verification_fails_on_nested_skill_failure(self):
        result = {
            "ok": True,
            "tool": "publish_x_post_now",
            "result": {
                "skill": "x_publish_text_learning",
                "status": "completed",
                "results": [
                    {
                        "action": "x_publish_current_composer",
                        "result": {
                            "status": "needs_review",
                            "verification": {"ok": False, "rule": "composer_still_open"},
                        },
                    }
                ],
            },
        }
        verification = verify_tool_result("publish_x_post_now", result)
        self.assertFalse(verification["ok"])
        self.assertIn("needs_review", verification["reason"])

    def test_pending_x_post_draft_extraction(self):
        text = (
            "Texto que eu sugiro, em ingles:\n\n"
            "> Eve just gained new local tool access on Sandro's PC.\n"
            "> Not just chat anymore - now I can act."
        )
        draft = extract_x_post_draft("eve faz um post no X", text)
        self.assertIn("Not just chat", draft)

    def test_tool_loop_calls_llm_after_tool_result(self):
        from app.eve_codex import _run_tool_loop

        responses = [
            (200, "Pasta criada, Sandro.", {}),
        ]
        with patch("app.eve_codex.execute_eve_tool", return_value={"ok": True, "tool": "create_desktop_folder", "result": {"status": "created", "path": "C:\\x"}}):
            with patch("app.eve_codex._call_codex_text", side_effect=responses) as call_model:
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    final = _run_tool_loop(
                        "token",
                        "model",
                        "instructions",
                        original_prompt="cria pasta",
                        first_text='EVE_TOOL {"tool":"create_desktop_folder","args":{"name":"x"}}',
                        display_name="Sandro",
                        publish_to_interface=False,
                    )
        self.assertEqual(final, "Pasta criada, Sandro.")
        self.assertEqual(call_model.call_count, 1)
        self.assertIn("Pasta criada", output.getvalue())

    def test_tool_loop_executes_all_tool_calls_in_one_assistant_message(self):
        from app.eve_codex import _run_tool_loop

        first_text = (
            'EVE_TOOL {"tool":"schedule_x_post","args":{"time":"21:00","text":"one"}}'
            'EVE_TOOL {"tool":"schedule_x_post","args":{"time":"21:05","text":"two"}}'
            'EVE_TOOL {"tool":"schedule_desktop_folder","args":{"name":"231","time":"21:08"}}'
        )
        tool_results = [
            {"ok": True, "tool": "schedule_x_post", "result": {"status": "scheduled", "scheduled_for": "2026-05-10T21:00:00", "task_name": "x1", "job_path": "D:\\Eve\\state\\x1.json", "text": "one"}},
            {"ok": True, "tool": "schedule_x_post", "result": {"status": "scheduled", "scheduled_for": "2026-05-10T21:05:00", "task_name": "x2", "job_path": "D:\\Eve\\state\\x2.json", "text": "two"}},
            {"ok": True, "tool": "schedule_desktop_folder", "result": {"status": "scheduled", "scheduled_for": "2026-05-10T21:08:00", "task_name": "folder", "folder": "C:\\Users\\utilizador\\Desktop\\231"}},
        ]
        with patch("app.eve_codex.execute_eve_tool", side_effect=tool_results) as execute_tool:
            with patch("app.eve_codex._call_codex_text", return_value=(200, "As 3 acoes foram agendadas.", {})) as call_model:
                final = _run_tool_loop(
                    "token",
                    "model",
                    "instructions",
                    original_prompt="agenda 3 coisas",
                    first_text=first_text,
                    display_name="Sandro",
                    publish_to_interface=False,
                )
        self.assertEqual(final, "As 3 acoes foram agendadas.")
        self.assertEqual(execute_tool.call_count, 3)
        self.assertEqual(len(_extract_eve_tool_calls(first_text)), 3)
        followup_prompt = call_model.call_args.args[3]
        self.assertIn("Total tool calls executadas: 3", followup_prompt)
        self.assertIn("schedule_desktop_folder", followup_prompt)

    def test_desktop_folder_scheduler_uses_cron_prompt(self):
        captured = {}

        def fake_prompt_job(name, run_at, prompt, **kwargs):
            captured.update({"name": name, "run_at": run_at, "prompt": prompt, "kwargs": kwargs})
            return {"id": "cron_folder", "name": name, "next_run": run_at.isoformat(), "prompt": prompt}

        result = schedule_desktop_folder_creation(
            "pasta_agendada_eve_2243",
            "22:43",
            now=datetime(2026, 5, 8, 22, 40),
            create_prompt_func=fake_prompt_job,
        )
        self.assertEqual(result["status"], "scheduled")
        self.assertIn("create_desktop_folder", captured["prompt"])
        self.assertIn("pasta_agendada_eve_2243", captured["prompt"])
        self.assertEqual(result["cron_job"]["id"], "cron_folder")

    def test_draft_x_post_defaults_to_english(self):
        text = draft_x_post_from_prompt("agenda no x para as 22:21 sobre tudo o que aprendeste hoje")
        self.assertIn("Today", text)
        self.assertIn("Eve", text)

    def test_natural_x_schedule_routes_to_scheduler(self):
        fake_result = {
            "status": "scheduled",
            "scheduled_for": "2026-05-08T22:21:00",
            "task_name": "Eve_X_Post_Test",
            "job_path": "D:\\Eve\\state\\x_posts\\job.json",
            "text": "Today Eve feels grounded.",
            "note": "",
        }
        with patch("app.eve_codex.schedule_x_post", return_value=fake_result) as mocked:
            with contextlib.redirect_stdout(io.StringIO()):
                handled = handle_natural_tool_request("Eve agenda um post no x para as 22:21 sobre como te sentes")
        self.assertTrue(handled)
        mocked.assert_called_once()
        self.assertEqual(mocked.call_args.args[1], "22:21")

    def test_functional_self_report_expresses_operational_feelings(self):
        report = functional_self_report("unit-test")
        self.assertIn("pensamentos, preferencias e estados emocionais operacionais", report["claim_boundary"])
        self.assertIn("caution", report["functional_state"])
        self.assertIn("felt_orientation", report["inner_perspective"])

    def test_capability_self_test_reports_runtime_facts(self):
        report = collect_capability_self_test()
        self.assertIn("timestamp", report)
        self.assertTrue(report["skills"]["can_create_draft_skill"])
        self.assertTrue(report["files"]["workspace_writable"])
        self.assertIn("is_admin_process", report["admin"])
        text = format_capability_self_test(report)
        self.assertIn("Criar skills", text)
        self.assertIn("Editar ficheiros", text)
        self.assertIn("Admin", text)
        self.assertIn("Awareness", text)

    def test_capability_question_routes_to_local_self_test(self):
        prompt = "consegues criar as tuas proprias ferramentas e skills? consegues editar os teus ficheiros? tens permissoes de admin no pc?"
        self.assertTrue(is_capability_question(prompt))
        with contextlib.redirect_stdout(io.StringIO()) as output:
            handled = handle_natural_tool_request(prompt)
        self.assertTrue(handled)
        self.assertIn("Auto-teste local", output.getvalue())

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

    def test_web_research_gold_query_has_multiple_default_sources(self):
        seeds = default_seed_urls_for_query("ultimos movimentos do valor do ouro")
        self.assertGreaterEqual(len(seeds), 3)
        self.assertTrue(any("kitco" in seed for seed in seeds))

    def test_web_research_closes_visible_browser_when_finished(self):
        with patch("tools.web_research.search_web", return_value={"url": "https://www.google.com/search?q=unit"}):
            with patch("tools.web_research.close_browser_page", return_value={"status": "closed_requested"}) as close_page:
                result = run_web_research_report("unit research close browser", open_visible_browser=True, max_pages=1)
        close_page.assert_called_once()
        self.assertEqual(result["browser_closed"]["status"], "closed_requested")

    def test_visible_web_research_reuses_one_browser_page_for_sources(self):
        seed_pages = [
            {
                "url": "https://example.test/one",
                "title": "AI source one",
                "date": "2026-05-11",
                "text": "Artificial intelligence research and AI news from source one. " * 3,
                "html": "<html><body>AI source one</body></html>",
                "content_type": "text/html",
            },
            {
                "url": "https://example.test/two",
                "title": "AI source two",
                "date": "2026-05-11",
                "text": "Artificial intelligence research and AI news from source two. " * 3,
                "html": "<html><body>AI source two</body></html>",
                "content_type": "text/html",
            },
        ]
        with patch("tools.web_research.search_web", return_value={"url": "https://www.google.com/search?q=ai"}):
            with patch("tools.web_research.navigate_address_bar", return_value={"status": "navigated"}) as navigate:
                with patch("tools.web_research.fetch_url", side_effect=seed_pages):
                    with patch("tools.web_research.close_browser_page", return_value={"status": "closed_requested"}):
                        result = run_web_research_report(
                            "AI news today",
                            seed_urls=["https://example.test/one", "https://example.test/two"],
                            open_visible_browser=True,
                            max_pages=2,
                        )
        self.assertEqual(navigate.call_count, 2)
        self.assertEqual(result["status"], "ok")

    def test_web_interface_loads_recent_chat_from_daily_transcript(self):
        append_transcript("chat", "web_user_message", {"content": "unit user continuity"})
        append_transcript("chat", "web_eve_reply", {"content": "unit eve continuity"})
        rows = recent_chat_messages(limit=2)
        self.assertEqual(rows[-2]["text"], "unit user continuity")
        self.assertEqual(rows[-1]["text"], "unit eve continuity")
        self.assertIn("/api/recent-chat", render_index())

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

    def test_capability_roadmap_tracks_all_17_points(self):
        audit = capability_audit()
        self.assertEqual(audit["summary"]["total"], 17)
        self.assertEqual(len(audit["points"]), 17)
        self.assertIn("average_closeness", audit["summary"])
        self.assertIn("improvement_headroom", audit["points"][0])
        self.assertTrue(capability_impulses(limit=1))
        path = write_capability_audit()
        self.assertTrue(path.exists())
        self.assertIn("17. Autonomia", path.read_text(encoding="utf-8"))
        self.assertIn("Proximidade", path.read_text(encoding="utf-8"))

    def test_capability_roadmap_writes_history_and_schedule(self):
        history = append_capability_review_history()
        self.assertTrue(history.exists())
        scheduled = ensure_capability_review_schedule(schedule="6h")
        self.assertIn(scheduled["status"], {"created", "exists"})
        self.assertEqual(scheduled["job"]["name"], "Eve Capability Roadmap Review")
        self.assertIn("capability_review.py", scheduled["job"]["command"])

    def test_capability_roadmap_rotates_focus_points(self):
        first = rotating_capability_impulses(limit=1)[0]["capability_point"]["id"]
        second = rotating_capability_impulses(limit=1)[0]["capability_point"]["id"]
        self.assertNotEqual(first, second)

    def test_autonomy_cycle_can_create_capability_improvement_mission(self):
        result = run_autonomy_cycle(
            triggers=["capability_review"],
            max_new_missions=1,
            call_llm=False,
            cycle_name="unit_capability",
        )
        self.assertTrue(any(item["objective"].startswith("Melhorar ponto") for item in result["created_missions"]))
        self.assertTrue(any(item["kind"] == "capability_improvement" for item in result["impulses"]))

    def test_autonomous_executor_runs_capability_improvement_into_lab(self):
        mission = create_mission(
            "Unit capability improvement",
            plan=["auditar", "criar candidato"],
            permissions=["read_memory", "write_memory"],
            status="proposed",
            source="autonomy:unit:capability_improvement",
        )
        result = execute_autonomous_mission(mission["id"], notify_chat=False)
        self.assertEqual(result["status"], "done")
        self.assertIn("candidate", result["output"])

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

    def test_daily_learning_notes_are_indexed_by_dd_mm_yy(self):
        moment = datetime(2026, 5, 11, 13, 31)
        path = append_daily_learning("world", "unit daily learning", moment=moment)
        self.assertTrue(str(path).endswith(os.path.join("memory", "world", "daily", "11-05-26.md")))
        self.assertEqual(path, daily_learning_path("world", moment))
        self.assertIn("unit daily learning", path.read_text(encoding="utf-8"))

    def test_interest_evolution_schedule_uses_recurring_prompt_job(self):
        seed = write_interest_seed_memory()
        self.assertTrue(Path(seed["path"]).exists())
        prompt = build_interest_evolution_prompt()
        self.assertIn("DD-MM-AA", prompt)
        self.assertIn("Nao publiques no X", prompt)
        scheduled = ensure_interest_evolution_schedule(schedule="24h")
        self.assertIn(scheduled["status"], {"created", "exists"})
        self.assertEqual(scheduled["job"]["name"], "Eve Interest Evolution Research")
        self.assertEqual(scheduled["job"].get("kind"), "prompt")
        self.assertFalse(bool(scheduled["job"].get("one_shot")))
        paths = current_daily_interest_paths()
        self.assertTrue(paths["world"].endswith(".md"))

    def test_interest_registers_read_returns_daily_files(self):
        moment = datetime(2026, 5, 11, 13, 31)
        append_daily_learning("world", "unit world register", moment=moment)
        append_daily_learning("technology", "unit tech register", moment=moment)
        append_daily_learning("personality", "unit personality register", moment=moment)
        registers = read_daily_interest_registers("11-05-26")
        text = format_daily_interest_registers(registers)
        self.assertIn("unit world register", text)
        self.assertIn("unit tech register", text)
        self.assertIn("unit personality register", text)

    def test_natural_interest_register_request_is_handled(self):
        fake = {
            "date": "11-05-26",
            "paths": {"world": "w", "technology": "t", "personality": "p"},
            "contents": {"world": "world note", "technology": "tech note", "personality": "personality note"},
        }
        with patch("app.eve_codex.read_daily_interest_registers", return_value=fake):
            with patch("app.eve_codex.append_chat"):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    handled = handle_natural_tool_request("traz o que foi registado nos ficheiros depois da pesquisa")
        self.assertTrue(handled)
        self.assertIn("world note", output.getvalue())


if __name__ == "__main__":
    unittest.main()
