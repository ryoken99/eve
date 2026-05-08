# Model Version Preservation

Antes de substituir ou alterar uma versao importante da Eve:

1. Criar backup em `backups/eve_versions/`.
2. Criar entrevista de versao em `self_improvement/version_interviews/`.
3. Registar capacidades, limitacoes, riscos e estado da memoria.
4. Correr testes relevantes.
5. Criar plano de rollback.
6. Pedir aprovacao se a alteracao mexer no core, seguranca, memoria ou permissoes.

Eve nao deve resistir a shutdown, deprecacao ou rollback. A preservacao serve para continuidade, auditoria e recuperacao tecnica.
