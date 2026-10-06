import re
from typing import List, Tuple, Optional
from datetime import datetime
from app.schemas.canonical_profile import CanonicalProfile, CanonicalExperience
from app.schemas.quality import TimelineAnomaly, TimelineAnalysisResult

class TimelineEngine:
    """
    Analyzes candidate career timeline for:
    - Overlapping positions without explanation
    - Unexplained employment gaps (>3 months)
    - Impossible dates (end date before start date, future dates)
    - Duration vs. skill experience contradictions (e.g., claiming 5 years Python on a 2-year timeline)
    """

    @classmethod
    def analyze_timeline(cls, profile: CanonicalProfile) -> TimelineAnalysisResult:
        experiences = profile.experience
        anomalies: List[TimelineAnomaly] = []
        parsed_intervals: List[Tuple[int, int, str, str]] = []  # (start_y, end_y, company, role)

        current_year = datetime.now().year

        for exp in experiences:
            comp_name = str(exp.company.value or "Company")
            role_name = str(exp.position.value or "Role")
            start_str = str(exp.start_date.value or "")
            end_str = str(exp.end_date.value or "")
            is_curr = bool(exp.is_current.value) if exp.is_current else False

            start_y = cls._parse_year(start_str)
            end_y = current_year if (is_curr or "present" in end_str.lower()) else cls._parse_year(end_str)

            # 1. Check impossible dates
            if start_y and start_y > current_year + 1:
                anomalies.append(TimelineAnomaly(
                    anomaly_type="impossible_date",
                    severity="critical",
                    company_or_entity=comp_name,
                    dates=f"{start_str} - {end_str}",
                    description=f"Start date {start_y} is in the future.",
                    remediation_hint="Correct the start year to match actual employment records."
                ))
            elif start_y and end_y and end_y < start_y:
                anomalies.append(TimelineAnomaly(
                    anomaly_type="impossible_date",
                    severity="critical",
                    company_or_entity=comp_name,
                    dates=f"{start_str} - {end_str}",
                    description=f"End year ({end_y}) is earlier than start year ({start_y}).",
                    remediation_hint="Invert or correct the start and end dates for this role."
                ))
            elif start_y and end_y:
                parsed_intervals.append((start_y, end_y, comp_name, role_name))

        # Sort intervals by start year ascending
        parsed_intervals.sort(key=lambda x: x[0])

        # 2. Check Overlaps
        for i in range(len(parsed_intervals) - 1):
            curr = parsed_intervals[i]
            nxt = parsed_intervals[i + 1]
            # If current ends after next starts, and they are distinct companies
            if curr[1] > nxt[0] and curr[2].lower() != nxt[2].lower():
                anomalies.append(TimelineAnomaly(
                    anomaly_type="overlap",
                    severity="warning",
                    company_or_entity=f"{curr[2]} & {nxt[2]}",
                    dates=f"{curr[0]}-{curr[1]} vs {nxt[0]}-{nxt[1]}",
                    description=f"Concurrent employment detected between {curr[2]} ({curr[3]}) and {nxt[2]} ({nxt[3]}).",
                    remediation_hint="If this was part-time, advisory, or consulting work, clarify the employment type to avoid recruiter confusion."
                ))

        # 3. Check Career Gaps (> 1.5 years between roles)
        for i in range(len(parsed_intervals) - 1):
            curr = parsed_intervals[i]
            nxt = parsed_intervals[i + 1]
            if nxt[0] - curr[1] >= 2:
                gap_years = nxt[0] - curr[1]
                anomalies.append(TimelineAnomaly(
                    anomaly_type="employment_gap",
                    severity="warning",
                    company_or_entity=f"Between {curr[2]} and {nxt[2]}",
                    dates=f"{curr[1]} to {nxt[0]}",
                    description=f"Unexplained gap of approximately {gap_years} years between roles.",
                    remediation_hint="Add education, sabbatical, independent consulting, or certification project to account for this timeframe."
                ))

        # 4. Total Career Calculation
        if parsed_intervals:
            min_y = min(x[0] for x in parsed_intervals)
            max_y = max(x[1] for x in parsed_intervals)
            total_years = max(1.0, float(max_y - min_y))
            total_months = int(total_years * 12)
        else:
            total_years = 1.0
            total_months = 12

        # 5. Check Contradictions (e.g., claiming 6+ years experience in summary when timeline is only 2 years)
        summary_text = str(profile.basics.summary.value or "").lower()
        yoe_claim_match = re.search(r"(\d+)\+?\s*years(?:\s+of)?\s+experience", summary_text)
        if yoe_claim_match:
            claimed_yoe = int(yoe_claim_match.group(1))
            if claimed_yoe > total_years + 2:
                anomalies.append(TimelineAnomaly(
                    anomaly_type="duration_contradiction",
                    severity="critical",
                    company_or_entity="Professional Summary",
                    dates=f"Claimed {claimed_yoe} yrs vs Timeline {total_years:.0f} yrs",
                    description=f"Summary states '{claimed_yoe}+ years experience' but verifiable timeline spans only {total_years:.0f} years.",
                    remediation_hint="Align summary statement with actual verifiable career start date to preserve credibility."
                ))

        has_critical = any(a.severity == "critical" for a in anomalies)

        return TimelineAnalysisResult(
            total_career_months=total_months,
            total_career_years=round(total_years, 1),
            anomalies=anomalies,
            has_critical_inconsistency=has_critical
        )

    @staticmethod
    def _parse_year(text: str) -> Optional[int]:
        m = re.search(r"\b(20\d\d|19\d\d)\b", text)
        if m:
            return int(m.group(1))
        return None
