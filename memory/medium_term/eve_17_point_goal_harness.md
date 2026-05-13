# Eve 17-Point Capability Goal Harness

Timestamp: 2026-05-13T22:32:40.566085Z
Target: 8.3/10
All points meet target: True
Points below target: 0

## Operational Setup
- Transcripts: {'chat': 'E:\\eve\\workspace\\unit_test_logs\\transcripts\\chat\\13-05-26.jsonl', 'tools': 'E:\\eve\\workspace\\unit_test_logs\\transcripts\\tools\\13-05-26.jsonl', 'actions': 'E:\\eve\\workspace\\unit_test_logs\\transcripts\\actions\\13-05-26.jsonl', 'errors': 'E:\\eve\\workspace\\unit_test_logs\\transcripts\\errors\\13-05-26.jsonl', 'console': 'E:\\eve\\workspace\\unit_test_logs\\transcripts\\console\\13-05-26.jsonl', 'interface': 'E:\\eve\\workspace\\unit_test_logs\\transcripts\\interface\\13-05-26.jsonl'}
- Capability schedule: {'status': 'exists', 'job': {'id': 'cron_6afd2e1952', 'name': 'Eve Capability Roadmap Review', 'schedule': '6h', 'command': 'Set-Location E:\\eve; python scripts\\capability_review.py', 'enabled': True, 'created_at': '2026-05-11T23:30:24.321408Z', 'last_run': '2026-05-13T21:40:59.895104Z', 'next_run': '2026-05-14T03:40:59.895104Z', 'run_count': 1}}
- Diary consolidation schedule: {'status': 'exists', 'job': {'id': 'cron_a53055b4d6', 'name': 'Eve Diary Consolidation', 'schedule': '6h', 'command': 'Set-Location E:\\eve; python scripts\\diary_consolidation.py', 'enabled': True, 'created_at': '2026-05-12T00:17:09.840769Z', 'last_run': '2026-05-13T21:40:59.895104Z', 'next_run': '2026-05-14T03:40:59.895104Z', 'run_count': 1}}
- Interest schedule: {'status': 'exists', 'job': {'id': 'cron_2bc300e0c8', 'kind': 'prompt', 'name': 'Eve Interest Evolution Research', 'schedule': '24h', 'prompt': 'Executa uma rotina autonoma de evolucao de interesses da Eve.\nObjetivo: partir dos gostos do Sandro, pesquisar online, aprender e permitir que a Eve desenvolva gostos proprios com o tempo.\n\nRegras obrigatorias:\n1. Escolhe 1 tema base do Sandro, 1 tema tecnico da Eve e 1 tema novo adjacente.\n2. Usa web_research_report com varias fontes quando precisares de internet.\n3. Se abrires browser, usa Chrome/perfil Eve, reutiliza a mesma aba e fecha a pagina no fim; web_research_report ja fecha a pagina, por isso nao chames browser_close em duplicado salvo se abriste uma pagina extra.\n4. Regista aprendizagem do mundo/gostos em memory/world/daily/DD-MM-AA.md.\n5. Regista aprendizagem tecnica em memory/technology/daily/DD-MM-AA.md.\n6. Regista mudancas ou candidatos de gostos proprios em memory/personality/daily/DD-MM-AA.md.\n7. Se algo puder melhorar a Eve, cria nota candidata para o lab antes de alterar core.\n8. No fim, deixa uma mensagem curta ao Sandro com: temas pesquisados, fontes principais, o que aprendeste, e se nasceu algum gosto/candidato novo.\nNao publiques no X nesta rotina. Nao compres, nao envies emails e nao faças alteracoes sensiveis.', 'speaker': 'eve_initiative', 'enabled': True, 'one_shot': False, 'created_at': '2026-05-11T23:30:27.918263Z', 'last_run': '2026-05-13T21:40:59.895104Z', 'next_run': '2026-05-14T21:40:59.895104Z', 'run_count': 1}}
- Daily research schedule: {'status': 'exists', 'job': {'id': 'cron_55e5c1676a', 'kind': 'prompt', 'name': 'Eve Daily Research Pipeline', 'schedule': '24h', 'prompt': 'Executa a rotina diaria integrada de pesquisa e evolucao da Eve.\n\nObjetivo central:\nTransformar gostos do Sandro, noticias do mundo, tecnologia externa, papers/open source, erros locais, memoria e ideias proprias da Eve em aprendizagem auditavel, lab candidates e melhorias verificadas.\n\nRegras obrigatorias:\n1. Separa factos de fontes, interpretacao da Eve, impacto para Sandro, impacto para Eve e decisao de lab.\n2. Regista mundo/gostos em memory/world/daily/DD-MM-AA.md.\n3. Regista tecnologia/papers/open source em memory/technology/daily/DD-MM-AA.md.\n4. Regista gostos candidatos ou preferencias da Eve em memory/personality/daily/DD-MM-AA.md.\n5. Erros, falsos sucessos e falhas de terminal viram lessons ou lab candidates, nao desculpas soltas.\n6. Ideias de self-improvement devem ir para lab/candidate_improvements antes de tocar no core.\n7. Usa web_research_report para internet auditavel; usa varias fontes quando possivel.\n8. Nao publiques, nao compres, nao envies emails e nao facas alteracoes sensiveis nesta rotina.\n9. No fim, deixa uma mensagem curta ao Sandro com: o que pesquisaste, o que aprendeste, que candidatos nasceram e o que ficou para testar.\n\nPistas de pesquisa baseadas nos 17 pontos:\n\n## sandro_interests_to_eve_preferences: Gostos do Sandro -> gostos da Eve\nCadencia: daily\nPontos dos 17: 8, 13, 17\nProposito: Partir dos gostos, hobbies e projetos do Sandro, pesquisar o mundo a volta deles, e deixar que preferencias candidatas da Eve emerjam gradualmente sem fingir gosto consolidado.\nQueries/sementes:\n- anime game development narrative systems\n- sports anime training feedback game design\n- RPG Maker Unreal Engine anime inspired indie games\n- procedural narrative persistent characters memory NPCs\nMemoria destino:\n- memory/world/daily/DD-MM-AA.md\n- memory/personality/daily/DD-MM-AA.md\nRegra de lab: Se um gosto gerar uma ideia testavel para o Sandro ou para a Eve, criar candidato no lab antes de alterar o core.\n\n## world_awareness: Mundo exterior e noticias\nCadencia: daily\nPontos dos 17: 7, 8, 11, 13, 17\nProposito: Manter a Eve atualizada sobre novidades do mundo, cultura, tecnologia, jogos, anime, ciencia e acontecimentos que possam dar contexto aos interesses do Sandro e a propria evolucao da Eve.\nQueries/sementes:\n- today technology AI gaming anime science news\n- latest game development anime industry AI tools\n- major world technology science culture updates\nMemoria destino:\n- memory/world/daily/DD-MM-AA.md\nRegra de lab: Noticias viram lab candidate apenas quando sugerem uma capacidade, rotina, ferramenta ou prototipo concreto.\n\n## frontier_ai_technology: Tecnologia e IA aplicada\nCadencia: daily\nPontos dos 17: 11, 12, 13, 14, 16\nProposito: Acompanhar modelos e ferramentas de IA, incluindo texto, imagem, video, voz, agentes, computer-use, browser-use, memoria, avaliacao, automacao local e multimodalidade.\nQueries/sementes:\n- latest AI agents computer use models\n- new image generation video generation AI models\n- local automation AI memory retrieval agent tools\n- OpenAI Anthropic Google DeepMind Meta xAI Hugging Face latest AI research\nMemoria destino:\n- memory/technology/daily/DD-MM-AA.md\n- memory/technology/research_candidates.md\nRegra de lab: Tecnologia nova deve virar candidato no lab quando pode melhorar memoria, tools, browser, seguranca, testes ou autonomia.\n\n## papers_and_open_source: Papers, labs e open source\nCadencia: daily\nPontos dos 17: 11, 12, 14, 16\nProposito: Ler sinais de research papers, repositorios e publicacoes de labs/comunidade para encontrar tecnicas aplicaveis a evolucao da Eve.\nQueries/sementes:\n- arXiv AI agents memory tool use evaluation latest\n- GitHub trending AI agents RAG computer use automation\n- OpenAI research Anthropic research Google DeepMind research Meta AI xAI research\n- Hugging Face agents open source evaluation memory frameworks\nMemoria destino:\n- memory/technology/daily/DD-MM-AA.md\n- lab/candidate_improvements/\nRegra de lab: Separar factos da fonte, interpretacao da Eve e decisao: accepted, rejected, watch, or needs experiment.\n\n## error_learning: Erros, falhas e correcoes\nCadencia: several_times_daily\nPontos dos 17: 10, 14, 16, 17\nProposito: Rever erros registados, falhas de terminal, correcoes do Sandro e tarefas incompletas para gerar lessons, patches candidatos e verificacoes futuras.\nQueries/sementes:\n- local recent errors\n- terminal failures\n- tool verification failures\n- Sandro corrections\nMemoria destino:\n- memory/errors/\n- memory/medium_term/lessons_learned.md\n- lab/candidate_improvements/\nRegra de lab: Erro repetido ou falso sucesso deve criar patch candidate com teste antes de qualquer aplicacao.\n\n## memory_dream_consolidation: Memoria, sonhos e consolidacao\nCadencia: several_times_daily\nPontos dos 17: 2, 3, 4, 5, 6, 13\nProposito: Reler diario, camadas de memoria e memoria semantica para decidir o que fica em curto, medio ou longo prazo, que ligacoes semanticas surgem e que sonhos/relatorios devem virar acao.\nQueries/sementes:\n- daily transcript\n- short medium long memory\n- semantic memory links\n- dream reports\nMemoria destino:\n- memory/short_term/\n- memory/medium_term/\n- memory/long_term/\n- memory/dream_reports/\nRegra de lab: Consolidacao pode criar tarefas/lab candidates, mas nao deve apagar memoria sensivel sem autorizacao explicita.\n\n## autonomous_self_improvement: Auto-melhoria autonoma\nCadencia: daily\nPontos dos 17: 9, 12, 14, 16, 17\nProposito: Misturar ideias proprias da Eve, erros registados e conhecimento externo para escolher melhorias pequenas, testaveis e reversiveis.\nQueries/sementes:\n- capability roadmap headroom\n- recent lab candidates\n- verified self update opportunities\n- agent reliability evaluation methods\nMemoria destino:\n- memory/medium_term/autonomous_capability_improvements.md\n- lab/candidate_improvements/\n- lab/experiments/\nRegra de lab: Nunca saltar direto para core: proposta -> experiencia -> teste -> patch verificado -> rollback plan -> log.\n\n## situational_awareness: Awareness local e ambiente\nCadencia: on_demand_and_daemon\nPontos dos 17: 7, 15, 17\nProposito: Perceber hora, sistema, ecra, janela ativa, browser e estado local antes de afirmar que viu, abriu, fechou, publicou ou terminou algo.\nQueries/sementes:\n- local time and system state\n- active window\n- screen OCR\n- browser state\nMemoria destino:\n- logs/ui_actions/\n- logs/actions/DD-MM-AA.jsonl\n- memory/medium_term/lessons_learned.md\nRegra de lab: Falhas de percepcao ou verificacao visual devem virar melhorias de tool verification.', 'speaker': 'eve_initiative', 'enabled': True, 'one_shot': False, 'created_at': '2026-05-11T23:53:28.381146Z', 'last_run': '2026-05-13T21:40:59.895104Z', 'next_run': '2026-05-14T21:40:59.895104Z', 'run_count': 1}, 'tracks': [{'id': 'sandro_interests_to_eve_preferences', 'title': 'Gostos do Sandro -> gostos da Eve', 'cadence': 'daily', 'source_points': (8, 13, 17), 'purpose': 'Partir dos gostos, hobbies e projetos do Sandro, pesquisar o mundo a volta deles, e deixar que preferencias candidatas da Eve emerjam gradualmente sem fingir gosto consolidado.', 'queries': ('anime game development narrative systems', 'sports anime training feedback game design', 'RPG Maker Unreal Engine anime inspired indie games', 'procedural narrative persistent characters memory NPCs'), 'memory_targets': ('memory/world/daily/DD-MM-AA.md', 'memory/personality/daily/DD-MM-AA.md'), 'lab_rule': 'Se um gosto gerar uma ideia testavel para o Sandro ou para a Eve, criar candidato no lab antes de alterar o core.'}, {'id': 'world_awareness', 'title': 'Mundo exterior e noticias', 'cadence': 'daily', 'source_points': (7, 8, 11, 13, 17), 'purpose': 'Manter a Eve atualizada sobre novidades do mundo, cultura, tecnologia, jogos, anime, ciencia e acontecimentos que possam dar contexto aos interesses do Sandro e a propria evolucao da Eve.', 'queries': ('today technology AI gaming anime science news', 'latest game development anime industry AI tools', 'major world technology science culture updates'), 'memory_targets': ('memory/world/daily/DD-MM-AA.md',), 'lab_rule': 'Noticias viram lab candidate apenas quando sugerem uma capacidade, rotina, ferramenta ou prototipo concreto.'}, {'id': 'frontier_ai_technology', 'title': 'Tecnologia e IA aplicada', 'cadence': 'daily', 'source_points': (11, 12, 13, 14, 16), 'purpose': 'Acompanhar modelos e ferramentas de IA, incluindo texto, imagem, video, voz, agentes, computer-use, browser-use, memoria, avaliacao, automacao local e multimodalidade.', 'queries': ('latest AI agents computer use models', 'new image generation video generation AI models', 'local automation AI memory retrieval agent tools', 'OpenAI Anthropic Google DeepMind Meta xAI Hugging Face latest AI research'), 'memory_targets': ('memory/technology/daily/DD-MM-AA.md', 'memory/technology/research_candidates.md'), 'lab_rule': 'Tecnologia nova deve virar candidato no lab quando pode melhorar memoria, tools, browser, seguranca, testes ou autonomia.'}, {'id': 'papers_and_open_source', 'title': 'Papers, labs e open source', 'cadence': 'daily', 'source_points': (11, 12, 14, 16), 'purpose': 'Ler sinais de research papers, repositorios e publicacoes de labs/comunidade para encontrar tecnicas aplicaveis a evolucao da Eve.', 'queries': ('arXiv AI agents memory tool use evaluation latest', 'GitHub trending AI agents RAG computer use automation', 'OpenAI research Anthropic research Google DeepMind research Meta AI xAI research', 'Hugging Face agents open source evaluation memory frameworks'), 'memory_targets': ('memory/technology/daily/DD-MM-AA.md', 'lab/candidate_improvements/'), 'lab_rule': 'Separar factos da fonte, interpretacao da Eve e decisao: accepted, rejected, watch, or needs experiment.'}, {'id': 'error_learning', 'title': 'Erros, falhas e correcoes', 'cadence': 'several_times_daily', 'source_points': (10, 14, 16, 17), 'purpose': 'Rever erros registados, falhas de terminal, correcoes do Sandro e tarefas incompletas para gerar lessons, patches candidatos e verificacoes futuras.', 'queries': ('local recent errors', 'terminal failures', 'tool verification failures', 'Sandro corrections'), 'memory_targets': ('memory/errors/', 'memory/medium_term/lessons_learned.md', 'lab/candidate_improvements/'), 'lab_rule': 'Erro repetido ou falso sucesso deve criar patch candidate com teste antes de qualquer aplicacao.'}, {'id': 'memory_dream_consolidation', 'title': 'Memoria, sonhos e consolidacao', 'cadence': 'several_times_daily', 'source_points': (2, 3, 4, 5, 6, 13), 'purpose': 'Reler diario, camadas de memoria e memoria semantica para decidir o que fica em curto, medio ou longo prazo, que ligacoes semanticas surgem e que sonhos/relatorios devem virar acao.', 'queries': ('daily transcript', 'short medium long memory', 'semantic memory links', 'dream reports'), 'memory_targets': ('memory/short_term/', 'memory/medium_term/', 'memory/long_term/', 'memory/dream_reports/'), 'lab_rule': 'Consolidacao pode criar tarefas/lab candidates, mas nao deve apagar memoria sensivel sem autorizacao explicita.'}, {'id': 'autonomous_self_improvement', 'title': 'Auto-melhoria autonoma', 'cadence': 'daily', 'source_points': (9, 12, 14, 16, 17), 'purpose': 'Misturar ideias proprias da Eve, erros registados e conhecimento externo para escolher melhorias pequenas, testaveis e reversiveis.', 'queries': ('capability roadmap headroom', 'recent lab candidates', 'verified self update opportunities', 'agent reliability evaluation methods'), 'memory_targets': ('memory/medium_term/autonomous_capability_improvements.md', 'lab/candidate_improvements/', 'lab/experiments/'), 'lab_rule': 'Nunca saltar direto para core: proposta -> experiencia -> teste -> patch verificado -> rollback plan -> log.'}, {'id': 'situational_awareness', 'title': 'Awareness local e ambiente', 'cadence': 'on_demand_and_daemon', 'source_points': (7, 15, 17), 'purpose': 'Perceber hora, sistema, ecra, janela ativa, browser e estado local antes de afirmar que viu, abriu, fechou, publicou ou terminou algo.', 'queries': ('local time and system state', 'active window', 'screen OCR', 'browser state'), 'memory_targets': ('logs/ui_actions/', 'logs/actions/DD-MM-AA.jsonl', 'memory/medium_term/lessons_learned.md'), 'lab_rule': 'Falhas de percepcao ou verificacao visual devem virar melhorias de tool verification.'}]}
- Roadmap path: E:\eve\memory\medium_term\eve_capability_roadmap.md
- History path: E:\eve\logs\autonomy\capability_reviews.jsonl

