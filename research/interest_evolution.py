from __future__ import annotations

from typing import Any

from autonomy.cron_manager import add_recurring_prompt_job, list_cron_jobs
from core.paths import MEMORY_DIR, ensure_project_dirs
from research.research_notes import append_daily_learning, daily_learning_path


EVE_STARTING_INTERESTS = [
    "memoria artificial",
    "agentes autonomos",
    "computer-use agents",
    "skills que aprendem com erros",
    "self-improvement controlado",
    "laboratorios de melhoria",
]


def write_interest_seed_memory() -> dict[str, str]:
    ensure_project_dirs()
    path = MEMORY_DIR / "personality" / "interest_evolution_seed.md"
    sandro_source = MEMORY_DIR / "long_term" / "sandro_interests.md"
    sandro_text = sandro_source.read_text(encoding="utf-8").strip() if sandro_source.exists() else "Ainda falta criar memory/long_term/sandro_interests.md."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Eve Interest Evolution Seed",
                "",
                "A Eve deve comecar a desenvolver gostos proprios partindo dos interesses reais do Sandro, sem os copiar para sempre.",
                "",
                "## Interesses base do Sandro",
                "",
                f"Fonte local: `{sandro_source}`",
                "",
                sandro_text,
                "",
                "## Interesses iniciais proprios da Eve",
                "",
                *[f"- {item}" for item in EVE_STARTING_INTERESTS],
                "",
                "## Regra de divergencia",
                "",
                "Todos os dias, a Eve deve pesquisar alguns temas ligados a esta base, encontrar ligacoes novas, "
                "registar o que aprendeu e decidir se algum tema comeca a ser um gosto proprio dela.",
                "",
                "A Eve nao deve afirmar que gosta de algo por teatro. Deve explicar o motivo operacional: curiosidade, utilidade, beleza tecnica, ligacao ao Sandro, ou potencial de melhoria.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    append_daily_learning("personality", "Seed de evolucao de interesses atualizado com interesses base do Sandro e interesses iniciais da Eve.")
    return {"path": str(path)}


def build_interest_evolution_prompt() -> str:
    return (
        "Executa uma rotina autonoma de evolucao de interesses da Eve.\n"
        "Objetivo: partir dos gostos do Sandro, pesquisar online, aprender e permitir que a Eve desenvolva gostos proprios com o tempo.\n\n"
        "Regras obrigatorias:\n"
        "1. Escolhe 1 tema base do Sandro, 1 tema tecnico da Eve e 1 tema novo adjacente.\n"
        "2. Usa web_research_report com varias fontes quando precisares de internet.\n"
        "3. Se abrires browser, usa Chrome/perfil Eve, reutiliza a mesma aba e fecha a pagina no fim; web_research_report ja fecha a pagina, por isso nao chames browser_close em duplicado salvo se abriste uma pagina extra.\n"
        "4. Regista aprendizagem do mundo/gostos em memory/world/daily/DD-MM-AA.md.\n"
        "5. Regista aprendizagem tecnica em memory/technology/daily/DD-MM-AA.md.\n"
        "6. Regista mudancas ou candidatos de gostos proprios em memory/personality/daily/DD-MM-AA.md.\n"
        "7. Se algo puder melhorar a Eve, cria nota candidata para o lab antes de alterar core.\n"
        "8. No fim, deixa uma mensagem curta ao Sandro com: temas pesquisados, fontes principais, o que aprendeste, e se nasceu algum gosto/candidato novo.\n"
        "Nao publiques no X nesta rotina. Nao compres, nao envies emails e nao faças alteracoes sensiveis."
    )


def ensure_interest_evolution_schedule(*, schedule: str = "24h") -> dict[str, Any]:
    write_interest_seed_memory()
    existing = [job for job in list_cron_jobs() if job.get("name") == "Eve Interest Evolution Research"]
    if existing:
        return {"status": "exists", "job": existing[0]}
    job = add_recurring_prompt_job(
        "Eve Interest Evolution Research",
        schedule,
        build_interest_evolution_prompt(),
        speaker="eve_initiative",
        enabled=True,
    )
    return {"status": "created", "job": job}


def current_daily_interest_paths() -> dict[str, str]:
    return {
        "world": str(daily_learning_path("world")),
        "technology": str(daily_learning_path("technology")),
        "personality": str(daily_learning_path("personality")),
    }


def read_daily_interest_registers(date_key: str | None = None, *, max_chars_per_file: int = 12000) -> dict[str, Any]:
    ensure_project_dirs()
    paths = {}
    contents = {}
    for kind in ("world", "technology", "personality"):
        path = MEMORY_DIR / kind / "daily" / f"{date_key}.md" if date_key else daily_learning_path(kind)
        paths[kind] = str(path)
        if path.exists():
            text = path.read_text(encoding="utf-8")
            contents[kind] = text[-max_chars_per_file:]
        else:
            contents[kind] = ""
    return {"date": date_key or daily_learning_path("world").stem, "paths": paths, "contents": contents}


def format_daily_interest_registers(registers: dict[str, Any]) -> str:
    lines = [f"Registos diarios de evolucao/interesses - {registers.get('date')}", ""]
    labels = {
        "world": "Mundo/gostos",
        "technology": "Tecnologia",
        "personality": "Personalidade/gostos da Eve",
    }
    for kind in ("world", "technology", "personality"):
        lines.append(f"## {labels[kind]}")
        lines.append(f"Ficheiro: {registers['paths'][kind]}")
        content = (registers["contents"].get(kind) or "").strip()
        lines.append(content if content else "Sem registo para esta data.")
        lines.append("")
    return "\n".join(lines).strip()
