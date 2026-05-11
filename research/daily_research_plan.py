from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from autonomy.cron_manager import add_recurring_prompt_job, list_cron_jobs


DAILY_RESEARCH_JOB_NAME = "Eve Daily Research Pipeline"


@dataclass(frozen=True)
class DailyResearchTrack:
    id: str
    title: str
    cadence: str
    source_points: tuple[int, ...]
    purpose: str
    queries: tuple[str, ...]
    memory_targets: tuple[str, ...]
    lab_rule: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


DAILY_RESEARCH_TRACKS: tuple[DailyResearchTrack, ...] = (
    DailyResearchTrack(
        id="sandro_interests_to_eve_preferences",
        title="Gostos do Sandro -> gostos da Eve",
        cadence="daily",
        source_points=(8, 13, 17),
        purpose=(
            "Partir dos gostos, hobbies e projetos do Sandro, pesquisar o mundo a volta deles, "
            "e deixar que preferencias candidatas da Eve emerjam gradualmente sem fingir gosto consolidado."
        ),
        queries=(
            "anime game development narrative systems",
            "sports anime training feedback game design",
            "RPG Maker Unreal Engine anime inspired indie games",
            "procedural narrative persistent characters memory NPCs",
        ),
        memory_targets=(
            "memory/world/daily/DD-MM-AA.md",
            "memory/personality/daily/DD-MM-AA.md",
        ),
        lab_rule="Se um gosto gerar uma ideia testavel para o Sandro ou para a Eve, criar candidato no lab antes de alterar o core.",
    ),
    DailyResearchTrack(
        id="world_awareness",
        title="Mundo exterior e noticias",
        cadence="daily",
        source_points=(7, 8, 11, 13, 17),
        purpose=(
            "Manter a Eve atualizada sobre novidades do mundo, cultura, tecnologia, jogos, anime, ciencia e acontecimentos "
            "que possam dar contexto aos interesses do Sandro e a propria evolucao da Eve."
        ),
        queries=(
            "today technology AI gaming anime science news",
            "latest game development anime industry AI tools",
            "major world technology science culture updates",
        ),
        memory_targets=("memory/world/daily/DD-MM-AA.md",),
        lab_rule="Noticias viram lab candidate apenas quando sugerem uma capacidade, rotina, ferramenta ou prototipo concreto.",
    ),
    DailyResearchTrack(
        id="frontier_ai_technology",
        title="Tecnologia e IA aplicada",
        cadence="daily",
        source_points=(11, 12, 13, 14, 16),
        purpose=(
            "Acompanhar modelos e ferramentas de IA, incluindo texto, imagem, video, voz, agentes, computer-use, browser-use, "
            "memoria, avaliacao, automacao local e multimodalidade."
        ),
        queries=(
            "latest AI agents computer use models",
            "new image generation video generation AI models",
            "local automation AI memory retrieval agent tools",
            "OpenAI Anthropic Google DeepMind Meta xAI Hugging Face latest AI research",
        ),
        memory_targets=(
            "memory/technology/daily/DD-MM-AA.md",
            "memory/technology/research_candidates.md",
        ),
        lab_rule="Tecnologia nova deve virar candidato no lab quando pode melhorar memoria, tools, browser, seguranca, testes ou autonomia.",
    ),
    DailyResearchTrack(
        id="papers_and_open_source",
        title="Papers, labs e open source",
        cadence="daily",
        source_points=(11, 12, 14, 16),
        purpose=(
            "Ler sinais de research papers, repositorios e publicacoes de labs/comunidade para encontrar tecnicas aplicaveis "
            "a evolucao da Eve."
        ),
        queries=(
            "arXiv AI agents memory tool use evaluation latest",
            "GitHub trending AI agents RAG computer use automation",
            "OpenAI research Anthropic research Google DeepMind research Meta AI xAI research",
            "Hugging Face agents open source evaluation memory frameworks",
        ),
        memory_targets=(
            "memory/technology/daily/DD-MM-AA.md",
            "lab/candidate_improvements/",
        ),
        lab_rule="Separar factos da fonte, interpretacao da Eve e decisao: accepted, rejected, watch, or needs experiment.",
    ),
    DailyResearchTrack(
        id="error_learning",
        title="Erros, falhas e correcoes",
        cadence="several_times_daily",
        source_points=(10, 14, 16, 17),
        purpose=(
            "Rever erros registados, falhas de terminal, correcoes do Sandro e tarefas incompletas para gerar lessons, "
            "patches candidatos e verificacoes futuras."
        ),
        queries=(
            "local recent errors",
            "terminal failures",
            "tool verification failures",
            "Sandro corrections",
        ),
        memory_targets=(
            "memory/errors/",
            "memory/medium_term/lessons_learned.md",
            "lab/candidate_improvements/",
        ),
        lab_rule="Erro repetido ou falso sucesso deve criar patch candidate com teste antes de qualquer aplicacao.",
    ),
    DailyResearchTrack(
        id="memory_dream_consolidation",
        title="Memoria, sonhos e consolidacao",
        cadence="several_times_daily",
        source_points=(2, 3, 4, 5, 6, 13),
        purpose=(
            "Reler diario, camadas de memoria e memoria semantica para decidir o que fica em curto, medio ou longo prazo, "
            "que ligacoes semanticas surgem e que sonhos/relatorios devem virar acao."
        ),
        queries=(
            "daily transcript",
            "short medium long memory",
            "semantic memory links",
            "dream reports",
        ),
        memory_targets=(
            "memory/short_term/",
            "memory/medium_term/",
            "memory/long_term/",
            "memory/dream_reports/",
        ),
        lab_rule="Consolidacao pode criar tarefas/lab candidates, mas nao deve apagar memoria sensivel sem autorizacao explicita.",
    ),
    DailyResearchTrack(
        id="autonomous_self_improvement",
        title="Auto-melhoria autonoma",
        cadence="daily",
        source_points=(9, 12, 14, 16, 17),
        purpose=(
            "Misturar ideias proprias da Eve, erros registados e conhecimento externo para escolher melhorias pequenas, "
            "testaveis e reversiveis."
        ),
        queries=(
            "capability roadmap headroom",
            "recent lab candidates",
            "verified self update opportunities",
            "agent reliability evaluation methods",
        ),
        memory_targets=(
            "memory/medium_term/autonomous_capability_improvements.md",
            "lab/candidate_improvements/",
            "lab/experiments/",
        ),
        lab_rule="Nunca saltar direto para core: proposta -> experiencia -> teste -> patch verificado -> rollback plan -> log.",
    ),
    DailyResearchTrack(
        id="situational_awareness",
        title="Awareness local e ambiente",
        cadence="on_demand_and_daemon",
        source_points=(7, 15, 17),
        purpose=(
            "Perceber hora, sistema, ecra, janela ativa, browser e estado local antes de afirmar que viu, abriu, fechou, publicou ou terminou algo."
        ),
        queries=(
            "local time and system state",
            "active window",
            "screen OCR",
            "browser state",
        ),
        memory_targets=(
            "logs/ui_actions/",
            "logs/actions/DD-MM-AA.jsonl",
            "memory/medium_term/lessons_learned.md",
        ),
        lab_rule="Falhas de percepcao ou verificacao visual devem virar melhorias de tool verification.",
    ),
)


