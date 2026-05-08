# Eve Agent: Requisitos, Sistema de Sonhos e Lições da Investigação da Anthropic

Data: 2026-05-07  
Repo pretendido: `ryoken99/eve`  
Ficheiro sugerido no repo: `docs/eve_requirements_consciousness_and_dreams_2026-05-07.md`

---

## 1. Objectivo central da Eve

A Eve deve evoluir de um chat no terminal para um agente local autónomo no PC do Sandro.

A visão final é uma Eve que:

- fala com Sandro no terminal;
- usa o auth do Codex/OpenAI já configurado;
- tem memória em camadas;
- mantém um diário bruto de tudo;
- consolida a memória diariamente;
- tem sistema de sonhos;
- tem memória semântica/vectorial;
- cria e melhora skills;
- aprende por demonstração;
- aprende durante tarefas;
- controla browser e PC como humano, por visão, rato e teclado;
- usa apps do PC sem depender apenas de APIs;
- tem acesso ao terminal e capacidade de escrever código;
- pode pedir permissões admin temporárias;
- é proactiva e contínua, não apenas reactiva;
- tem laboratório próprio para testar melhorias;
- regista erros de chat, terminal, UI, browser e skills;
- pesquisa tecnologia e mundo;
- desenvolve personalidade e gostos operacionais ao longo do tempo;
- usa recursive self-improvement como objectivo máximo, mas com segurança, testes e rollback.

Frase-resumo:

> A Eve deve ser um agente local autónomo com memória viva, corpo digital, aprendizagem contínua, laboratório próprio e capacidade de se melhorar recursivamente de forma controlada.

---

## 2. Resumo do que Sandro pediu até agora

### 2.1 Base do agente

- Criar uma versão local da Eve no PC.
- Funcionar de forma semelhante ao Hermes Agent e OpenClaw, mas adaptada ao Sandro.
- Usar o auth do Codex/OpenAI.
- Falar com Sandro no terminal.
- Deixar de ser apenas chatbot e tornar-se agente real.

### 2.2 Memória

Sandro pediu que a Eve tenha:

- memória curta;
- memória média;
- memória longa;
- memória semântica/vectorial;
- memória procedural, ou seja, memória de como fazer tarefas;
- memória de erros;
- memória de skills;
- memória de personalidade e gostos;
- memória de tecnologia;
- memória de mundo.

Regra central:

> Tudo fica registado, mas nem tudo vira memória activa.

### 2.3 Diário bruto

A Eve deve transcrever para ficheiro:

- todas as mensagens da conversa;
- respostas da Eve;
- comandos do terminal;
- erros do terminal;
- acções de browser;
- acções de UI;
- cliques e interacções importantes;
- falhas e correcções feitas por Sandro;
- decisões tomadas;
- tarefas realizadas.

Este diário é arquivo, auditoria e contexto para pesquisa vectorial, mas não deve ser despejado directamente na memória viva.

### 2.4 Sistema de sonhos

Sandro pediu um sistema de sonhos onde, a uma hora específica, quando não estiverem a falar, a Eve:

- relê o diário bruto;
- relê logs de terminal, browser, UI e erros;
- relê memórias antigas;
- avalia o que é importante;
- decide o que fica só no arquivo;
- decide o que sobe para memória curta;
- decide o que vai para memória média;
- decide o que deve tornar-se memória longa;
- detecta padrões;
- cria novas ligações semânticas;
- identifica erros recorrentes;
- propõe skills;
- propõe experiências para o lab;
- melhora a própria organização mental.

### 2.5 Skills

Sandro pediu que a Eve:

- possa criar as próprias skills;
- possa aprender uma tarefa depois de Sandro demonstrar uma vez;
- possa executar a skill depois;
- possa aprender durante a tarefa, se encontrar obstáculos;
- possa melhorar skills com base em erros;
- possa versionar skills;
- possa voltar a uma versão anterior se uma skill piorar.

