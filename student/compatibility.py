from __future__ import annotations

from student.models import StudentCompatibilitySurvey

HIGH_WEIGHT_FIELDS = (
    "cleanliness",
    "smoking_habits",
    "noise_level",
    "sleep_schedule",
)

MEDIUM_WEIGHT_FIELDS = (
    "guests",
    "party_at_home",
    "roommate_relationship",
    "conflict_style",
)

STANDARD_WEIGHT_FIELDS = (
    "pets",
    "morning_night_preference",
    "personality",
    "study_at_home",
)

FIELD_WEIGHTS = {
    **{field: 3 for field in HIGH_WEIGHT_FIELDS},
    **{field: 2 for field in MEDIUM_WEIGHT_FIELDS},
    **{field: 1 for field in STANDARD_WEIGHT_FIELDS},
}


def _score_choice(raw_value: str | None) -> int | None:
    return StudentCompatibilitySurvey.score_from_choice(raw_value)


def compatibility_percent(
    base_survey: StudentCompatibilitySurvey,
    other_survey: StudentCompatibilitySurvey,
    max_scale: int = 5,
) -> int:
    """
    Compute a weighted compatibility percentage between two surveys.

    Per-question formula:
    question_score = (1 - abs(a - b) / (max_scale - 1)) * weight
    """
    if max_scale <= 1:
        raise ValueError("max_scale must be greater than 1")

    total_score = 0.0
    total_possible = 0.0
    denominator = float(max_scale - 1)

    for field_name, weight in FIELD_WEIGHTS.items():
        a = _score_choice(getattr(base_survey, field_name, None))
        b = _score_choice(getattr(other_survey, field_name, None))
        if a is None or b is None:
            continue

        question_score = (1.0 - abs(a - b) / denominator) * weight
        total_score += question_score
        total_possible += weight

    if total_possible == 0:
        return 0

    return round((total_score / total_possible) * 100)
