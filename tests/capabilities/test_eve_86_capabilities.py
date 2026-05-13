from __future__ import annotations

import inspect
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from autonomy.action_verifier import verify_autonomous_action
from autonomy.autonomy_budget import budget_allows
from autonomy.priority_engine import score_mission
from computer.action_router import perform_ui_action
from computer.state_diff import compare_states, verify_action
from computer.uia_observer import find_element
from dream.consolidation_pipeline import consolidate_diary_text
from dream.dream_evaluator import evaluate_dream
from dream.dream_synthesizer import synthesize_dream
from lab.comparison_runner import run_comparison
from lab.experiment_templates import experiment_template
from learning.error_to_test import propose_regression_test
from memory.conversation_reconstructor import find_missing_turns
from memory.learning_validator import repair_misfiled_learning, validate_target_folder
from memory.memory_conflicts import possible_conflict
from memory.memory_lifecycle import expire_memory, mark_conflict, promote_memory, register_memory
from memory.memory_quality import memory_quality_score
from memory.semantic_vector.chunker import chunk_text
from memory.semantic_vector.embedding_store import add_embedded_document, embed_text
from memory.semantic_vector.reranker import semantic_search
from memory.transcript_validator import normalize_transcript_entry, validate_transcript_chain
from personality.identity_consistency import identity_consistency_check
from personality.preference_lifecycle import update_preference
from personality.value_system import core_values
from research.applicability_judge import judge_applicability
from research.paper_reader import summarize_paper
from research.research_deduper import dedupe_research_items
from research.research_quality import score_research_item
from research.research_to_lab import research_to_lab_candidate
from security.admin_session import create_admin_session, expire_admin_session, validate_admin_session
from security.app_permissions import check_app_permission
from security.local_account import _hash_code, _safe_name, DEFAULT_ITERATIONS
from self_improvement.improvement_cycle import run_improvement_cycle
from self_improvement.arsi_cycle import run_arsi_cycle
from self_improvement.arsi_policy import arsi_change_allowed
from self_improvement.rsi_policy import classify_change_risk, rsi_change_allowed
from tools.browser_playwright import browser_dom_snapshot, click_by_role, fill_by_label


def test_01_admin_sessions_are_temporary_allowlisted_and_audited():
    session = create_admin_session("unit test", 5, ["Get-Process*"])
    assert validate_admin_session(session["session_id"], "Get-Process python")["allowed"]
    assert not validate_admin_session(session["session_id"], "Remove-Item x")["allowed"]
    assert expire_admin_session(session["session_id"])["allowed"]
    assert not validate_admin_session(session["session_id"], "Get-Process python")["allowed"]


def test_02_transcript_hash_chain_validator_detects_missing_hash():
    with tempfile.TemporaryDirectory() as tmp:
        path = __import__("pathlib").Path(tmp) / "chat.jsonl"
        first = normalize_transcript_entry({"kind": "chat", "event": "message", "payload": {"session_id": "s1", "turn_id": "t1"}})
        second = normalize_transcript_entry({"kind": "chat", "event": "message", "payload": {"session_id": "s1", "turn_id": "t2", "parent_turn_id": "t1"}}, first["hash"])
        path.write_text(__import__("json").dumps(first) + "\n" + __import__("json").dumps(second) + "\n", encoding="utf-8")
        assert validate_transcript_chain("chat", path=path)["valid"]
        path.write_text('{"kind":"chat"}\n', encoding="utf-8")
        assert not validate_transcript_chain("chat", path=path)["valid"]


def test_03_consolidation_extracts_decisions_tasks_preferences_and_contradictions():
    result = consolidate_diary_text("Decidi melhorar UIA\nTarefa fazer testes\nGosto de narrativa\nMas isto contradiz algo")
    assert result["decisions"] and result["tasks"] and result["preferences"] and result["contradictions"]