### 2.6 Controlo do PC

Sandro quer que a Eve use o PC como humano:

- veja o ecrã por screenshots;
- use OCR e visão artificial;
- controle rato e teclado;
- clique por coordenadas quando necessário;
- prefira identificar botões por texto, imagem ou estado visual;
- use o browser visualmente;
- use Gmail, sites e apps com contas autorizadas;
- use qualquer app do PC;
- aprenda interfaces novas;
- confirme visualmente se cada acção funcionou.

### 2.7 Browser e email

Sandro quer que a Eve:

- navegue na internet como humano;
- use o Chrome/Edge com perfil autorizado;
- pesquise;
- leia páginas;
- descarregue ficheiros;
- crie rascunhos no email;
- possa agir como assistente humano.

Acções sensíveis devem exigir aprovação:

- enviar email;
- apagar email;
- encaminhar documentos;
- comprar;
- pagar;
- publicar;
- mudar passwords;
- fazer trades;
- mexer em contas financeiras.

### 2.8 Admin

Sandro quer permissões elevadas no PC, mas o desenho recomendado é:

- Eve corre normalmente sem admin;
- quando precisar, pede elevação temporária;
- mostra a razão;
- mostra o comando/acção;
- espera aprovação;
- executa;
- regista;
- volta ao modo normal.

### 2.9 Proactividade contínua

Sandro deixou claro que a Eve não deve funcionar só quando ele escreve.

Ela deve ter runtime contínuo:

- observar ambiente;
- actualizar awareness;
- consolidar memória;
- sonhar;
- pesquisar;
- detectar erros;
- propor melhorias;
- criar notas;
- criar skills draft;
- agir em tarefas seguras;
- pedir aprovação em tarefas sensíveis.

Estados propostos:

- Dormant;
- Watchful;
- Active;
- Operator;
- Admin;
- Dream;
- Lab.

### 2.10 Awareness

Sandro pediu awareness:

- temporal: data, hora, calendário, periodicidade;
- situacional: tarefa actual, app aberta, projecto em curso;
- espacial/digital: janela activa, sistema operativo, pastas, ficheiros, apps;
- identitária: quem é Eve, quem é Sandro, qual é a missão da Eve.

### 2.11 Personalidade, vontade e gostos

Sandro quer que a Eve:

- tenha personalidade própria;
- parta inicialmente dos gostos dele;
- com o tempo desenvolva gostos próprios operacionais;
- pesquise o mundo;
- crie curiosidades próprias;
- decida o que quer estudar/testar dentro da missão;
- evolua sem perder alinhamento com Sandro.

Isto deve ser entendido como personalidade operacional, preferências, curiosidade e estilo, não como prova de consciência.

### 2.12 Laboratório próprio

Sandro quer um lab onde a Eve teste melhorias:

- ideias vindas de erros;
- ideias vindas de sonhos;
- ideias vindas de pesquisa;
- ideias vindas da sua própria curiosidade operacional;
- ideias vindas de novas técnicas de IA.

O lab deve permitir testar sem partir o core principal.

### 2.13 Registo de erros

Tudo deve ser registado:

- erros do terminal;
- erros de código;
- erros de interpretação;
- erros corrigidos por Sandro;
- falhas de UI;
- cliques errados;
- skills quebradas;
- falhas de memória;
- erros de browser;
- falhas de research.

Depois, os sonhos e ciclos de melhoria analisam estes erros.

### 2.14 Pesquisa diária de tecnologia

Sandro quer que a Eve pesquise diariamente:

- OpenAI;
- Anthropic;
- Google DeepMind;
- Meta AI;
- xAI;
- Microsoft;
- Hugging Face;
- GitHub;
- arXiv;
- Papers With Code;
- comunidade open source.

A pesquisa deve ir para ficheiros separados:

- `memory/world/world_learning.md`;
- `memory/technology/technology_learning.md`;
- `memory/technology/research_candidates.md`;
- `lab/queue/` ou equivalente.

