from __future__ import annotations

from runtime_validation_lib import check, finalize

from memory.learning_taxonomy import classify_learning_item
from memory.learning_validator import repair_misfiled_learning, validate_target_folder


def main() -> dict:
    examples = {
        "world": "Noticia mundial sobre ciencia e sociedade",
        "technology": "OpenAI publicou paper sobre agent memory benchmark",
        "sandro": "Sandro prefere anime e treino",
        "personality": "Eu gosto de narrativa procedural",
        "project": "Projeto RPG Maker no repo da Eve",
    }
    classifications = {target: classify_learning_item(text) for target, text in examples.items()}
    repaired = repair_misfiled_learning([{"text": examples["technology"], "target": "personality"}])
    checks = [
        check(f"{target} classified correctly", got == target, {"text": examples[target], "got": got}, critical=target in {"technology", "personality", "sandro"})
        for target, got in classifications.items()
    ]
    checks.append(check("validator detects misfiled technology/personality mix", repaired[0]["misfiled"] and repaired[0]["suggested_target"] == "technology", repaired, critical=True))
    checks.append(check("validate_target_folder accepts correct target", validate_target_folder(examples["technology"], "technology")["valid"], examples["technology"]))
    return finalize("point_13_learning_separation_runtime", "Point 13 Learning Separation Runtime", "point_13_learning_separation_runtime.md", checks)


if __name__ == "__main__":
    main()
