from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from core.paths import ENTITIES_MEMORY_DIR, MEMORY_DIR, ensure_project_dirs
from memory.semantic_vector.vector_store import rebuild_memory_index
from security.audit_log import log_event


TARGET_FILES = [
    "mem.txt",
    "mem resume .txt",
    "mastermind 0 .txt",
    "mastermind 1 .txt",
]
OUTPUT_MD = MEMORY_DIR / "long_term" / "sandro_core_memory.md"
OUTPUT_JSON = MEMORY_DIR / "long_term" / "sandro_core_memory_sources.json"

CATEGORY_PATTERNS = {
    "identity": [
        "full name",
        "nome completo",
        "nasceu",
        "born",
        "years old",
        "anos",
        "portugal",
        "pinhal novo",
    ],
    "languages": ["language", "languages", "língua", "lingua", "portuguese", "bengali", "japanese", "francês", "italiano"],
    "studies_work": ["biology", "biologia", "computer engineering", "engenharia", "trader", "trading", "financial", "family business", "negócio"],
    "martial_arts": ["karate", "karaté", "karatê", "jiu-jitsu", "shukokai", "faixa", "belt", "lúcio", "bruno"],
    "magic": ["magic", "magia", "magician", "mentalism", "mentalismo", "tamariz", "daortiz", "darwin ortiz"],
    "projects": ["echoes of eternity", "wonder world", "game", "jogo", "rpg", "classes", "story", "história", "livro", "rap"],
    "eve_preferences": ["eve", "assistant", "assistente", "proactive", "proativa", "português de portugal", "master", "mestre"],
    "people": ["bubu", "marta", "raton", "friends", "amigos", "siblings", "irmãos", "pais"],
    "pc_assets": ["computadores", "computer", "rtx", "i9", "windows 11", "citroen", "c3"],
}


@dataclass
class SourceLine:
    file: str
    line: int
    text: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _repair_text(text: str) -> str:
    try:
        repaired = text.encode("latin1").decode("utf-8")
        if repaired.count("Ã") + repaired.count("â") < text.count("Ã") + text.count("â"):
            return repaired
    except UnicodeError:
        pass
    try:
        repaired = text.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
        if repaired.count("Ã") + repaired.count("â") < text.count("Ã") + text.count("â"):
            return repaired
    except UnicodeError:
        pass
    return text


def _target_paths(files: Iterable[str] | None = None) -> list[Path]:
    names = list(files or TARGET_FILES)
    return [ENTITIES_MEMORY_DIR / name for name in names]


def _normalise_line(line: str) -> str:
    line = _repair_text(line)
    line = re.sub(r"\s+", " ", line).strip(" -\t")
    return line


def _read_source_lines(path: Path) -> list[SourceLine]:
    rows: list[SourceLine] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for index, raw in enumerate(text.splitlines(), start=1):
        line = _normalise_line(raw)
        if len(line) >= 20:
            rows.append(SourceLine(path.name, index, line))
    return rows


def _matches(line: str, patterns: list[str]) -> bool:
    lowered = line.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def _dedupe(rows: list[SourceLine]) -> list[SourceLine]:
    seen: set[str] = set()
    unique: list[SourceLine] = []
    for row in rows:
        key = re.sub(r"\W+", " ", row.text.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def build_sandro_core_memory(files: Iterable[str] | None = None) -> dict:
    ensure_project_dirs()
    paths = _target_paths(files)
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Ficheiros de memoria nao encontrados: {missing}")

    all_rows: list[SourceLine] = []
    for path in paths:
        all_rows.extend(_read_source_lines(path))

    categorized: dict[str, list[SourceLine]] = {}
    for category, patterns in CATEGORY_PATTERNS.items():
        categorized[category] = _dedupe([row for row in all_rows if _matches(row.text, patterns)])[:40]

    sources = {
        category: [{"file": row.file, "line": row.line, "text": row.text} for row in rows]
        for category, rows in categorized.items()
    }
    OUTPUT_JSON.write_text(json.dumps({"built_at": _now(), "sources": sources}, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Sandro Core Memory",
        "",
        f"Construido pela Eve em {_now()} a partir de memoria base indicada por Sandro.",
        "",
        "Regra de uso: estes dados sao memoria de trabalho local. Quando houver conflito, preferir fontes mais recentes e explicitas. Distinguir factos pessoais estaveis de material de jogo, roleplay ou brainstorming.",
        "",
        "## Resumo Operacional Confirmado",
        "",
        "- Nome completo: Sandro Gabriel Figueiredo Goncalves.",
        "- Data de nascimento: 17 de junho de 1999. Em 2026-05-06, Sandro tem 26 anos.",
        "- Linguas: portugues nativo; ingles e espanhol fluentes/avancados; frances e italiano com boa compreensao; japones e bengali em nivel basico/aprendizagem.",
        "- Artes marciais: Karate Shukokai ha cerca de 8 anos e Jiu-Jitsu ha cerca de 2 anos. Fontes recentes indicam faixa azul; fontes antigas indicam Karate faixa azul e Jiu-Jitsu faixa branca com dois graus. Se perguntarem a faixa atual, responder que a memoria mais recente diz faixa azul em ambos, mencionando a divergencia se necessario.",
        "- Mestre de Karate Shukokai: Lucio. Mestre de Jiu-Jitsu: Bruno.",
        "- Interesses centrais: IA/agentes, programacao, criacao de jogos, escrita, magia/mentalismo, trading, linguas, ciencia, NBA/futebol, tecnologia e atualidade.",
        "- Projeto criativo principal: Echoes of Eternity: Wonder World/open-world RPG com classes fluidas, consequencias reais, vida/morte significativa, magia e armas com profundidade.",
        "- Preferencia de comunicacao: portugues de Portugal, tratamento por tu, informal, direto, como amigo proximo; pode chamar Sandro ou mestre.",
        "- Como Sandro quer a Eve: proativa, com continuidade entre conversas, memoria viva, capaz de aprender e adaptar, usando ferramentas reais do PC quando autorizado.",
        "",
        "## Identidade e Perfil",
    ]
    _write_category(lines, categorized, "identity")
    lines.append("## Linguas")
    _write_category(lines, categorized, "languages")
    lines.append("## Estudos, Trabalho e Competencias")
    _write_category(lines, categorized, "studies_work")
    lines.append("## Artes Marciais")
    _write_category(lines, categorized, "martial_arts")
    lines.append("## Magia e Mentalismo")
    _write_category(lines, categorized, "magic")
    lines.append("## Projetos Criativos")
    _write_category(lines, categorized, "projects")
    lines.append("## Como Sandro Quer a Eve")
    _write_category(lines, categorized, "eve_preferences")
    lines.append("## Pessoas Importantes")
    _write_category(lines, categorized, "people")
    lines.append("## Equipamento e Recursos")
    _write_category(lines, categorized, "pc_assets")
    OUTPUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    index_path = rebuild_memory_index()
    payload = {
        "files": [str(path) for path in paths],
        "output": str(OUTPUT_MD),
        "sources": str(OUTPUT_JSON),
        "index": str(index_path),
        "counts": {category: len(rows) for category, rows in categorized.items()},
    }
    log_event("sandro_core_memory_built", payload)
    return payload


def _write_category(lines: list[str], categorized: dict[str, list[SourceLine]], category: str) -> None:
    rows = categorized.get(category) or []
    if not rows:
        lines.extend(["", "- Sem dados extraidos com confianca.", ""])
        return
    lines.append("")
    for row in rows[:8]:
        lines.append(f"- {row.text} `[{row.file}:{row.line}]`")
    lines.append("")
