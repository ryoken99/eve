# PC2 Runtime Final Cleanup

Generated: 2026-05-16 00:04:44

## Role

PC 2 is the main home/runtime of Eve.

## Git

Current branch: main
Last commit: 95e38fc Prepare PC2 main Eve runtime startup

## Web UI

Target URL:
http://127.0.0.1:8787/

Manual HTTP result:
FAILED: The operation has timed out.

Port 8787 summary:
- TIME_WAIT entries: 4990
- LISTEN entries: 0

Observation:
Port 8787 remains saturated in Windows TCP state. Even a minimal HTTP server on 127.0.0.1:8787 timed out, so the current blocker is the local TCP/Windows port state, not only Eve's Web UI code. Web UI code was previously verified on alternate local ports.

## Netstat 8787

  TCP    127.0.0.1:8787         127.0.0.1:49152        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49153        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49154        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49155        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49156        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49157        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49158        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49159        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49160        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49161        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49162        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49163        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49164        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49165        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49166        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49167        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49168        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49169        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49170        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49171        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49172        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49173        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49174        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49175        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49176        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49177        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49178        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49179        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49180        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49181        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49182        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49183        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49184        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49185        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49186        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49187        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49188        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49189        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49190        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49191        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49192        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49193        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49194        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49195        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49196        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49197        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49198        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49199        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49200        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49201        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49202        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49203        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49204        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49205        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49206        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49207        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49208        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49209        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49210        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49211        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49212        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49213        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49214        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49215        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49216        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49217        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49218        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49219        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49220        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49221        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49222        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49223        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49224        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49225        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49226        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49227        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49228        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49229        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49230        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49231        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49232        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49233        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49235        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49236        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49237        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49238        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49239        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49240        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49241        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49242        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49243        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49244        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49245        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49246        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49247        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49248        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49249        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49250        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49251        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49252        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49253        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49254        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49255        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49256        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49257        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49258        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49259        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49260        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49261        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49262        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49263        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49264        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49265        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49266        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49267        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49268        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49269        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49270        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49271        TIME_WAIT       0
  TCP    127.0.0.1:8787         127.0.0.1:49272        TIME_WAIT       0


## Eve/Python Processes After Cleanup


ProcessId CommandLine                                                                                                  
--------- -----------                                                                                                  
     5412 E:\eve\.venv\Scripts\python.exe E:\eve\scripts\telegram_bridge.py run --interval 5                           
    10036 "C:\Users\Sandro\AppData\Local\Programs\Python\Python311\python.exe" E:\eve\scripts\telegram_bridge.py run...
    11772 "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -Command "[Console]::OutputEncoding=[System.Te...




## Telegram

Telegram bridge was stopped and restarted through scripts\telegram_bridge.py.
Telegram status after cleanup:

```json
{
  "ok": true,
  "running": true,
  "pid": 10036,
  "token": {
    "configured": true,
    "masked": "8774**************************************jp64"
  },
  "status_error": null,
  "errors": []
}
```

Telegram notify test was attempted and returned ok with a Telegram message id in command output.

## Healthcheck

full_eve_17_points_healthcheck.py:
- overall_score: 10.0
- all_points_at_target: True
- telegram_bridge_status.running: True

capability_review.py completed with status ok.

## Startup Task

The automatic startup task is still only prepared.
Do not install until Sandro confirms after manual Web UI + Telegram test.

Install command when confirmed:

powershell.exe -ExecutionPolicy Bypass -File .\scripts\install_eve_pc2_startup_task.ps1

Uninstall command:

powershell.exe -ExecutionPolicy Bypass -File .\scripts\uninstall_eve_pc2_startup_task.ps1

## Git Policy

Do not commit secrets, logs, state/telegram_bridge*, memory, workspace or PIDs.

## Next Action Needed

To clear the stuck TCP state on 8787, reboot Windows or use an admin-level TCP stack reset. After reboot, run:

powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_eve_pc2.ps1
powershell.exe -ExecutionPolicy Bypass -File .\scripts\status_eve_pc2.ps1
