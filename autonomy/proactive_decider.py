from __future__ import annotations

from memory.errors.error_memory import recent_errors
from autonomy.scheduler import list_scheduled_tasks


def propose_low_risk_actions() -> list[str]:
    proposals = []
    if recent_errors(limit=3):
        proposals.append("resumir erros recentes e criar licoes adaptativas")
    if not list_scheduled_tasks():
        proposals.append("criar agenda local para consolidacao, sonho e pesquisa tecnologica")
    proposals.append("manter diario e estado vivo atualizados")
    return proposals
