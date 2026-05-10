from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from computer.monitors import virtual_bounds
from computer.mouse_control import click
from computer.ocr import ocr_desktop_data, ocr_image
from computer.screen_capture import take_screenshot
from computer.ui_action_log import log_ui_action
from core.paths import LOGS_DIR, ensure_project_dirs
from learning.adaptive_learning import record_adaptive_lesson, record_skill_failure
from security.permission_manager import check_action


X_POST_CHAR_LIMIT = 280


def validate_x_post_text(post_text: str) -> dict:
    text = str(post_text or "")
    characters = len(text)
    remaining = X_POST_CHAR_LIMIT - characters
    status = "ok" if characters <= X_POST_CHAR_LIMIT else "too_long"
    return {
        "ok": status == "ok",
        "status": status,
        "characters": characters,
        "limit": X_POST_CHAR_LIMIT,
        "remaining": remaining,
    }


def fit_x_post_text(post_text: str, *, limit: int = X_POST_CHAR_LIMIT) -> dict:
    original = " ".join(str(post_text or "").split())
    if len(original) <= limit:
        return {
            "text": original,
            "status": "unchanged",
            "original_characters": len(original),
            "characters": len(original),
            "validation": validate_x_post_text(original),
        }
    suffix = "..."
    target = max(1, limit - len(suffix))
    candidate = original[:target].rstrip()
    if " " in candidate:
        candidate = candidate.rsplit(" ", 1)[0].rstrip()
    if not candidate:
        candidate = original[:target].rstrip()
    fitted = f"{candidate}{suffix}"
    if len(fitted) > limit:
        fitted = fitted[:limit]
    return {
        "text": fitted,
        "status": "auto_shortened",
        "original_characters": len(original),
        "characters": len(fitted),
        "validation": validate_x_post_text(fitted),
    }


def _ocr_contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def _composer_evidence(post_text: str) -> dict:
    observed = ocr_desktop_data()
    required_terms = [
        term.strip(".,!?;:'\"()[]{}")
        for term in post_text.split()
        if len(term.strip(".,!?;:'\"()[]{}")) >= 4
    ]
    anchor_terms = [term for term in ("Eve", "Hermes", "OpenClaw") if term.lower() in post_text.lower()]
    if len(anchor_terms) < 2:
        anchor_terms = required_terms[:4]
    anchor_entries = [
        entry
        for entry in observed["entries"]
        if any(term.lower() in entry["text"].lower() for term in anchor_terms)
    ]
    control_entries = [
        entry
        for entry in observed["entries"]
        if entry["text"].lower().strip(".,:;") in {"everyone", "reply"}
    ]
    selected_entries = observed["entries"]
    best_region = None
    best_matched_terms: list[str] = []
    best_score = None
    seed_entries = control_entries + anchor_entries
    for seed_entry in seed_entries:
        control_box = seed_entry["image_box"]
        left = max(0, control_box["left"] - 360)
        right = control_box["left"] + 980
        top = max(0, control_box["top"] - 260)
        bottom = control_box["top"] + 520
        candidate_entries = [
            entry
            for entry in observed["entries"]
            if left <= entry["image_box"]["left"] <= right and top <= entry["image_box"]["top"] <= bottom
        ]
        candidate_text = " ".join(entry["text"] for entry in candidate_entries)
        candidate_matches = [term for term in anchor_terms if term.lower() in candidate_text.lower()]
        control_count = sum(
            1
            for entry in candidate_entries
            if entry["text"].lower().strip(".,:;") in {"everyone", "reply"}
        )
        score = len(candidate_matches) * 1000 + control_count * 100 - len(candidate_entries)
        if best_score is None or score > best_score:
            best_score = score
            best_region = {"left": left, "right": right, "top": top, "bottom": bottom}
            best_matched_terms = candidate_matches
            selected_entries = candidate_entries
    combined = " ".join(entry["text"] for entry in selected_entries)
    matched_terms = [term for term in anchor_terms if term.lower() in combined.lower()]
    evidence = {
        "screenshot": observed["screenshot"],
        "has_reply_control": _ocr_contains(combined, "Everyone"),
        "has_post_text": len(matched_terms) >= max(2, min(3, len(anchor_terms))),
        "matched_terms": matched_terms,
        "anchor_terms": anchor_terms,
        "entries": selected_entries,
        "selected_entry_count": len(selected_entries),
        "cluster_score": best_score,
        "cluster_region": best_region,
        "cluster_matched_terms": best_matched_terms,
    }
    evidence["looks_like_composer"] = evidence["has_reply_control"] and evidence["has_post_text"]
    return evidence