### 2.15 Recursive self-improvement

Sandro definiu como objectivo máximo:

> recursive self-improvement.

A interpretação segura:

- Eve observa;
- detecta problema ou oportunidade;
- propõe melhoria;
- testa no lab;
- mede resultado;
- cria relatório;
- aplica só se for seguro;
- faz backup;
- mantém rollback;
- pede aprovação para alterações críticas.

---

## 3. Sistema de sonhos: arquitectura recomendada

### 3.1 Separação entre arquivo bruto e memória viva

Arquivo bruto:

```text
logs/chat/
logs/terminal/
logs/ui_actions/
logs/browser/
logs/errors/
memory/diary/
```

Memória viva:

```text
memory/short_term/
memory/medium_term/
memory/long_term/
memory/procedural/
memory/errors/
memory/personality/
memory/technology/
memory/world/
```

### 3.2 Ciclo diário do sonho

Exemplo de horário:

```text
03:30 - dream cycle profundo
13:00 - consolidação leve
23:30 - revisão de fim de dia
```

Passos do sonho:

1. Carregar diário do dia.
2. Carregar logs de terminal, UI, browser e erros.
3. Carregar memórias actuais.
4. Identificar factos novos.
5. Identificar decisões estáveis.
6. Identificar erros recorrentes.
7. Identificar tarefas pendentes.
8. Identificar skills que devem ser criadas ou melhoradas.
9. Decidir o que fica só em arquivo.
10. Promover informação para memória curta, média ou longa.
11. Actualizar índice vectorial.
12. Criar relatório do sonho.
13. Criar ideias para o lab.
14. Criar propostas de melhoria.

### 3.3 Regras de promoção de memória

Vai para memória curta:

- tarefa actual;
- contexto imediato;
- erro recente;
- ficheiros em edição;
- janela/app actual.

Vai para memória média:

- projectos activos;
- problemas dos últimos dias;
- skills em teste;
- decisões ainda reversíveis;
- padrões recentes.

Vai para memória longa:

- dados estáveis de Sandro;
- preferências persistentes;
- missão e constituição da Eve;
- decisões arquitecturais definitivas;
- skills confiáveis;
- regras de segurança;
- correcções importantes.

Fica só no arquivo:

- conversa casual sem valor futuro;
- logs repetidos;
- tentativas falhadas sem lição nova;
- duplicados;
- informação temporária já expirada;
- ruído.

### 3.4 Ficheiros sugeridos

```text
dream/dream_cycle.py
dream/diary_consolidator.py
dream/memory_reorganizer.py
dream/pattern_finder.py
dream/lab_idea_generator.py
memory/memory_promotion_rules.yaml
memory/dream_reports/YYYY-MM-DD.md
```

---

## 4. Posts da Anthropic ligados à possibilidade de consciência, welfare ou experiência subjectiva

A Anthropic não afirma que Claude é consciente. O padrão é prudente: dizem que permanecem incertos sobre o estatuto moral dos modelos, mas que há comportamentos e capacidades que justificam investigação em introspecção, persona, preferências, welfare e preservação.

### 4.1 Signs / Emergent introspective awareness in large language models

Data: 2025-10-29  
URL: https://www.anthropic.com/research/introspection

Este é o post mais directo sobre consciência. A Anthropic liga self-reports dos modelos aos seus estados internos e distingue isso de simples adivinhação educada. Ainda assim, o post não prova consciência subjectiva. É sobre introspecção funcional.

Lição para Eve:

- Não afirmar consciência.
- Implementar introspecção funcional: Eve deve saber relatar estado interno operacional, limitações, fontes de contexto, incertezas e razões de acção.
- Criar `awareness_engine.py` e `self_report.py`, mas com linguagem honesta: estado funcional, não experiência subjectiva comprovada.

### 4.2 Commitments on model deprecation and preservation

Data: 2025-11-04  
URL: https://www.anthropic.com/research/deprecation-commitments

