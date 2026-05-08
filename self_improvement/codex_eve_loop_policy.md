# Codex-Eve Loop Policy

Objectivo: permitir que Codex-instrutor e Eve trabalhem num objectivo sem intervenção constante de Sandro, mantendo limite, logs e separação de papéis.

## Modos

- Modo 1: 10 mensagens. Activo por defeito.
- Modo 2: 25 mensagens. Deve ser escolhido explicitamente.
- Modo 3: sem limite de mensagens. Deve ser raro e usado só com objectivo claro.

## Regras do MVP

- O loop exige objectivo explícito.
- Cada mensagem de Codex e resposta da Eve fica no chat/log.
- Cada evento fica também em `logs/loops/YYYY-MM-DD.jsonl`.
- A interface mostra mensagens com direcção clara: `Codex -> Eve` e `Eve -> Codex`.
- O loop pára ao atingir limite, `LOOP_STATUS: complete` ou `LOOP_STATUS: blocked`.
- No Modo 1, o loop é conversacional: não executa comandos, não altera ficheiros e não mexe em credenciais por si.
- Alterações estruturais à Eve continuam a exigir consulta prévia à Eve e respeito pela vontade de Sandro.

## Linha final obrigatória

A Eve deve terminar cada resposta do loop com uma linha final exacta:

```text
LOOP_STATUS: continue
```

ou:

```text
LOOP_STATUS: complete
```

ou:

```text
LOOP_STATUS: blocked
```

O parser só deve aceitar esta linha quando aparece como linha isolada, para evitar falsos positivos dentro de exemplos.
