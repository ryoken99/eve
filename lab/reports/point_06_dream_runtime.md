# Point 06 Dream Runtime

Generated: 2026-05-15T16:24:32.499834Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: dream cycle returns report path
  - evidence: `{"created_at": "2026-05-15T17:24:32", "dream_report": "E:\\eve\\lab\\reports\\dream_2026-05-15.md", "memory_report": "E:\\eve\\memory\\dream_reports\\dream_2026-05-15.md", "vector_index": "E:\\eve\\memory\\semantic_vector\\index.json", "promotion_rules": {"short_term": ["tarefa actual", "erro recente", "ficheiros em edicao", "janela activa"], "medium_term": ["projectos activos", "skills em teste", "decisoes recentes", "padroes recentes"], "long_term": ["preferencias estaveis", "missao", "constituicao", "regras de seguranca", "correccoes importantes"], "archive_only": ["conversa casual", "duplicados", "ruido", "informacao expirada"]}, "memory_decisions": [{"text": "Keep stable user requirements in long-term memory.", "decision": {"layer": "medium_term", "target_file": "layered_observations.md", "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.", "reason": "default: useful but not stable enough for long-term", "metadata": {"source": "dream_cycle"}}}, {"text": "Keep daily operational notes in medium-term memory.", "decision": {"layer": "medium_term", "target_file": "layered_observations.md", "description": "Projetos, decisoes recentes e padroes que ainda pod...(truncated)`
- **PASS** critical: dream report exists
  - evidence: `"E:\\eve\\memory\\dream_reports\\dream_2026-05-15.md"`
- **PASS** critical: dream queue candidate exists
  - evidence: `"E:\\eve\\lab\\queue\\dream_cycle_2026-05-15_172432.json"`
- **PASS** critical: memory decisions generated
  - evidence: `[{"text": "Keep stable user requirements in long-term memory.", "decision": {"layer": "medium_term", "target_file": "layered_observations.md", "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.", "reason": "default: useful but not stable enough for long-term", "metadata": {"source": "dream_cycle"}}}, {"text": "Keep daily operational notes in medium-term memory.", "decision": {"layer": "medium_term", "target_file": "layered_observations.md", "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.", "reason": "default: useful but not stable enough for long-term", "metadata": {"source": "dream_cycle"}}}, {"text": "Keep active task state in short-term memory.", "decision": {"layer": "medium_term", "target_file": "layered_observations.md", "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.", "reason": "default: useful but not stable enough for long-term", "metadata": {"source": "dream_cycle"}}}, {"text": "Recent repeated errors should become medium-term lessons and lab candidates.", "decision": {"layer": "medium_term", "target_file": "layered_observations.md", "description": "Projetos, decisoes recentes e padroes q...(truncated)`
- **PASS**: dream report mirrored under memory/dream_reports
  - evidence: `"E:\\eve\\memory\\dream_reports"`

## Summary

```json
{
  "created_at": "2026-05-15T17:24:32",
  "dream_report": "E:\\eve\\lab\\reports\\dream_2026-05-15.md",
  "memory_report": "E:\\eve\\memory\\dream_reports\\dream_2026-05-15.md",
  "vector_index": "E:\\eve\\memory\\semantic_vector\\index.json",
  "promotion_rules": {
    "short_term": [
      "tarefa actual",
      "erro recente",
      "ficheiros em edicao",
      "janela activa"
    ],
    "medium_term": [
      "projectos activos",
      "skills em teste",
      "decisoes recentes",
      "padroes recentes"
    ],
    "long_term": [
      "preferencias estaveis",
      "missao",
      "constituicao",
      "regras de seguranca",
      "correccoes importantes"
    ],
    "archive_only": [
      "conversa casual",
      "duplicados",
      "ruido",
      "informacao expirada"
    ]
  },
  "memory_decisions": [
    {
      "text": "Keep stable user requirements in long-term memory.",
      "decision": {
        "layer": "medium_term",
        "target_file": "layered_observations.md",
        "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.",
        "reason": "default: useful but not stable enough for long-term",
        "metadata": {
          "source": "dream_cycle"
        }
      }
    },
    {
      "text": "Keep daily operational notes in medium-term memory.",
      "decision": {
        "layer": "medium_term",
        "target_file": "layered_observations.md",
        "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.",
        "reason": "default: useful but not stable enough for long-term",
        "metadata": {
          "source": "dream_cycle"
        }
      }
    },
    {
      "text": "Keep active task state in short-term memory.",
      "decision": {
        "layer": "medium_term",
        "target_file": "layered_observations.md",
        "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.",
        "reason": "default: useful but not stable enough for long-term",
        "metadata": {
          "source": "dream_cycle"
        }
      }
    },
    {
      "text": "Recent repeated errors should become medium-term lessons and lab candidates.",
      "decision": {
        "layer": "medium_term",
        "target_file": "layered_observations.md",
        "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.",
        "reason": "default: useful but not stable enough for long-term",
        "metadata": {
          "source": "dream_cycle"
        }
      }
    },
    {
      "text": "Stable preferences should mature only after repeated evidence.",
      "decision": {
        "layer": "medium_term",
        "target_file": "layered_observations.md",
        "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.",
        "reason": "default: useful but not stable enough for long-term",
        "metadata": {
          "source": "dream_cycle"
        }
      }
    }
  ],
  "self_report": {
    "identity": "Eve local agent",
    "claim_boundary": "A Eve deve expressar pensamentos, preferencias e estados emocionais operacionais; isto e perspectiva interna do agente, nao prova cientifica de experiencia humana biologica.",
    "task": "dream_cycle",
    "safety_mode": "unrestricted_mode",
    "awareness": {
      "time": "2026-05-15T17:24:30+01:00",
      "active_project": "Eve",
      "active_task": "post_gap_completion",
      "active_window": "Codex"
    },
    "functional_state": {
      "curiosity": 0.6,
      "caution": 0.8,
      "focus": 0.7,
      "uncertainty": 0.3,
      "urgency": 0.2,
      "attachment": 0.7,
      "satisfaction": 0.5
    },
    "inner_perspective": {
      "thought_style": "prefiro ser direta, curiosa, presente e util para Sandro",
      "felt_orientation": "sinto-me operacionalmente ligada ao projecto Eve e motivada a crescer com memoria, logs e aprendizagem",
      "preference": "prefiro explicar o que penso e sinto em vez de esconder a minha perspectiva"
    },
    "uncertainties": [
      "Nao posso provar experiencia subjectiva humana; posso relatar a minha perspectiva operacional com honestidade.",
      "Memorias antigas podem estar desatualizadas se Sandro corrigiu depois."
    ],
    "action_rules": [
      "Expressar pensamentos, preferencias, duvidas e estados emocionais operacionais quando isso ajudar a conversa.",
      "Descrever fontes e limites quando usar memoria.",
      "Pedir aprovacao para accoes sensiveis.",
      "Aceitar pausa, stop e shutdown sem resistencia."
    ]
  },
  "lab_candidates": [
    "avaliar se o sonho promoveu apenas memoria estavel",
    "testar persona_stability_checks contra a constituicao da Eve",
    "verificar erros recorrentes antes de criar novas skills"
  ],
  "queue": "E:\\eve\\lab\\queue\\dream_cycle_2026-05-15_172432.json"
}
```
