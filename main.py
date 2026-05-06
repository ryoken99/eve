import argparse
import subprocess
import sys
from pathlib import Path

from core.paths import EVE_ROOT, ensure_project_dirs
from core.awareness_engine import describe_awareness
from memory.memory_manager import consolidate_today
from tools.terminal import run_command


def open_chat() -> int:
    ensure_project_dirs()
    script = EVE_ROOT / "app" / "eve_codex.py"
    return subprocess.call([sys.executable, str(script), "chat"], cwd=str(EVE_ROOT))


def status() -> None:
    ensure_project_dirs()
    print("Eve online. Modo actual: safe.")
    print(describe_awareness())


def main() -> int:
    parser = argparse.ArgumentParser(description="Eve local agent")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("chat")
    sub.add_parser("status")
    sub.add_parser("consolidate")
    cmd_p = sub.add_parser("cmd")
    cmd_p.add_argument("command")
    args = parser.parse_args()

    if args.cmd in (None, "chat"):
        return open_chat()
    if args.cmd == "status":
        status()
        return 0
    if args.cmd == "consolidate":
        print(f"Consolidado em: {consolidate_today()}")
        return 0
    if args.cmd == "cmd":
        result = run_command(args.command)
        print(result)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
