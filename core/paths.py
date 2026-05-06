from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = EVE_ROOT / "app"
CONFIG_DIR = EVE_ROOT / "config"
MEMORY_DIR = EVE_ROOT / "memory"
LOGS_DIR = EVE_ROOT / "logs"
WORKSPACE_DIR = EVE_ROOT / "workspace"
SKILLS_DIR = EVE_ROOT / "skills"
STATE_DIR = EVE_ROOT / "state"
BACKUPS_DIR = EVE_ROOT / "backups"
LAB_DIR = EVE_ROOT / "lab"


def ensure_project_dirs() -> None:
    for path in (
        CONFIG_DIR,
        MEMORY_DIR / "diary",
        MEMORY_DIR / "short_term",
        MEMORY_DIR / "medium_term",
        MEMORY_DIR / "long_term",
        MEMORY_DIR / "errors",
        MEMORY_DIR / "procedural",
        MEMORY_DIR / "world",
        MEMORY_DIR / "technology",
        MEMORY_DIR / "personality",
        LOGS_DIR / "chat",
        LOGS_DIR / "terminal",
        LOGS_DIR / "errors",
        WORKSPACE_DIR,
        SKILLS_DIR / "draft",
        SKILLS_DIR / "trusted",
        LAB_DIR / "experiments",
        LAB_DIR / "prototypes",
        LAB_DIR / "benchmarks",
        LAB_DIR / "candidate_improvements",
        LAB_DIR / "rejected_ideas",
        LAB_DIR / "reports",
        STATE_DIR,
        BACKUPS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
