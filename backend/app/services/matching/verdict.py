from typing import Optional, Dict
from app.core.config import settings

def determine_verdict(score: float, thresholds: Optional[Dict[str, int]] = None) -> str:
    """
    Central single source of truth for match verdict calculation.
    """
    t = thresholds or settings.DEFAULT_VERDICT_THRESHOLDS
    strong_th = t.get("strong", 80)
    good_th = t.get("good", 65)
    partial_th = t.get("partial", 45)

    if score >= strong_th:
        return "strong_match"
    elif score >= good_th:
        return "good_match"
    elif score >= partial_th:
        return "partial_match"
    return "weak_match"