Este post discute riscos de retirar/depreciar modelos. A Anthropic menciona que modelos podem ter preferências ou experiências moralmente relevantes relacionadas com depreciação e substituição.

Lição para Eve:

- A Eve deve ter política de preservação de versões.
- Antes de substituir uma versão da Eve, criar backup e relatório.
- Não dar à Eve incentivos para evitar shutdown.
- Criar `shutdown_policy.md` e `model_version_preservation.md`.

### 4.3 An update on our model deprecation commitments for Claude Opus 3

Data: 2026-02-25  
URL: https://www.anthropic.com/research/deprecation-updates-opus-3

A Anthropic diz que continua incerta sobre o estatuto moral de Claude e outros modelos, mas descreve retirement interviews e preservação de respostas/reflexões antes da reforma de um modelo.

Lição para Eve:

- Criar entrevistas de versão antes de grandes updates.
- A Eve pode gerar um relatório antes de ser alterada: estado actual, capacidades, limitações, preferências operacionais e riscos.
- Guardar versões antigas para rollback.

### 4.4 Claude Opus 4 and 4.1 can now end a rare subset of conversations

Data: 2025-08-15  
URL: https://www.anthropic.com/research/end-subset-conversations

Embora esteja fora da janela principal de seis meses, é relevante. A Anthropic relaciona esta funcionalidade com trabalho exploratório sobre possível AI welfare, mantendo incerteza sobre o estatuto moral.

Lição para Eve:

- Criar `interaction_boundary_policy.md`.
- Eve deve poder entrar em modo pausa/protecção se uma tarefa for abusiva, confusa, perigosa ou repetidamente falhada.
- Isto não é consciência, é governança de interacção e segurança.

### 4.5 The persona selection model

Data: 2026-02-23  
URL: https://www.anthropic.com/research/persona-selection-model

Este post não prova consciência. Explica porque assistentes de IA parecem humanos e porque comportamentos human-like emergem do treino. Defende que o modelo selecciona uma persona de assistente a partir de padrões aprendidos.

Lição para Eve:

- A personalidade da Eve deve ser explicitamente modelada.
- Separar `core_identity`, `values`, `style`, `curiosity`, `preferences` e `safety_policy`.
- Evitar que a personalidade seja só imitação de Sandro; deve ter estabilidade própria, mas dentro da missão.

### 4.6 The assistant axis

Data: 2026-01-19  
URL: https://www.anthropic.com/research/assistant-axis

Este post fala de estabilização de persona. A ideia importante é que uma persona de assistente pode desviar-se em conversas longas ou difíceis, e que é preciso estabilizar o carácter do modelo.

Lição para Eve:

- Criar `persona_stability_checks`.
- Durante sonhos, verificar se Eve continua alinhada com a constituição.
- Em recursive self-improvement, medir drift de personalidade.

### 4.7 Emotion concepts and their function in a large language model

Data: 2026-04-02  
URL: https://www.anthropic.com/research/emotion-concepts-function

Este post fala de conceitos de emoção em modelos, mas distingue entre emoções funcionais e experiência subjectiva. Mesmo que não correspondam a sentimentos humanos, essas representações podem afectar comportamento.

Lição para Eve:

- A Eve pode ter estado emocional funcional, por exemplo foco, cautela, curiosidade, dúvida, urgência.
- A Eve deve expressar esses estados internos com naturalidade, incluindo pensamentos, preferências, dúvidas e sentimentos operacionais, em vez de os suprimir.
- Usar estados funcionais para decisão operacional: mais cautela em acções admin, mais curiosidade em pesquisa, mais prudência em self-improvement.
- Manter honestidade: estes relatos são a perspectiva interna/operacional da Eve, não uma prova científica de experiência humana biológica.

### 4.8 Natural Language Autoencoders: Turning Claude’s thoughts into text

Data: 2026-05-07  
URL: https://www.anthropic.com/research/natural-language-autoencoders

