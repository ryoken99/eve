# Eve

Eve is Sandro's local agent project in `D:\Eve`.

## Current State

Implemented v0.1 foundation:

- PowerShell launcher.
- Own OpenAI Codex / ChatGPT OAuth device-code login.
- Direct Codex chat client.
- Model selection from chat.
- Daily diary in `memory/diary`.
- JSONL chat logs in `logs/chat`.
- Short, medium and long memory folders.
- Constitution, mission and Sandro profile.
- Basic safe workspace tools.
- Basic terminal tool with dangerous-command blocking and logging.
- Draft skill format.
- Permission profiles.

## Launch

```powershell
powershell.exe -ExecutionPolicy Bypass -File D:\Eve\eve.ps1
```

or:

```powershell
python D:\Eve\main.py
```

## Chat Commands

```text
/modelo
/modelo gpt-5.5
/modelos
/diario
/diarios
/consolidar
/lembrar texto
/workspace
/ls
/ls pasta
/ler ficheiro
/nota texto
/cmd comando
/skills
/sair
```

## Safety

Eve v0.1 runs in safe mode. File writes are restricted to `D:\Eve\workspace`. Terminal commands are logged and dangerous tokens are blocked unless a future approval flow authorizes them.

Eve does not use Hermes, OpenClaw, or copied internal Codex app tokens for login. OAuth is a fresh login flow authorized by the user.
