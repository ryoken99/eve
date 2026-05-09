# Eve

Eve is Sandro's local agent project in `D:\Eve`.

## Current State

Implemented local foundation:

- PowerShell launcher.
- Own OpenAI Codex / ChatGPT OAuth device-code login.
- Direct Codex chat client.
- Model selection from chat.
- Multiple saved Codex auth accounts.
- Daily diary in `memory/diary`.
- JSONL chat logs in `logs/chat`.
- Short, medium and long memory folders.
- Entity-base learning from `D:\entities\memoria para  as entidades`.
- Operational memory for known local capabilities.
- Constitution, mission and Sandro profile.
- Basic safe workspace tools.
- Basic terminal tool with dangerous-command blocking and logging.
- Draft/trusted skills, including X publishing through Chrome profile Eve.
- Windows scheduled X post jobs through `/x-agendar`.
- Codex-instructor/Eve loop modes, including mode 3 with no message limit.
- Mission control, autonomy cycles, Token Gate and autonomy reports.
- Safety modes, permission profiles and admin elevation helper.

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
/capacidades
/diario
/diarios
/consolidar
/sonhar
/lembrar texto
/world texto
/tech texto
/lab
/lab titulo | hipotese
/workspace
/ls
/ls pasta
/ler ficheiro
/nota texto
/cmd comando
/skills
/x-agendar HH:MM | texto em ingles
/loop-modo 3
/autonomia-ciclo
/sair
```

## Safety

Eve v0.1 runs in safe mode. File writes are restricted to `D:\Eve\workspace`. Terminal commands are logged and dangerous tokens are blocked unless a future approval flow authorizes them.

Eve does not use Hermes, OpenClaw, or copied internal Codex app tokens for login. OAuth is a fresh login flow authorized by the user.
