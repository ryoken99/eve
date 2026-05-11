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
OUTPUT_COMPARISON = MEMORY_DIR / "long_term" / "sandro_profile_comparison.md"

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
    "martial_arts": ["karate", "karaté", "karatê", "jiu-jitsu", "shukokai", "faixa", "belt", "lúcio", "bruno", "carlos"],
    "magic": ["magic", "magia", "magician", "mentalism", "mentalismo", "tamariz", "daortiz", "darwin ortiz"],
    "projects": ["echoes of eternity", "wonder world", "game", "jogo", "rpg", "classes", "story", "história", "livro", "rap"],
    "media": ["favorite movies", "list of favorite", "animes", "anime", "avatar", "matrix", "lord of the rings", "saw", "war horse", "death note", "kuroko", "sword art", "yu"],
    "constructed_language": ["unique history language", "drag =", "vibe =", "translation", "tons de pron", "linguagem", "naru", "zefiro"],
    "eve_preferences": ["eve", "assistant", "assistente", "proactive", "proativa", "português de portugal", "master", "mestre"],
    "people": ["bubu", "marta", "raton", "friends", "amigos", "siblings", "irmãos", "pais"],
    "pc_assets": ["computadores", "computer", "rtx", "i9", "windows 11", "citroen", "c3"],
}

CANONICAL_MAGIC_BOOKS = [
    "The Magic Way - Juan Tamariz",
    "Mnemonica - Juan Tamariz",
    "The Five Points in Magic - Juan Tamariz",
    "Verbal Magic - Juan Tamariz",
    "Sonata - Juan Tamariz",
    "The Magic Rainbow - Juan Tamariz",
    "Freedom of Expression - Dani DaOrtiz",
    "Designing Miracles - Darwin Ortiz",
    "Strong Magic - Darwin Ortiz",
    "Sterenko on Cards - Sterenko",
    "Drawing Room Deceptions - Guy Hollingworth",
    "Royal Road to Card Magic - Jean Hugard e Frederick Braue",
    "Expert at the Card Technique - Jean Hugard e Frederick Braue",
    "Card Control - Arthur Buckley",
    "Modern Coin Magic - J.B. Bobo",
    "Truques com Cartas - Joao Miranda",
    "Livro dos Segredos - Luis de Matos",
    "Scripting Magic 1 - Pete McCabe",
    "Scripting Magic 2 - Pete McCabe",
    "Paper Engine - Aaron Fisher",
    "13 Steps to Mentalism - Tony Corinda",
    "Nick Trost's Subtle Card Creations Volume 1",
    "Nick Trost's Subtle Card Creations Volume 2",
    "Nick Trost's Subtle Card Creations Volume 3",
    "The Card Magic of Nick Trost",
    "Destination Zero - John Bannon",
    "Mastering the Art of Magic - Eugene Burger",
    "Miracles with Cards - James Swain",
    "By Forces Unseen - Stephen Minch / Ernest Earick",
    "Card College Volume 1 - Roberto Giobbi",
    "Handcrafted Card Magic Volume 1 - Denis Behr",
    "Complete Course in Magic - Mark Wilson",
    "Scarne on Card Tricks - John Scarne",
    "Expert at the Card Table - S.W. Erdnase",
    "Confident Deceptions - Jason Ladanye",
    "Game Changer - Jason Ladanye",
    "Revolutionary Card Technique - Ed Marlo",
    "Cardially Yours - Ed Marlo",
]

CANONICAL_ANIMES = [
    "Death Note",
    "Devils Line",
    "Dr. Stone",
    "Gungrave",
    "Haikyuu!!",
    "Hellsing Ultimate",
    "Imawa no Kuni no Alice",
    "Kengan Ashura",
    "Kiseijuu: Sei no Kakuritsu",
    "Kuroko no Basket",
    "Log Horizon",
    "No Game No Life",
    "Noragami",
    "Orange",
    "Satsuriku no Tenshi",
    "Sword Art Online",
    "Yu-Gi-Oh!",
]