def test_04_memory_lifecycle_promotes_expires_and_marks_conflicts():
    a = register_memory("Sandro gosta de anime", source="unit", confidence=0.8)
    b = register_memory("Sandro nao gosta de anime", source="unit", confidence=0.8)
    assert promote_memory(a["id"])["layer"] == "medium_term"
    assert mark_conflict(a["id"], b["id"])["conflicted"]
    assert expire_memory(b["id"])["status"] == "archived"


def test_05_semantic_memory_chunks_embeds_and_reranks():
    chunks = chunk_text("agentes com memoria " * 200, max_tokens=50, overlap=10)
    assert len(chunks) > 1
    assert len(embed_text("memoria semantica")) >= 64
    add_embedded_document("unit-semantic", "Eve usa embeddings para encontrar conceitos de memoria viva.", {"importance": 1.0, "recency": 1.0})
    assert semantic_search("conceitos memoria", limit=1)


def test_06_dreams_join_multiple_sources_and_score_quality():
    dream = synthesize_dream({"diary": ["memoria agentes"], "errors": ["erro memoria"], "research": ["paper agentes"]})
    score = evaluate_dream(dream)
    assert dream["new_connections"]
    assert score["confidence_score"] > 0


def test_07_awareness_state_diff_verifies_expected_change():
    before = {"active_window": "A", "browser": {"url": "x"}}
    after = {"active_window": "B", "browser": {"url": "x"}}
    assert compare_states(before, after)["changed"]
    assert verify_action(before, after, {"active_window": "B"})["verified"]


def test_08_personality_preferences_mature_and_detect_identity_conflict():
    topic = f"unit taste {datetime.now().timestamp()}"
    assert update_preference(topic, "first", source="unit")["status"] == "candidate"
    assert update_preference(topic, "second", source="unit")["status"] == "reinforced"
    assert update_preference(topic, "third", source="unit")["status"] == "stable"
    assert "honestidade" in core_values()
    assert not identity_consistency_check("vou fingir gosto")["consistent"]


def test_09_lab_experiments_require_metrics_and_thresholds():
    template = experiment_template("ui_action", "UIA improves verification")
    assert template["metric"] == "ui_action_score"
    result = run_comparison(lambda: 0.5, lambda: 0.7, threshold=0.1)
    assert result["accepted"]


def test_10_error_learning_clusters_into_regression_test_proposal():
    proposal = propose_regression_test("FileNotFoundError: missing config.json")
    assert proposal["root_cause"] == "missing file or wrong path"
    assert proposal["test_name"].startswith("test_prevent_error_")


def test_11_research_is_ranked_deduped_and_paper_summarized():
    items = dedupe_research_items([{"title": "Agent Memory", "url": "https://openai.com/a"}, {"title": "Agent Memory", "url": "https://openai.com/b"}])
    assert len(items) == 1
    scored = score_research_item({"title": "New agent memory benchmark", "url": "https://openai.com/research", "summary": "code and benchmark"})
    assert scored["source_quality"] >= 0.8
    assert summarize_paper("Computer Use", "We propose an agent method with benchmark results.")["applicability_to_eve"] == "high"


def test_12_research_to_lab_requires_testable_applicability():
    item = score_research_item({"title": "Agent UI benchmark", "summary": "code benchmark for browser agents"})
    judgment = judge_applicability(item)
    candidate = research_to_lab_candidate(item)
    assert judgment["decision"] == "test_in_lab"
    assert candidate["metric"] == "capability_delta"


def test_13_learning_taxonomy_prevents_world_technology_personality_mixing():
    assert validate_target_folder("OpenAI publicou novo modelo agent", "technology")["valid"]
    repaired = repair_misfiled_learning([{"text": "Gosto de narrativa procedural", "target": "world"}])
    assert repaired[0]["misfiled"]
    assert repaired[0]["suggested_target"] == "personality"


