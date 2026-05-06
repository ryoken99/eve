# Eve Specification

Fonte: conversa partilhada do ChatGPT "Criacao da Eve PC", lida em 2026-05-06.

## Visao

A Eve deve ser um agente local autonomo com memoria viva, corpo digital, aprendizagem continua, laboratorio proprio e capacidade de se melhorar recursivamente de forma controlada.

## Principios

- Nao copiar diretamente Hermes Agent ou OpenClaw.
- Usar a logica deles como inspiracao, mas manter a Eve simples, controlavel e adaptada ao Sandro.
- Construir por modulos e fases, com um MVP seguro primeiro.
- Separar conversa, memoria, ferramentas, permissao, execucao, logs e auto-melhoria.
- Toda acao sensivel deve ter permissao e registo.

## Blocos Principais

1. Terminal agent com Codex/OpenAI auth.
2. Memoria em camadas.
3. Diario completo.
4. Consolidacao varias vezes por dia.
5. Sistema de sonhos.
6. Memoria semantica/vetorial.
7. Skills proprias.
8. Modo aprendizagem por demonstracao.
9. Aprendizagem adaptativa durante tarefas.
10. Proatividade.
11. Tarefas programadas.
12. Awareness temporal, situacional e espacial.
13. Controlo humano do PC por visao, rato e teclado.
14. Browser humano com contas reais.
15. Terminal e programacao.
16. Admin controlado.
17. Personalidade e gostos evolutivos.
18. Pesquisa diaria do mundo e da tecnologia.
19. Lab proprio.
20. Registo total de erros.
21. Sistema autonomo de melhoria.
22. Recursive self-improvement como objetivo maximo.

## Fases

### Fase 1: Eve Core

- Chat no terminal.
- Auth Codex/OpenAI proprio.
- Personalidade base.
- Memoria basica em Markdown/JSON.
- Leitura e escrita de notas.
- Resumo de projetos.
- Pasta propria em `D:\Eve`.

### Fase 2: Operadora do PC

- Ler pastas.
- Abrir e criar ficheiros.
- Organizar documentos, imagens e textos.
- Executar scripts Python.
- Trabalhar com projetos do utilizador.
- Explicar logs e erros.

### Fase 3: Programadora

- Editar codigo.
- Criar ficheiros.
- Corrigir erros.
- Correr comandos.
- Testar scripts.
- Guardar rollback antes de alteracoes relevantes.

### Fase 4: Multi-modelo

- Escolha manual de modelo Codex.
- Possivel roteamento futuro entre modelos locais, Codex, GPT/API, Claude, Gemini e modelos especializados.
- Usar modelos mais baratos para tarefas simples e modelos fortes para tarefas complexas.

### Fase 5: Interface, voz e automacoes

- Dashboard simples.
- Voz.
- Notificacoes.
- Comandos por fala.
- Ligacao ao telemovel.
- Tarefas programadas.

### Fase 6: Aprendizagem e auto-melhoria

- Diario de tarefas.
- Resumo automatico de sessoes.
- Criacao de skills a partir de tarefas repetidas.
- Lab de experiencias.
- Testes em sandbox.
- Patches com aprovacao quando forem criticos.
- Rollback sempre que a propria Eve alterar codigo importante.

## Arquitetura Desejada

```text
Eve/
  app/
  agents/
    planner
    coder
    researcher
    organizer
  memory/
    user_profile
    projects
    preferences
    skills
    diary
  tools/
    filesystem
    terminal
    code_editor
    browser_human_control
    web_research
    admin_executor
  autonomy/
    scheduler
    event_watcher
    proactive_decider
    notification_policy
    autonomous_action_log
  research/
    technology_watcher
    world_watcher
    paper_reader
    open_source_tracker
  dream/
    diary_consolidator
    memory_reorganizer
    pattern_finder
    personality_reflector
    lab_idea_generator
  lab/
    experiments
    prototypes
    benchmarks
    candidate_improvements
    rejected_ideas
    reports
  self_improvement/
    error_analyzer
    improvement_planner
    patch_generator
    sandbox_tester
    rollback_manager
    core_updater
  security/
    permission_profiles
    sensitive_action_guard
    credential_vault
    audit_log
    admin_gate
    emergency_lock
  logs/
```

## Ciclos

### Ciclo Normal

Sandro fala -> Eve consulta memoria -> entende contexto -> planeia -> age -> responde -> regista no diario.

### Ciclo de Aprendizagem

Sandro demonstra -> Eve observa -> grava passos -> interpreta intencao -> cria skill -> testa -> guarda versao.

### Ciclo Adaptativo

Eve executa skill -> algo falha -> tenta alternativa -> se resolver, guarda licao -> atualiza skill.

### Ciclo de Sonho

Eve rele diario e memorias -> filtra ruido -> move informacao entre camadas -> detecta padroes -> gera ideias -> envia para o lab.

### Ciclo de Investigacao

Eve pesquisa mundo/tecnologia -> guarda notas -> classifica utilidade -> envia tecnologia promissora para o lab -> testa -> decide se aplica.

### Ciclo de Auto-melhoria

Erros + sonhos + pesquisa + lab + feedback -> proposta de melhoria -> teste no lab -> patch -> aprovacao se critico -> aplica -> guarda rollback.

## Seguranca

- Permissoes por nivel: ler, escrever, executar, internet, sistema/admin.
- Acesso admin nunca deve ser irrestrito.
- Acoes destrutivas, instalacoes, alteracoes de sistema, credenciais e auto-modificacao exigem aprovacao.
- Registar comandos, alteracoes, erros e acoes autonomas.
- Ter emergency lock.

## MVP Seguro

O MVP deve fazer bem isto:

1. Chat terminal com Codex auth.
2. Memoria local simples.
3. Leitura/escrita controlada em `D:\Eve`.
4. Selecionar modelo Codex.
5. Guardar diario das conversas.
6. Criar planos e ficheiros com autorizacao.
7. Executar comandos apenas depois de aprovacao.
