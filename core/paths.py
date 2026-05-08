from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = EVE_ROOT / "app"
CONFIG_DIR = EVE_ROOT / "config"
DOCS_DIR = EVE_ROOT / "docs"
MEMORY_DIR = EVE_ROOT / "memory"
LOGS_DIR = EVE_ROOT / "logs"
WORKSPACE_DIR = EVE_ROOT / "workspace"
SCRIPTS_DIR = EVE_ROOT / "scripts"
SKILLS_DIR = EVE_ROOT / "skills"
STATE_DIR = EVE_ROOT / "state"
BACKUPS_DIR = EVE_ROOT / "backups"
LAB_DIR = EVE_ROOT / "lab"
SECURITY_DIR = EVE_ROOT / "security"
ENTITIES_MEMORY_DIR = Path(r"D:\entities\memoria para  as entidades")


def ensure_project_dirs() -> None:
    for path in (
        CONFIG_DIR,
        DOCS_DIR,
        MEMORY_DIR / "diary",
        MEMORY_DIR / "short_term",
        MEMORY_DIR / "medium_term",
        MEMORY_DIR / "long_term",
        MEMORY_DIR / "errors",
        MEMORY_DIR / "procedural",
        MEMORY_DIR / "procedural" / "demonstrations",
        MEMORY_DIR / "world",
        MEMORY_DIR / "technology",
        MEMORY_DIR / "personality",
        MEMORY_DIR / "semantic_vector",
        MEMORY_DIR / "dream_reports",
        LOGS_DIR / "chat",
        LOGS_DIR / "terminal",
        LOGS_DIR / "errors",
        LOGS_DIR / "loops",
        LOGS_DIR / "autonomy",
        LOGS_DIR / "approvals",
        LOGS_DIR / "audit",
        LOGS_DIR / "ui_actions",
        LOGS_DIR / "ui_actions" / "screenshots",
        LOGS_DIR / "browser",
        LOGS_DIR / "research",
        LOGS_DIR / "email_drafts",
        WORKSPACE_DIR,
        SCRIPTS_DIR,
        SKILLS_DIR / "draft",
        SKILLS_DIR / "trusted",
        SKILLS_DIR / "app_specific",
        SKILLS_DIR / "app_specific" / "chrome",
        SKILLS_DIR / "app_specific" / "gmail",
        LAB_DIR / "experiments",
        LAB_DIR / "prototypes",
        LAB_DIR / "benchmarks",
        LAB_DIR / "candidate_improvements",
        LAB_DIR / "rejected_ideas",
        LAB_DIR / "reports",
        LAB_DIR / "queue",
        LAB_DIR / "evaluation_suites",
        STATE_DIR,
        STATE_DIR / "missions",
        BACKUPS_DIR,
        BACKUPS_DIR / "files",
        BACKUPS_DIR / "eve_versions",
        EVE_ROOT / "self_improvement" / "version_interviews",
        EVE_ROOT / "mobile_bridge",
        ENTITIES_MEMORY_DIR,
        ENTITIES_MEMORY_DIR / "entities",
        ENTITIES_MEMORY_DIR / "relations",
        ENTITIES_MEMORY_DIR / "indexes",
    ):
        path.mkdir(parents=True, exist_ok=True)