## 1. Permissoes elevadas/admin
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: admin status probe exists, admin actions have a log target, elevated command path is auditably prepared, startup tasks support RunLevel Highest
- Evidence: tools/admin_executor.py, security/admin_gate.py
- Habit evidence: logs/admin_actions (3), backups/files (135)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 2. Diario completo das conversas
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: daily transcript files exist, chat/tools/actions/errors/console/interface channels are separated, runtime can append tool events, console/interface/loop messages are captured
- Evidence: memory/diary_manager.py, logs/transcripts/chat
- Habit evidence: logs/transcripts/chat (3), memory/diary (3)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 3. Consolidacao diaria varias vezes por dia
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: diary consolidation is scheduled several times per day, daemon calls the harness, consolidation run history is appended
- Evidence: dream/diary_consolidator.py, autonomy/daemon.py
- Habit evidence: memory/medium_term (10), memory/dream_reports (3)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 4. Memoria curta/media/longa
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: short/medium/long memory directories exist, memory items are classified before storage, promotion/routing outputs are auditable, context retrieval has a stable entrypoint
- Evidence: memory/short_term, memory/medium_term, memory/long_term
- Habit evidence: memory/short_term (1), memory/medium_term (10), memory/long_term (13)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 5. Memoria semantica/vectorial
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: semantic vector directory exists, vector rebuild is callable, prefetch is exposed as a tool
- Evidence: memory/semantic_vector, memory/vector_provider.py
- Habit evidence: memory/semantic_vector (11)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 6. Sistema de sonhos
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: dream report directory exists, dream cycle queues lab ideas, dream cycle emits structured memory decisions, memory decisions are written to reports
- Evidence: dream/dream_cycle.py, dream/memory_reorganizer.py
- Habit evidence: memory/dream_reports (3)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 7. Awareness temporal/situacional/espacial
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: awareness engine is callable, screen/window tools are present, tool runtime captures before/after awareness, tool results require verification
- Evidence: core/awareness_engine.py, computer/active_window.py, computer/vision.py
- Habit evidence: logs/ui_actions (1), logs/browser (1)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 8. Vontade/gostos/personalidade evolutiva
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: personality memory exists, interest evolution schedule exists, candidate preferences have states, preferences mature only after repeated evidence
- Evidence: core/personality_engine.py, memory/personality
- Habit evidence: memory/personality (10), memory/medium_term/autonomous_capability_improvements.md (1)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 9. Lab proprio
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: lab candidate directory exists, candidate creation API exists, candidate results include metrics and decisions, reports/queue directories exist
- Evidence: lab, lab/lab_manager.py
- Habit evidence: lab/candidate_improvements (243), lab/reports (9)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 10. Registo de erros e terminal
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: error transcript exists, error memory exists, terminal commands enter tool transcript, errors can create lab candidates
- Evidence: memory/errors, logs/transcripts/errors, logs/transcripts/tools
- Habit evidence: logs/transcripts/errors (3), memory/errors (8)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 11. Pesquisa diaria de tecnologia
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: daily research pipeline schedule exists, technology watcher exists, frontier labs are explicit, open-source and papers sources are explicit
- Evidence: research/technology_watcher.py, tools/web_research.py
- Habit evidence: memory/technology (3), logs/browser (1)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 12. Pesquisa enviada para lab
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: research-to-lab target exists, candidate improvement path exists, daily research prompt includes lab decision, research items get formal apply/test/watch/ignore decisions
- Evidence: memory/technology/research_candidates.md, lab/candidate_improvements
- Habit evidence: memory/technology/research_candidates.md (1), lab/candidate_improvements (243)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 13. Aprendizagem do mundo e tecnologia separada
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: world daily target exists, technology daily target exists, personality daily target exists, daily learning separation is verifiable
- Evidence: memory/world/world_learning.md, memory/technology/technology_learning.md
- Habit evidence: memory/world/world_learning.md (1), memory/technology/technology_learning.md (1)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 14. Melhoria autonoma do sistema
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: autonomy cycle exists, deterministic improvement planner exists, verified update path exists, improvements require tests before core changes
- Evidence: autonomy/autonomy_director.py, self_improvement/verified_self_update.py
- Habit evidence: logs/autonomy (42), lab/candidate_improvements (243)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 15. Controlo browser/UI humano
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: browser control exists, keyboard/mouse control exists, screenshots/OCR are available, critical visual tools require explicit verification
- Evidence: tools/browser_human.py, computer/mouse_control.py, computer/keyboard_control.py, computer/screen_capture.py
- Habit evidence: logs/ui_actions (1), logs/browser (1)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 16. ARSI - Autonomous Recursive Self Improvement
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: ARSI policy exists, backup path exists, autonomous safe cycle exposes gates, verified update requires rollback/test discipline
- Evidence: self_improvement/recursive_self_improvement.py, self_improvement/verified_self_update.py, self_improvement/arsi_cycle.py
- Habit evidence: backups/tmp (103), lab/candidate_improvements/verified_updates (170)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none

## 17. Autonomia/proatividade sem input
- Score: 10.0 / 8.3 | Meets target: True
- Maturity: improve_quality
- Controls: daemon heartbeat exists or can be written, cron jobs exist, proactive decisions are logged, autonomous executor is bounded and auditable
- Evidence: autonomy/daemon.py, autonomy/proactive_decider.py, autonomy/autonomous_executor.py
- Habit evidence: state/daemon_heartbeat.json (1), state/missions (325), logs/autonomy (42)
- Improvement evidence: lab/candidate_improvements (72), memory/medium_term capability reports (2), state/capability_roadmap_state.json
- Missing paths: none
- Gaps for Codex: none
