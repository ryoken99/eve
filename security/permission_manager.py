from __future__ import annotations

from dataclasses import dataclass


SENSITIVE_ACTIONS = {
    "delete_files",
    "send_email",
    "publish_online",
    "purchase",
    "payment",
    "password_change",
    "install_software",
    "financial_action",
    "trading_action",
    "self_modify_core",
    "admin",
}


DANGEROUS_COMMAND_TOKENS = {
    "Remove-Item",
    "rm ",
    "rmdir",
    "del ",
    "format",
    "diskpart",
    "shutdown",
    "Restart-Computer",
    "Stop-Computer",
    "bcdedit",
    "reg delete",
    "takeown",
    "icacls",
}


@dataclass
class Decision:
    allowed: bool
    reason: str
    requires_approval: bool = False


def check_action(action: str, *, approved: bool = False) -> Decision:
    if action in SENSITIVE_ACTIONS and not approved:
        return Decision(False, f"Acao sensivel requer aprovacao: {action}", True)
    return Decision(True, "ok", False)


def check_command(command: str, *, approved: bool = False) -> Decision:
    lowered = command.lower()
    for token in DANGEROUS_COMMAND_TOKENS:
        if token.lower() in lowered and not approved:
            return Decision(False, f"Comando potencialmente perigoso requer aprovacao: {token}", True)
    return Decision(True, "ok", False)
