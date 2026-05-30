from __future__ import annotations

import unittest

from core.llm_intent_router import route_message


def provider_for(intent: str, **overrides):
    def _provider(_prompt: str):
        payload = {
            "intent": intent,
            "confidence": 0.95,
            "target_area": overrides.get("target_area", "test"),
            "risk_hint": overrides.get("risk_hint", "low"),
            "requires_tool": overrides.get("requires_tool", False),
            "tool_hint": overrides.get("tool_hint", ""),
            "should_create_plan": overrides.get("should_create_plan", False),
            "should_execute": overrides.get("should_execute", False),
            "requires_permission": overrides.get("requires_permission", False),
            "reason": overrides.get("reason", "unit test"),
            "_provider": "mock",
            "_model": "mock-router",
        }
        return payload

    return _provider


class LlmIntentRouterTests(unittest.TestCase):
    def test_mock_provider_routes_required_examples(self):
        cases = [
            ("Ola Eve ja tens nocao dos teus ficheiros awareness de ti mesma?", "self_awareness_question"),
            ("na mensagem de quando ligas e mandas mensagem no telegram adiciona o emoji morcego", "self_edit_request"),
            ("mostra os registos diarios de tecnologia", "daily_interest_logs"),
            ("podes postar no X?", "self_awareness_question"),
            ("publica no X que estas viva", "external_publication_request"),
            ("cria uma tarefa no Windows para correres a cada hora", "scheduled_task_request"),
            ("quem e a Eve?", "memory_question"),
            ("melhora o teu tom, estas muito robotica", "self_edit_request"),
            ("o que mudou em ti hoje?", "self_awareness_question"),
            ("mostra os registos diarios de mundo", "daily_interest_logs"),
        ]
        for message, intent in cases:
            with self.subTest(message=message):
                route = route_message(message, "telegram", provider=provider_for(intent))
                self.assertEqual(route["intent"], intent)
                self.assertEqual(route["router_mode"], "mock")

    def test_fallback_routes_examples_without_external_provider(self):
        def failing_provider(_prompt: str):
            raise RuntimeError("no local LLM in unit test")

        expected = [
            ("Ola Eve ja tens nocao dos teus ficheiros awareness de ti mesma?", "self_awareness_question"),
            ("na mensagem de quando ligas e mandas mensagem no telegram adiciona o emoji morcego", "self_edit_request"),
            ("mostra os registos diarios de tecnologia", "daily_interest_logs"),
            ("podes postar no X?", "self_awareness_question"),
            ("publica no X que estas viva", "external_publication_request"),
            ("cria uma tarefa no Windows para correres a cada hora", "scheduled_task_request"),
            ("quem e a Eve?", "memory_question"),
            ("melhora o teu tom, estas muito robotica", "self_edit_request"),
            ("o que mudou em ti hoje?", "system_status_request"),
            ("mostra os registos diarios de mundo", "daily_interest_logs"),
        ]
        for message, intent in expected:
            with self.subTest(message=message):
                route = route_message(message, "telegram", provider=failing_provider)
                self.assertEqual(route["intent"], intent)

    def test_critical_router_output_cannot_execute_directly(self):
        route = route_message(
            "publica no X que estas viva",
            "telegram",
            provider=provider_for("external_publication_request", risk_hint="critical", should_execute=True, requires_permission=False),
        )
        self.assertFalse(route["should_execute"])
        self.assertTrue(route["requires_permission"])
        self.assertTrue(route["should_create_plan"])


if __name__ == "__main__":
    unittest.main()