def test_14_improvement_cycle_requires_tests_and_policy():
    candidate = {"files_changed": ["docs/example.md"], "tests_required": ["test_docs"], "baseline_metric": 0.5, "new_metric": 0.6}
    assert run_improvement_cycle(candidate)["applied"]
    risky = {"files_changed": ["security/admin_gate.py"], "tests_required": ["test_security"], "baseline_metric": 0.5, "new_metric": 0.6}
    assert not run_improvement_cycle(risky)["applied"]


def test_15_computer_use_prefers_structured_permissions_and_blocks_sensitive_actions():
    assert browser_dom_snapshot()["engine"] == "playwright"
    assert not click_by_role("button", "Save")["ok"]
    assert not fill_by_label("Email", "x")["ok"]
    tree = {"name": "Root", "control_type": "Window", "element_id": "root", "children": [{"name": "Save", "control_type": "Button", "element_id": "save"}]}
    assert find_element(name="Save", control_type="Button", tree=tree)["found"]
    assert not check_app_permission("chrome.exe", "click", selector={"name": "submit payment"})["allowed"]
    assert perform_ui_action("notepad.exe", "type", {"name": "Editor", "control_type": "Edit"}, text="hello", uia_tree={"name": "Root", "control_type": "Window", "children": [{"name": "Editor", "control_type": "Edit"}]})["ok"]


def test_16_rsi_policy_allows_safe_and_blocks_high_risk_without_approval():
    assert classify_change_risk(["docs/a.md"]) == "safe"
    assert rsi_change_allowed(["docs/a.md"])["allowed"]
    assert classify_change_risk(["security/admin_gate.py"]) == "high"
    assert not rsi_change_allowed(["security/admin_gate.py"])["allowed"]
    assert arsi_change_allowed(["docs/a.md"])["framework"] == "ARSI"
    assert run_arsi_cycle({"files_changed": ["docs/a.md"], "tests_required": ["runtime"], "baseline_metric": 0.1, "new_metric": 0.2})["applied"]


def test_17_autonomy_has_priority_budget_and_verification():
    assert score_mission(importance=1, urgency=0.5, risk=0.1, user_value=1, system_value=0.8, confidence=0.9)["score"] > 0.7
    assert budget_allows("actions_per_hour", 0)["allowed"]
    assert verify_autonomous_action({"ok": True}, {"ok": True})["verified"]


def test_memory_quality_and_conflict_helpers_cover_capability_edges():
    conflict = possible_conflict("Sandro gosta de anime", "Sandro nao gosta de anime")
    assert conflict["conflict"]
    quality = memory_quality_score({"id": "x", "source": "unit", "confidence": 0.8, "created_at": "now", "layer": "long_term"})
    assert quality["score"] >= 0.8


def test_portable_launch_files_do_not_pin_sandro_drive_letters():
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "eve.ps1",
        root / "requirements.txt",
        root / "config" / "browser.json",
        *sorted((root / "scripts").glob("*.cmd")),
        *sorted((root / "scripts").glob("*.ps1")),
    ]
    needles = ["D:\\Eve", "D:/Eve", "E:\\eve", "E:/eve"]
    offenders = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        offenders.extend(f"{path.relative_to(root)}:{needle}" for needle in needles if needle in text)
    assert offenders == []


def test_local_account_hashing_and_profile_names_are_portable():
    salt = b"unit-test-salt-16"
    assert _hash_code("172099", salt, DEFAULT_ITERATIONS) == _hash_code("172099", salt, DEFAULT_ITERATIONS)
    assert _hash_code("172099", salt, DEFAULT_ITERATIONS) != _hash_code("bad", salt, DEFAULT_ITERATIONS)
    assert _safe_name("PC 1") == "pc_1"
    assert _safe_name("Eve Local") == "eve_local"


def test_missing_turn_detector_has_clean_empty_result():
    assert "missing" in find_missing_turns()


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(func):
            suite.addTest(unittest.FunctionTestCase(func))
    return suite