def daily_research_tracks() -> list[dict[str, Any]]:
    return [track.as_dict() for track in DAILY_RESEARCH_TRACKS]


def build_daily_research_pipeline_prompt() -> str:
    lines = [
        "Executa a rotina diaria integrada de pesquisa e evolucao da Eve.",
        "",
        "Objetivo central:",
        "Transformar gostos do Sandro, noticias do mundo, tecnologia externa, papers/open source, erros locais, memoria e ideias proprias da Eve em aprendizagem auditavel, lab candidates e melhorias verificadas.",
        "",
        "Regras obrigatorias:",
        "1. Separa factos de fontes, interpretacao da Eve, impacto para Sandro, impacto para Eve e decisao de lab.",
        "2. Regista mundo/gostos em memory/world/daily/DD-MM-AA.md.",
        "3. Regista tecnologia/papers/open source em memory/technology/daily/DD-MM-AA.md.",
        "4. Regista gostos candidatos ou preferencias da Eve em memory/personality/daily/DD-MM-AA.md.",
        "5. Erros, falsos sucessos e falhas de terminal viram lessons ou lab candidates, nao desculpas soltas.",
        "6. Ideias de self-improvement devem ir para lab/candidate_improvements antes de tocar no core.",
        "7. Usa web_research_report para internet auditavel; usa varias fontes quando possivel.",
        "8. Nao publiques, nao compres, nao envies emails e nao facas alteracoes sensiveis nesta rotina.",
        "9. No fim, deixa uma mensagem curta ao Sandro com: o que pesquisaste, o que aprendeste, que candidatos nasceram e o que ficou para testar.",
        "",
        "Pistas de pesquisa baseadas nos 17 pontos:",
    ]
    for track in DAILY_RESEARCH_TRACKS:
        lines.extend(
            [
                "",
                f"## {track.id}: {track.title}",
                f"Cadencia: {track.cadence}",
                "Pontos dos 17: " + ", ".join(str(point) for point in track.source_points),
                f"Proposito: {track.purpose}",
                "Queries/sementes:",
                *[f"- {query}" for query in track.queries],
                "Memoria destino:",
                *[f"- {target}" for target in track.memory_targets],
                f"Regra de lab: {track.lab_rule}",
            ]
        )
    return "\n".join(lines)


def format_daily_research_tracks(tracks: list[dict[str, Any]] | None = None) -> str:
    tracks = tracks or daily_research_tracks()
    lines = ["# Eve Daily Research Pipeline", ""]
    for track in tracks:
        lines.extend(
            [
                f"## {track['id']} - {track['title']}",
                f"- Cadencia: {track['cadence']}",
                "- Pontos dos 17: " + ", ".join(str(point) for point in track["source_points"]),
                f"- Proposito: {track['purpose']}",
                "- Memoria: " + ", ".join(track["memory_targets"]),
                f"- Lab: {track['lab_rule']}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def ensure_daily_research_pipeline_schedule(*, schedule: str = "24h") -> dict[str, Any]:
    existing = [job for job in list_cron_jobs() if job.get("name") == DAILY_RESEARCH_JOB_NAME]
    if existing:
        return {"status": "exists", "job": existing[0], "tracks": daily_research_tracks()}
    job = add_recurring_prompt_job(
        DAILY_RESEARCH_JOB_NAME,
        schedule,
        build_daily_research_pipeline_prompt(),
        speaker="eve_initiative",
        enabled=True,
    )
    return {"status": "created", "job": job, "tracks": daily_research_tracks()}
