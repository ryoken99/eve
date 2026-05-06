from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from core.paths import ENTITIES_MEMORY_DIR, MEMORY_DIR, STATE_DIR, ensure_project_dirs
from memory.entity_memory import list_base_memory_files
from security.audit_log import log_event


STATE_PATH = STATE_DIR / "entity_learning_state.json"
REPORT_DIR = MEMORY_DIR / "long_term"
SANDRO_REPORT = REPORT_DIR / "sandro_profile_from_entity_base.md"
EVE_REPORT = REPORT_DIR / "eve_identity_from_entity_base.md"
PROJECT_REPORT = REPORT_DIR / "sandro_projects_world_from_entity_base.md"
RELATION_REPORT = REPORT_DIR / "entity_relations_from_base.md"
REPORTS = (SANDRO_REPORT, EVE_REPORT, PROJECT_REPORT, RELATION_REPORT)

SANDRO_TERMS = {
    "sandro",
    "goncalves",
    "gonçalves",
    "portuguese",
    "portugues",
    "português",
    "teacher",
    "professor",
    "languages",
    "linguas",
    "línguas",
    "dream",
    "sonho",
    "interests",
    "interesses",
    "course",
    "curso",
    "student",
    "aluno",
}
EVE_TERMS = {
    "eve",
    "agent",
    "agente",
    "memoria",
    "memória",
    "skills",
    "self",
    "improvement",
    "autonomia",
    "rato",
    "teclado",
    "browser",
    "ocr",
    "admin",
    "lab",
    "recursive",
}
WORLD_TERMS = {
    "mundo",
    "ecos",
    "eternity",
    "mia",
    "ayla",
    "emma",
    "naomi",
    "inari",
    "reino",
    "personagem",
    "linguagem",
    "codigo",
    "código",
    "historia",
    "história",
}

MOJIBAKE_REPLACEMENTS = {
    "Ã¡": "á",
    "Ã ": "à",
    "Ã¢": "â",
    "Ã£": "ã",
    "Ã©": "é",
    "Ãª": "ê",
    "Ã­": "í",
    "Ã³": "ó",
    "Ã´": "ô",
    "Ãµ": "õ",
    "Ãº": "ú",
    "Ã§": "ç",
    "Ã": "Á",
    "Ã€": "À",
    "Ã‚": "Â",
    "Ãƒ": "Ã",
    "Ã‰": "É",
    "ÃŠ": "Ê",
    "Ã": "Í",
    "Ã“": "Ó",
    "Ã”": "Ô",
    "Ã•": "Õ",
    "Ãš": "Ú",
    "Ã‡": "Ç",
    "â€œ": '"',
    "â€": '"',
    "â€™": "'",
    "â€˜": "'",
    "â€“": "-",
    "â€”": "-",
    "â€¦": "...",
    "Â ": " ",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_state() -> dict:
    if not STATE_PATH.exists():
        return {"processed": {}, "last_run": None}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"processed": {}, "last_run": None}


def _write_state(state: dict) -> Path:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return STATE_PATH


def _repair_text(text: str) -> str:
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return text


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if len(part.strip()) > 30]


def _score(sentence: str, terms: set[str]) -> int:
    low = sentence.lower()
    return sum(1 for term in terms if term in low)


def _pick_relevant(sentences: list[str], terms: set[str], limit: int = 8) -> list[str]:
    ranked = sorted(((s, _score(s, terms)) for s in sentences), key=lambda item: item[1], reverse=True)
    return [s for s, score in ranked if score > 0][:limit]


def _top_terms(text: str, limit: int = 25) -> list[str]:
    words = re.findall(r"[\wÀ-ÿ]{4,}", text.lower())
    stop = {
        "para",
        "como",
        "sobre",
        "mais",
        "pela",
        "pelo",
        "with",
        "that",
        "this",
        "from",
        "have",
        "uma",
        "dos",
        "das",
        "que",
        "por",
        "com",
        "the",
        "and",
        "you",
        "your",
        "deve",
        "esta",
        "este",
    }
    counts = Counter(word for word in words if word not in stop)
    return [word for word, _ in counts.most_common(limit)]


def classify_text(text: str) -> dict:
    text = _repair_text(text)
    sentences = _sentences(text)
    return {
        "sandro": _pick_relevant(sentences, SANDRO_TERMS),
        "eve": _pick_relevant(sentences, EVE_TERMS),
        "world": _pick_relevant(sentences, WORLD_TERMS),
        "top_terms": _top_terms(text),
    }


def process_entity_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    classified = classify_text(text)
    return {
        "path": str(path),
        "relative": str(path.relative_to(ENTITIES_MEMORY_DIR)),
        "size": path.stat().st_size,
        "classified": classified,
    }


def _append_section(path: Path, title: str, source: str, bullets: list[str], top_terms: list[str]) -> None:
    if not bullets:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {title}\n\n")
        handle.write(f"Fonte: `{source}`\n\n")
        for bullet in bullets:
            handle.write(f"- {bullet[:1200]}\n")
        handle.write(f"\nTermos fortes: {', '.join(top_terms[:12])}\n")


def _clear_reports() -> None:
    for report in REPORTS:
        report.unlink(missing_ok=True)


def learn_entity_base(batch_size: int = 25, reset: bool = False) -> dict:
    ensure_project_dirs()
    state = {"processed": {}, "last_run": None} if reset else _read_state()
    if reset:
        _clear_reports()
    files = [Path(item["path"]) for item in list_base_memory_files()]
    processed_now = []
    for path in files:
        key = str(path)
        stat = path.stat()
        fingerprint = f"{stat.st_size}:{stat.st_mtime_ns}"
        if state["processed"].get(key) == fingerprint:
            continue
        result = process_entity_file(path)
        c = result["classified"]
        _append_section(SANDRO_REPORT, path.name, result["relative"], c["sandro"], c["top_terms"])
        _append_section(EVE_REPORT, path.name, result["relative"], c["eve"], c["top_terms"])
        _append_section(PROJECT_REPORT, path.name, result["relative"], c["world"], c["top_terms"])
        all_bullets = c["sandro"] + c["eve"] + c["world"]
        _append_section(RELATION_REPORT, path.name, result["relative"], all_bullets[:5], c["top_terms"])
        state["processed"][key] = fingerprint
        processed_now.append(result["relative"])
        if len(processed_now) >= batch_size:
            break
    state["last_run"] = _now()
    state["root"] = str(ENTITIES_MEMORY_DIR)
    state["total_files"] = len(files)
    state["processed_count"] = len(state["processed"])
    _write_state(state)
    payload = {
        "root": str(ENTITIES_MEMORY_DIR),
        "total_files": len(files),
        "processed_now": processed_now,
        "processed_count": len(state["processed"]),
        "remaining": max(0, len(files) - len(state["processed"])),
        "reports": [str(report) for report in REPORTS],
    }
    log_event("entity_base_learning_batch", payload)
    return payload
