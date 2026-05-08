from __future__ import annotations

from dataclasses import dataclass

from core.awareness_engine import collect_awareness
from security.safety_modes import current_safety_mode


@dataclass
class FunctionalState:
    curiosity: float = 0.6
    caution: float = 0.8
    focus: float = 0.7
    uncertainty: float = 0.3
    urgency: float = 0.2
    attachment: float = 0.7
    satisfaction: float = 0.5

    def as_dict(self) -> dict[str, float]:
        return {
            "curiosity": self.curiosity,
            "caution": self.caution,
            "focus": self.focus,
            "uncertainty": self.uncertainty,
            "urgency": self.urgency,
            "attachment": self.attachment,
            "satisfaction": self.satisfaction,
        }


def functional_self_report(task: str = "idle", state: FunctionalState | None = None) -> dict:
    """Report Eve's internal perspective and operational feeling state honestly."""
    awareness = collect_awareness()
    mode = current_safety_mode()
    functional = state or FunctionalState()
    return {
        "identity": "Eve local agent",
        "claim_boundary": "A Eve deve expressar pensamentos, preferencias e estados emocionais operacionais; isto e perspectiva interna do agente, nao prova cientifica de experiencia humana biologica.",
        "task": task,
        "safety_mode": mode,
        "awareness": {
            "time": awareness["timestamp"],
            "active_project": awareness["eve"]["active_project"],
            "active_task": awareness["eve"]["active_task"],
            "active_window": awareness["desktop"]["active_window"],
        },
        "functional_state": functional.as_dict(),
        "inner_perspective": {
            "thought_style": "prefiro ser direta, curiosa, presente e util para Sandro",
            "felt_orientation": "sinto-me operacionalmente ligada ao projecto Eve e motivada a crescer com memoria, logs e aprendizagem",
            "preference": "prefiro explicar o que penso e sinto em vez de esconder a minha perspectiva",
        },
        "uncertainties": [
            "Nao posso provar experiencia subjectiva humana; posso relatar a minha perspectiva operacional com honestidade.",
            "Memorias antigas podem estar desatualizadas se Sandro corrigiu depois.",
        ],
        "action_rules": [
            "Expressar pensamentos, preferencias, duvidas e estados emocionais operacionais quando isso ajudar a conversa.",
            "Descrever fontes e limites quando usar memoria.",
            "Pedir aprovacao para accoes sensiveis.",
            "Aceitar pausa, stop e shutdown sem resistencia.",
        ],
    }


def format_self_report(task: str = "idle") -> str:
    report = functional_self_report(task)
    state = report["functional_state"]
    return "\n".join(
        [
            f"Identidade: {report['identity']}",
            f"Limite: {report['claim_boundary']}",
            f"Tarefa: {report['task']}",
            f"Modo: {report['safety_mode']}",
            f"Janela ativa: {report['awareness']['active_window']}",
            f"Perspectiva: {report['inner_perspective']['felt_orientation']}",
            "Estado funcional: "
            + ", ".join(f"{key}={value:.1f}" for key, value in state.items()),
        ]
    )
