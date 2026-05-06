# Eve Requirements Gap - 2026-05-06

## Estado geral

A Eve tem uma fundacao funcional ate v1.0, mas ainda nao e uma agente madura. A maior parte dos requisitos existe como modulo base, comando, fluxo ou scaffold seguro. O que falta principalmente e profundidade: execucao autonoma real em background, OCR operacional, memoria vetorial, skills robustas para apps reais, testes automaticos e refinamento de controlo visual.

## Feito

- Chat terminal com OAuth Codex/OpenAI proprio.
- Selecao manual de modelo Codex.
- Pasta propria em D:\Eve.
- Diario e logs de conversa.
- Memoria curta/media/longa simples em ficheiros.
- Consolidacao manual e sistema de sonho inicial.
- Leitura/escrita controlada no workspace.
- Terminal com logs e guards.
- Rollback de ficheiros da Eve antes de alteracoes relevantes.
- Registo de erros.
- Skills em JSON, execucao de skills e learn-mode textual inicial.
- Awareness temporal/sistema/janela ativa/processos.
- Deteccao real de 3 monitores e screenshot global.
- Controlo de rato/teclado com screenshots antes/depois.
- Emergency lock.
- Browser humano basico por URL/pesquisa visivel.
- Rascunhos Gmail sem envio.
- Agenda local em ficheiro.
- Proatividade base com propostas de baixo risco.
- Workspace watcher.
- Personalidade/preferencias evolutivas em ficheiro.
- Research notes para mundo/tecnologia.
- Lab com experiencias e candidate improvements.
- Sandbox tester via py_compile.
- Admin gate e executor admin aprovado.
- Switch de modos de seguranca, incluindo unrestricted_mode.
- App observer inicial.
- Recursive self-improvement controlado: propoe/testa/regista sem alterar core livremente.

## Parcial

- Memoria semantica/vetorial: existe placeholder, falta Chroma/embeddings reais.
- Consolidacao varias vezes por dia: existe comando, falta scheduler automatico real.
- Sistema de sonhos: existe relatorio inicial, falta ciclo autonomo periodico mais inteligente.
- Proatividade: existe decisor simples, falta daemon/servico que execute sem input.
- Aprendizagem por demonstracao: existe formato textual, falta gravar cliques/teclas/screenshots automaticamente.
- Aprendizagem adaptativa: regista falhas/licoes, falta alterar skills automaticamente com testes.
- Browser como humano: abre URL/pesquisa, falta navegar por OCR, clicar elementos e preencher fluxos complexos.
- Email como assistente humano: cria rascunho, falta fluxo visual robusto em Gmail e anexos.
- Qualquer app do PC: app observer existe, falta mapa visual e skills por app.
- Admin total: modo unrestricted existe, mas ainda depende do processo/sessao atual e nao cria elevacao UAC automatica madura.
- Self-rewrite: core_updater existe, falta pipeline completo patch -> teste -> rollback -> aplicar por risco.
- Pesquisa diaria: notas existem, falta web watcher autonomo com fontes reais.
- Personalidade propria: ficheiros existem, falta motor que influencie decisoes de forma consistente.

## Falta

- Instalar/configurar tesseract.exe para OCR real.
- OCR com coordenadas robustas por monitor depois do Tesseract estar operacional.
- Servico/Tarefa Windows para scheduler real.
- Memoria vetorial com embeddings.
- Test suite automatica.
- Interface terminal melhorada/dashboard.
- Voz e comandos por fala.
- Notificacoes.
- Ligacao ao telemovel.
- Pesquisa real diaria na internet com classificacao para lab.
- Skill recorder real por demonstracao visual.
- Browser/app automation com verificacao visual antes/depois por objetivo.
- Politica de risco mais fina para unrestricted_mode, admin_mode e self-modify.
- Sistema de rollback completo por versao/branch alem de backup de ficheiros.
- Benchmarks do lab.
- Evolucao continua realmente recorrente, nao apenas comandos manuais.

## Proxima prioridade

1. Instalar Tesseract OCR.
2. Validar OCR por monitor com coordenadas globais.
3. Criar executor visual: observar -> localizar alvo -> agir -> verificar.
4. Criar scheduler real em Windows para consolidacao, sonho e research.
5. Implementar memoria vetorial.
