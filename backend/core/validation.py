"""Domain validation for the six student indicators.

Range sources (documented, not invented):
- attendance, internal_marks, assignments : percentage scale 0-100.
  The synthetic generator draws 40-95 / 35-90 / 30-95.
- study_hours : daily hours, capped at a documented 16h ceiling.
  The generator draws 0.5-8.0.
- backlog_count : non-negative count. Generator draws 0-8; allowing 0-20
  gives headroom for realistic growth without changing model semantics.
- stress_level : 1-10 scale, matching the generator exactly (1-10).

Validation at the API boundary is authoritative; the frontend mirrors these
for UX only.
"""

from typing import Dict, Tuple

# feature name -> (min, max, python type)
FEATURE_RANGES: Dict[str, Tuple[float, float, type]] = {
    "attendance": (0, 100, int),
    "internal_marks": (0, 100, int),
    "assignments": (0, 100, int),
    "study_hours": (0.0, 16.0, float),
    "backlog_count": (0, 20, int),
    "stress_level": (1, 10, int),
}


def validate_feature(name: str, value: float) -> str | None:
    """Return an error message if `value` is outside the documented range."""
    low, high, _type = FEATURE_RANGES[name]
    if value < low or value > high:
        return (
            f"{name} must be between {low} and {high}, got {value}"
        )
    return None