def _find_light_button_on_composer(
    screenshot: str | Path,
    entries: list[dict],
    anchor_terms: list[str] | None = None,
) -> dict:
    image = cv2.imread(str(screenshot))
    if image is None:
        return {"found": False, "reason": "screenshot_load_failed"}
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # X dark mode uses a bright rounded button for the composer Post control.
    mask = cv2.inRange(hsv, np.array([0, 0, 170]), np.array([180, 80, 255]))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    reply_entries = [
        entry
        for entry in entries
        if entry["text"].lower().strip(".,:;") in {"everyone", "reply"}
    ]
    if reply_entries:
        left_hint = min(entry["image_box"]["left"] for entry in reply_entries)
        top_hint = min(entry["image_box"]["top"] for entry in reply_entries)
        bottom_hint = max(
            entry["image_box"]["top"] + entry["image_box"]["height"] for entry in reply_entries
        )
        region = {
            "left": max(0, left_hint + 250),
            "right": min(image.shape[1], left_hint + 760),
            "top": max(0, bottom_hint - 20),
            "bottom": min(image.shape[0], bottom_hint + 170),
        }
    elif anchor_terms:
        anchor_entries = [
            entry
            for entry in entries
            if any(term.lower() in entry["text"].lower() for term in anchor_terms)
        ]
        if anchor_entries:
            left_hint = min(entry["image_box"]["left"] for entry in anchor_entries)
            bottom_hint = max(
                entry["image_box"]["top"] + entry["image_box"]["height"] for entry in anchor_entries
            )
            region = {
                "left": max(0, left_hint + 280),
                "right": min(image.shape[1], left_hint + 900),
                "top": max(0, bottom_hint + 80),
                "bottom": min(image.shape[0], bottom_hint + 300),
            }
        else:
            region = {"left": 0, "right": image.shape[1], "top": 0, "bottom": image.shape[0]}
    else:
        region = {"left": 0, "right": image.shape[1], "top": 0, "bottom": image.shape[0]}
    candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if not (55 <= w <= 210 and 28 <= h <= 80 and area >= 1600):
            continue
        if not (region["left"] <= x <= region["right"] and region["top"] <= y <= region["bottom"]):
            continue
        candidates.append(
            {
                "image_box": {"left": x, "top": y, "width": w, "height": h},
                "area": area,
                "distance_from_composer": abs(y - region["top"]),
            }
        )
    if not candidates:
        return {"found": False, "reason": "no_light_composer_button_found"}
    chosen = sorted(candidates, key=lambda item: (item["distance_from_composer"], -item["area"]))[0]
    box = chosen["image_box"]
    bounds = virtual_bounds()
    bounds_left = bounds["left"]
    bounds_top = bounds["top"]
    chosen["global_center"] = {
        "x": bounds_left + box["left"] + box["width"] // 2,
        "y": bounds_top + box["top"] + box["height"] // 2,
    }
    chosen["found"] = True
    chosen["search_region"] = region
    return chosen


def publish_current_x_composer(post_text: str, *, approved: bool = False) -> dict:
    decision = check_action("publish_online", approved=approved)
    if not decision.allowed:
        raise PermissionError(decision.reason)
    ensure_project_dirs()
    text_validation = validate_x_post_text(post_text)
    if not text_validation["ok"]:
        result = {
            "status": "text_too_long",
            "text_validation": text_validation,
            "verification": {
                "ok": False,
                "rule": "x_post_text_must_fit_before_click",
                "reason": f"Post has {text_validation['characters']} characters; X limit is {text_validation['limit']}.",
            },
        }
        record_skill_failure(
            "x_publish_text_learning",
            "validate_x_post_length",
            "Post text was above X character limit before clicking Post.",
            str(text_validation),
        )
        log_ui_action("x_publish_current_composer", result)
        return result
    before_evidence = _composer_evidence(post_text)
    if not before_evidence["looks_like_composer"]:
        record_skill_failure(
            "x_publish_text_learning",
            "verify_composer_before_publish",
            "Composer evidence was not strong enough before publishing.",
            str({k: before_evidence[k] for k in ("has_reply_control", "has_post_text")}),
        )
        return {
            "status": "composer_not_verified",
            "before": before_evidence,
            "text_validation": text_validation,
            "verification": {"ok": False, "rule": "composer_not_verified_before_publish"},
        }
    target = _find_light_button_on_composer(
        before_evidence["screenshot"],
        before_evidence["entries"],
        before_evidence["anchor_terms"],
    )
    if not target.get("found"):
        record_skill_failure(
            "x_publish_text_learning",
            "find_post_button_visual",
            target.get("reason", "unknown"),
            "Could not locate the bright X composer Post button by visual scan.",
        )
        return {
            "status": "post_button_not_found",
            "before": before_evidence,
            "target": target,
            "text_validation": text_validation,
            "verification": {"ok": False, "rule": "post_button_not_found"},
        }
    action = click(target["global_center"]["x"], target["global_center"]["y"])
    time.sleep(6)
    after = take_screenshot("after_x_publish_current_composer", scope="all")
    after_text = ocr_image(after)
    still_composer = _ocr_contains(after_text, "Everyone can reply")
    anchor_terms = before_evidence.get("anchor_terms") or []
    matched_after_terms = [term for term in anchor_terms if term.lower() in after_text.lower()]
    post_visible = len(matched_after_terms) >= max(2, min(3, len(anchor_terms)))
    sent_toast = _ocr_contains(after_text, "Your post was sent") or (
        _ocr_contains(after_text, "post") and _ocr_contains(after_text, "sent")
    )
    status = "published" if not still_composer and (sent_toast or post_visible) else "needs_review"
    result = {
        "status": status,
        "target": target,
        "click": action,
        "after_screenshot": str(after),
        "post_visible": post_visible,
        "matched_after_terms": matched_after_terms,
        "still_composer": still_composer,
        "sent_toast": sent_toast,
        "text_validation": text_validation,
        "verification": {
            "ok": status == "published",
            "rule": "x_post_sent_and_composer_closed",
            "reason": "composer still open or published post not verified" if status != "published" else "composer closed and post/send evidence found",
        },
    }
    if status == "published":
        record_adaptive_lesson(
            "x_publish_text_learning",
            "Earlier attempts used fixed coordinates or keyboard shortcuts and did not publish.",
            "Locate the active X composer by text/reply control, detect the bright composer Post button visually, then click the detected center.",
            "For X publishing, success requires the composer to disappear and the post text to remain visible as a feed/profile post.",
        )
    else:
        record_skill_failure(
            "x_publish_text_learning",
            "verify_publish_result",
            "Post click did not satisfy final verification.",
            str({"post_visible": post_visible, "still_composer": still_composer}),
        )
    log_ui_action("x_publish_current_composer", result)
    return result


def log_x_learning_note(content: str) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "browser" / "x_learning_notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## x_publish_text_learning\n\n{content.strip()}\n")
    return path
