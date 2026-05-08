@echo off
cd /d D:\Eve
python -c "from autonomy.autonomy_director import run_autonomy_cycle; import json; print(json.dumps(run_autonomy_cycle(triggers=['scheduled'], call_llm=False, cycle_name='scheduled_local_review'), indent=2, ensure_ascii=False))"
