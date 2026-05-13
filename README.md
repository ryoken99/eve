# Eve

Eve is Sandro's local agent project. The repository is designed to run from any
clone path, including Sandro's two current Windows installs:

- PC 1: `D:\Eve`
- PC 2: `E:\eve`

Runtime state, logs, secrets and scheduled tasks are local to each machine.

## Fresh Windows Setup

Clone the repository to the folder you want, open PowerShell in the repo root,
then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_windows.ps1 -CreateVenv -InstallPlaywright -ConfigureLocalAccount
```

The bootstrap asks for the local Eve entry pass/code and creates a machine-local
installation profile in `secrets/local_account.json`. That file is ignored by
git, so every person and every PC can use a different pass and folder.

For Sandro's two current installs:

```powershell
# PC 1, repo cloned at D:\Eve
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_windows.ps1 -CreateVenv -InstallPlaywright -ConfigureLocalAccount -InstallName pc1 -AddSandroPcProfiles

# PC 2, repo cloned at E:\eve
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_windows.ps1 -CreateVenv -InstallPlaywright -ConfigureLocalAccount -InstallName pc2 -AddSandroPcProfiles
```

After the pass is accepted in the web UI, Eve shows the available installation
profiles, so Sandro can choose PC 1 or PC 2. If the chosen profile points to a
different folder than the current process, Eve warns instead of silently using
the wrong root.

After bootstrap, verify the clone:

```powershell
.\.venv\Scripts\python.exe scripts\check_fresh_clone_readiness.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\run_capability_tests.py
.\.venv\Scripts\python.exe scripts\full_eve_healthcheck.py
```

If you do not want a virtual environment, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_windows.ps1 -InstallPlaywright
```

## Optional External Dependencies

OCR fallback uses `pytesseract`, but Windows also needs the Tesseract executable
installed separately and available on `PATH`. DOM/Playwright and Windows UI
Automation do not require Tesseract.

Codex/OpenAI login, browser profiles, local pass, installation profiles, secrets,
scheduled tasks and admin shortcuts are intentionally per-machine. They must be
configured locally after a fresh clone.

## Launch

From the repo root:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\eve.ps1
```

or:

```powershell
python .\main.py
```

Web interface and daemon:

```powershell
.\scripts\start_eve_interface.cmd
```

Admin-elevated interface:

```powershell
.\scripts\start_eve_interface_admin.cmd
```

Install local Windows startup tasks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_eve_autonomy_tasks.ps1
```

Create a desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_eve_admin_shortcut.ps1
```

## Current Capabilities

- PowerShell launcher.
- Own OpenAI Codex / ChatGPT OAuth device-code login.
- Direct Codex chat client.
- Model selection from chat.
- Multiple saved Codex auth accounts.
- Daily diary in `memory/diary`.
- JSONL chat logs and transcripts.
- Short, medium and long memory folders.
- Operational memory for known local capabilities.
- Constitution, mission and Sandro profile.
- Safe workspace tools.
- Terminal tool with dangerous-command blocking and logging.
- Draft/trusted skills, including X publishing through Chrome profile Eve.
- Windows scheduled jobs through local install scripts.
- Codex-instructor/Eve loop modes.
- Mission control, autonomy cycles, Token Gate and autonomy reports.
- Safety modes, permission profiles and admin elevation helper.
- Computer Use v2 foundations: Playwright/DOM, Windows UI Automation, OCR fallback, app permissions and action verification.
- 17-point capability audit, runtime audit and ARSI hardening.

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

Eve runs with safety modes, local audit logs and permission profiles. File writes
are restricted to Eve-controlled project/workspace areas unless a tool explicitly
allows a broader operation. Terminal commands are logged and dangerous tokens are
blocked unless an approval/admin flow authorizes them.

Eve does not use Hermes, OpenClaw, or copied internal Codex app tokens for login.
OAuth is a fresh login flow authorized by the user on each machine.