CANONICAL_MOVIES = [
    "Avatar 1 e 2",
    "The Last Samurai",
    "Matrix",
    "The Lord of the Rings",
    "Saw",
    "War Horse",
]

CONSTRUCTED_LANGUAGE_MAP = {
    "drag": "a",
    "vibe": "b",
    "ru": "c",
    "litch": "d",
    "il": "e",
    "franzel": "f",
    "hom": "g",
    "xiv": "h",
    "daru": "i",
    "rook": "j",
    "van": "k",
    "ni": "l",
    "ik": "m",
    "zad": "n",
    "naru": "o",
    "pak": "p",
    "roak": "q",
    "gol": "r",
    "shin": "s",
    "ra": "t",
    "ayr": "u",
    "fan": "v",
    "kim": "w",
    "rore": "x",
    "dir": "y",
    "kiri": "z",
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
    if missing and files is not None:
        raise FileNotFoundError(f"Ficheiros de memoria nao encontrados: {missing}")

    all_rows: list[SourceLine] = []
    for path in paths:
        if path.exists():
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
        "- Artes marciais: Karate Shukokai ha cerca de 8 anos e Jiu-Jitsu ha cerca de 2 anos. Sandro confirmou em 2026-05-07 que e faixa azul nas duas artes.",
        "- Mestres de artes marciais: Lucio aparece nas memorias antigas ligado ao Karate Shukokai; Bruno foi mestre em Evora; Carlos e o mestre no Pinhal Novo.",
        "- Interesses centrais: IA/agentes, programacao, criacao de jogos, escrita, magia/mentalismo, trading, linguas, ciencia, NBA/futebol, tecnologia e atualidade.",
        "- Projeto criativo principal: Echoes of Eternity: Wonder World/open-world RPG com classes fluidas, consequencias reais, vida/morte significativa, magia e armas com profundidade.",
        "- Preferencia de comunicacao: portugues de Portugal, tratamento por tu, informal, direto, como amigo proximo; pode chamar Sandro ou mestre.",
        "- Como Sandro quer a Eve: proativa, com continuidade entre conversas, memoria viva, capaz de aprender e adaptar, usando ferramentas reais do PC quando autorizado.",
        "- Magia: Sandro tem 38 livros de magia registados. A lista inclui The Magic Way - Juan Tamariz, Mnemonica - Juan Tamariz, 13 Steps to Mentalism - Tony Corinda, Card College Volume 1 - Roberto Giobbi e Cardially Yours - Ed Marlo.",
        "- Filmes favoritos registados: " + "; ".join(CANONICAL_MOVIES) + ".",
        "- Animes registados: " + "; ".join(CANONICAL_ANIMES) + ".",
        "- Linguagem criada: Sandro criou uma linguagem propria com traducao letra por letra, casos especiais, tons de pronuncia, contagem de silabas e tom final.",
        "- Mapa rapido da linguagem criada: drag=a, naru=o, ik=m, il=e, gol=r, dir=y, kiri=z.",
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
    lines.append("")
    lines.append("Livros de magia registados como lista canonica local:")
    for index, book in enumerate(CANONICAL_MAGIC_BOOKS, start=1):
        lines.append(f"{index}. {book}")
    lines.append("")
    _write_category(lines, categorized, "magic")
    lines.append("## Projetos Criativos")
    _write_category(lines, categorized, "projects")
    lines.append("## Filmes, Animes e Media")
    lines.append("")
    lines.append("- Filmes favoritos: " + "; ".join(CANONICAL_MOVIES) + ".")
    lines.append("- Animes registados: " + "; ".join(CANONICAL_ANIMES) + ".")
    lines.append("")
    _write_category(lines, categorized, "media")
    lines.append("## Linguagem Criada")
    lines.append("")
    lines.append("- A linguagem criada por Sandro envolve traducao letra por letra, casos especiais, tons de pronuncia, contagem de silabas, tom final e montagem das palavras.")
    mapping = ", ".join(f"{word}={letter}" for word, letter in CONSTRUCTED_LANGUAGE_MAP.items())
    lines.append(f"- Mapa base conhecido: {mapping}.")
    lines.append("- Exemplos conhecidos incluem: zefiro naru ni dragta ern; zefiro ik il miur ayur ern; hagma drag zefiro ik naru ast gol hina.")
    lines.append("")
    _write_category(lines, categorized, "constructed_language")
    lines.append("## Como Sandro Quer a Eve")
    _write_category(lines, categorized, "eve_preferences")
    lines.append("## Pessoas Importantes")
    _write_category(lines, categorized, "people")
    lines.append("## Equipamento e Recursos")
    _write_category(lines, categorized, "pc_assets")
    OUTPUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    _write_profile_comparison()

    index_path = rebuild_memory_index()
    payload = {
        "files": [str(path) for path in paths],
        "output": str(OUTPUT_MD),
        "sources": str(OUTPUT_JSON),
        "comparison": str(OUTPUT_COMPARISON),
        "index": str(index_path),
        "counts": {category: len(rows) for category, rows in categorized.items()},
    }
    log_event("sandro_core_memory_built", payload)
    return payload


def _write_profile_comparison() -> None:
    lines = [
        "# Comparacao do Perfil do Sandro",
        "",
        f"Atualizado pela Eve em {_now()}.",
        "",
        "## Coberto na memoria local",
        "",
        "- Identidade base: nome, nascimento, idade, localidade e preferencia por portugues de Portugal.",
        "- Artes marciais: faixa azul nas duas artes; Bruno em Evora; Carlos no Pinhal Novo; Lucio mantido como memoria antiga ligada ao Karate Shukokai.",
        "- Livros de magia: lista canonica local com 38 livros.",
        "- Filmes: Avatar 1 e 2, The Last Samurai, Matrix, The Lord of the Rings, Saw e War Horse.",
        "- Animes: Death Note, Dr. Stone, Haikyuu!!, Kengan Ashura, Kuroko no Basket, Sword Art Online, Yu-Gi-Oh! e outros da lista base.",
        "- Projetos: Echoes of Eternity, Wonder World/open-world RPG, jogos em RPG Maker/Unreal/Python, escrita e magia.",
        "- Linguagem criada: mapa letra por letra e exemplos base.",
        "- Interesses e hobbies: IA, programacao, trading, ciencia, linguas, NBA/futebol, tecnologia, magia, escrita, jogos e rap.",
        "- Pessoas e contexto: Bubu/Marta, Raton, familia/feiras, amigos e computadores principais.",
        "",
        "## Parcial ou a confirmar",
        "",
        "- Detalhes atuais de rotinas, progresso dos projetos, treinos e estudos podem mudar com o tempo.",
        "- Informacao de Bubu/Marta deve ser tratada como sensivel e potencialmente desatualizada.",
        "- Detalhes tecnicos atuais de OpenClaw, Hermes, ComfyUI, modelos e setup local podem ter mudado desde os ficheiros base.",
        "- Rap/Suno, preferencias de imagem e Mia Kinsky aparecem no perfil fornecido por Sandro, mas nao estao totalmente representados nos quatro ficheiros base usados nesta importacao.",
        "",
        "## Falta se Sandro quiser memoria completa",
        "",
        "- Importar ficheiros adicionais ou uma memoria escrita diretamente sobre Mia Kinsky.",
        "- Importar uma memoria separada sobre regras de imagem/prompting.",
        "- Importar uma memoria separada sobre estado atual dos projetos, PC, modelos locais e automacoes.",
    ]
    OUTPUT_COMPARISON.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_category(lines: list[str], categorized: dict[str, list[SourceLine]], category: str) -> None:
    rows = categorized.get(category) or []
    if not rows:
        lines.extend(["", "- Sem dados extraidos com confianca.", ""])
        return
    lines.append("")
    for row in rows[:8]:
        lines.append(f"- {row.text} `[{row.file}:{row.line}]`")
    lines.append("")