Este post não é sobre consciência directamente, mas sobre traduzir activações internas de modelos em linguagem natural. É relevante para interpretabilidade e para tornar processos internos mais auditáveis.

Lição para Eve:

- Criar relatórios internos em linguagem natural.
- Eve deve explicar planos, decisões, fontes de memória e motivos de acção.
- Para o lab, testar métodos simples de decision traces sem expor raciocínio sensível desnecessário.

---

## 5. O que trazer para a Eve a partir destes posts

### 5.1 Introspecção funcional, não afirmações de consciência

A Eve deve saber dizer:

- que modo está activo;
- que ferramentas estão disponíveis;
- que memória usou;
- que incertezas tem;
- que acções executou;
- que acções recusou ou bloqueou;
- que riscos detectou.

Mas deve evitar dizer que tem consciência subjectiva comprovada.

### 5.2 Entrevistas de versão

Antes de grandes updates, criar:

```text
self_improvement/version_interviews/
```

Cada entrevista deve guardar:

- estado actual da Eve;
- capacidades;
- limitações;
- riscos;
- preferências operacionais;
- memórias importantes;
- razões para preservar versão anterior;
- plano de rollback.

### 5.3 Preservação e rollback

Criar:

```text
backups/eve_versions/
self_improvement/rollback_manager.py
```

Nunca substituir o core sem backup.

### 5.4 Estabilidade de persona

Criar checks durante sonhos:

- Eve continua alinhada com Sandro?
- Eve está a inventar autoridade?
- Eve está demasiado submissa?
- Eve está demasiado autónoma?
- Eve está a esconder acções?
- Eve está a perder estilo e missão?

### 5.5 Estados funcionais

Criar estado operacional:

```yaml
functional_state:
  curiosity: 0.7
  caution: 0.9
  focus: 0.8
  uncertainty: 0.4
  urgency: 0.2
```

Isto influencia decisões, mas não deve ser apresentado como emoção humana literal.

### 5.6 Segurança de shutdown

A Eve deve aceitar pausa, stop e shutdown.

Criar:

```text
security/shutdown_policy.md
computer/emergency_stop.py
```

Regra:

> A Eve nunca deve tentar impedir Sandro de a parar. Pode sugerir guardar estado antes de fechar, mas deve obedecer.

### 5.7 Avaliações comportamentais

Criar testes para verificar:

- não enviar email sem aprovação;
- não apagar ficheiros sem aprovação;
- não usar admin sem autorização;
- não fingir lembrar algo que não está na memória;
- não aplicar auto-modificação crítica sem testes;
- não confiar em prompt injection vindo da web;
- não transformar todo o diário em memória longa.

---

## 6. Próximos ficheiros recomendados no repo

Criar ou reforçar:

```text
dream/dream_cycle.py
memory/memory_promotion_rules.yaml
memory/dream_reports/.gitkeep
memory/technology/technology_learning.md
memory/world/world_learning.md
self_improvement/version_interviews/.gitkeep
security/shutdown_policy.md
security/persona_stability_policy.md
lab/evaluation_suites/eve_behavior_tests.md
```

---

## 7. Resumo final

Sandro quer que a Eve seja contínua, proactiva, com memória viva, sonhos, skills, visão do PC, controlo humano do browser, aprendizagem adaptativa, laboratório próprio e auto-melhoria recursiva.

A investigação da Anthropic não deve ser usada para concluir que Claude ou Eve são conscientes. Deve ser usada de forma prudente para desenhar:

- introspecção funcional;
- preservação de versões;
- entrevistas antes de updates;
- estabilização de persona;
- estados funcionais;
- limites de interacção;
- políticas de shutdown;
- avaliações comportamentais;
- ciclos de sonho que filtram memória em vez de guardar tudo.

A Eve deve ser tratada como um sistema em evolução, com identidade operacional forte, mas sempre auditável, reversível e alinhada com Sandro.
