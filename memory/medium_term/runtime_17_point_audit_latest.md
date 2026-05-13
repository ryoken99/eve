# Runtime 17-Point Audit

Timestamp: 2026-05-13T22:29:16.796713Z
Average score: 9.04/10

## 1. Permissoes elevadas/admin: 9.0/10
- Evidence: admin status callable, admin session temporaria criada, allowlist permite comando esperado, allowlist bloqueia comando perigoso
- Limitations: processo nao esta elevado neste runtime, falhou: processo atual esta elevado

## 2. Diario completo das conversas: 9.4/10
- Evidence: transcript chat validavel, hash chain implementada, canais transcript existem
- Limitations: hash chain antiga pode marcar entradas pre-existentes sem hash

## 3. Consolidacao diaria varias vezes por dia: 9.6/10
- Evidence: daemon heartbeat existe, consolidation parser extrai categorias, cron executou sem erros, schedule 6h presente
- Limitations: none

## 4. Memoria curta/media/longa: 9.4/10
- Evidence: camadas existem, memoria registra metadata, promocao funciona, expiracao/arquivo funciona
- Limitations: none

## 5. Memoria semantica/vectorial: 8.8/10
- Evidence: indice semantico responde, chunk/metadata disponivel, fallback local disponivel, backend embeddings neural real disponivel
- Limitations: none

## 6. Sistema de sonhos: 8.8/10
- Evidence: sonho multi-fonte cria ligacoes, sonho gera lab candidates, avaliador de sonho pontua qualidade, dream reports existem
- Limitations: none

## 7. Awareness temporal/situacional/espacial: 8.9/10
- Evidence: awareness coleta hora/sistema, active window observado, environment_state captura browser/uia, UI Automation real disponivel
- Limitations: none

## 8. Vontade/gostos/personalidade evolutiva: 8.6/10
- Evidence: preferencia inicia candidate, preferencia reforca, preferencia estabiliza por evidencia, memoria personality existe
- Limitations: maturacao ainda e evidencia/contador, nao avaliacao profunda

## 9. Lab proprio: 8.9/10
- Evidence: lab comparison aceita melhoria medida, lab dirs existem, candidate improvements existem, experiencia runtime persistida com metrica
- Limitations: none

## 10. Registo de erros e terminal: 9.5/10
- Evidence: error transcript dir existe, terminal transcript dir existe, erro vira proposta de teste, logs errors existem
- Limitations: none

## 11. Pesquisa diaria de tecnologia: 8.8/10
- Evidence: research scoring funciona, daily research schedule no heartbeat, prompt jobs executaram sem login/codex erro, pesquisa web runtime buscou fonte externa
- Limitations: none

## 12. Pesquisa enviada para lab: 8.8/10
- Evidence: research vira candidate com metrica, candidate tem rollback, candidate tem expected_gain, probe real gerou candidate lab-ready
- Limitations: none

## 13. Aprendizagem mundo/tecnologia separada: 8.7/10
- Evidence: tecnologia classificada corretamente, world daily existe, technology daily existe, personality daily existe
- Limitations: none

## 14. Melhoria autonoma do sistema: 8.8/10
- Evidence: safe ARSI permitido, high risk bloqueado sem aprovacao, autonomy heartbeat criou/executou missao, ARSI safe cycle aplicou melhoria medida
- Limitations: melhoria medium/high continua a exigir humano

## 15. Controlo browser/UI humano: 9.5/10
- Evidence: Eve web local responde, Playwright instalado/disponivel, Playwright DOM smoke test real passou, UIA instalado/disponivel, OCR dependency instalada, pyautogui instalado, permissoes por app bloqueiam submit sensivel
- Limitations: Tesseract OCR executavel nao esta disponivel, falhou: Tesseract OCR executavel disponivel

## 16. ARSI - Autonomous Recursive Self Improvement: 9.0/10
- Evidence: safe changes autonomas permitidas, high risk exige aprovacao, verified updates dir existe, ARSI policy summary existe, ARSI safe cycle executa com medicao
- Limitations: ARSI medium/high-risk continua controlado por aprovacao

## 17. Autonomia/proatividade sem input: 9.1/10
- Evidence: daemon heartbeat existe, autonomy executed missions no heartbeat, priority engine pontua missoes, budget engine funciona, cron/prompt sem falhas
- Limitations: none
