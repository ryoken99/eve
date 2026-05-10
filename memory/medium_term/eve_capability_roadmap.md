# Eve Capability Roadmap

Resumo: {'total': 17, 'implemented_base': 17, 'partial': 0, 'missing': 0, 'needs_autonomous_habit': 17}

## 1. Permissoes elevadas/admin
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: admin temporario auditado
- Evidencia: tools/admin_executor.py, security/admin_gate.py
- Falta: nenhum caminho base

## 2. Diario completo das conversas
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: todas as mensagens em diario/transcript
- Evidencia: memory/diary_manager.py, logs/transcripts/chat
- Falta: nenhum caminho base

## 3. Consolidacao diaria varias vezes por dia
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: consolidacao periodica automatica
- Evidencia: dream/diary_consolidator.py, autonomy/daemon.py
- Falta: nenhum caminho base

## 4. Memoria curta/media/longa
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: camadas separadas e consultaveis
- Evidencia: memory/short_term, memory/medium_term, memory/long_term
- Falta: nenhum caminho base

## 5. Memoria semantica/vectorial
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: prefetch semantico em contexto
- Evidencia: memory/semantic_vector, memory/vector_provider.py
- Falta: nenhum caminho base

## 6. Sistema de sonhos
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: sonhos autonomos e curadoria de memoria
- Evidencia: dream/dream_cycle.py, dream/memory_reorganizer.py
- Falta: nenhum caminho base

## 7. Awareness temporal/situacional/espacial
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: percepcao periodica do ambiente
- Evidencia: core/awareness_engine.py, computer/active_window.py, computer/vision.py
- Falta: nenhum caminho base

## 8. Vontade/gostos/personalidade evolutiva
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: preferencias proprias evolutivas
- Evidencia: core/personality_engine.py, memory/personality
- Falta: nenhum caminho base

## 9. Lab proprio
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: experiencias por curiosidade propria
- Evidencia: lab, lab/lab_manager.py
- Falta: nenhum caminho base

## 10. Registo de erros e terminal
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: erros e terminal sempre analisaveis
- Evidencia: memory/errors, logs/transcripts/errors, logs/transcripts/tools
- Falta: nenhum caminho base

## 11. Pesquisa diaria de tecnologia
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: watchers diarios de labs/open source
- Evidencia: research/technology_watcher.py, tools/web_research.py
- Falta: nenhum caminho base

## 12. Pesquisa enviada para lab
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: research vira candidato de experiencia
- Evidencia: memory/technology/research_candidates.md, lab/candidate_improvements
- Falta: nenhum caminho base

## 13. Aprendizagem do mundo e tecnologia separada
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: ficheiros separados antes do lab
- Evidencia: memory/world/world_learning.md, memory/technology/technology_learning.md
- Falta: nenhum caminho base

## 14. Melhoria autonoma do sistema
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: melhorias propostas e testadas sem pedido manual
- Evidencia: autonomy/autonomy_director.py, self_improvement/verified_self_update.py
- Falta: nenhum caminho base

## 15. Controlo browser/UI humano
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: browser/teclado/rato/OCR com verificacao
- Evidencia: tools/browser_human.py, computer/mouse_control.py, computer/keyboard_control.py, computer/screen_capture.py
- Falta: nenhum caminho base

## 16. Recursive self-improvement
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: RSI controlado com sandbox, testes e rollback
- Evidencia: self_improvement/recursive_self_improvement.py, self_improvement/verified_self_update.py
- Falta: nenhum caminho base

## 17. Autonomia/proatividade sem input
- Estado: implemented_base
- Maturidade: needs_autonomous_habit
- Objetivo: acoes autonomas, mensagens e melhorias com o tempo
- Evidencia: autonomy/daemon.py, autonomy/proactive_decider.py, autonomy/autonomous_executor.py
- Falta: nenhum caminho base
