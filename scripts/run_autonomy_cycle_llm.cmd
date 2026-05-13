@echo off
setlocal
set "EVE_ROOT=%~dp0.."
for %%I in ("%EVE_ROOT%") do set "EVE_ROOT=%%~fI"
cd /d "%EVE_ROOT%"
python -c "from autonomy.autonomy_director import run_autonomy_cycle; import json; print(json.dumps(run_autonomy_cycle(triggers=['scheduled','llm_review'], call_llm=True, cycle_name='scheduled_llm_review'), indent=2, ensure_ascii=False))"
