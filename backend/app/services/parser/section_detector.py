import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class DetectedSection:
    section_type: str
    title: str
    content: str
    start_line: int
    end_line: int

class SectionDetector:
    SECTION_PATTERNS = {
        "summary": [
            r"^(professional\s+)?summary",
            r"^profile",
            r"^executive\s+summary",
            r"^about(\s+me)?",
            r"^objective",
            r"^career\s+objective",
        ],
        "experience": [
            r"^(work|professional|employment)\s+experience",
            r"^experience",
            r"^work\s+history",
            r"^employment\s+history",
            r"^career\s+history",
            r"^relevant\s+experience",
        ],
        "education": [
            r"^education",
            r"^academic\s+(background|history|qualifications)",
            r"^degrees",
            r"^educational\s+background",
        ],
        "skills": [
            r"^(technical\s+)?skills",
            r"^core\s+competencies",
            r"^technologies",
            r"^skills\s+(&|and)\s+tools",
            r"^technical\s+expertise",
            r"^proficiencies",
            r"^key\s+skills",
        ],
        "projects": [
            r"^projects",
            r"^key\s+projects",
            r"^personal\s+projects",
            r"^academic\s+projects",
            r"^selected\s+projects",
        ],
        "certifications": [
            r"^certifications?",
            r"^licenses?\s+(&|and)\s+certifications?",
            r"^credentials",
            r"^professional\s+certifications?",
        ],
        "awards": [
            r"^awards?(\s+(&|and)\s+honors)?",
            r"^honors?",
            r"^achievements",
        ]
    }

    @classmethod
    def detect_sections(cls, text: str) -> List[DetectedSection]:
        lines = [line.strip() for line in text.split("\n")]
        sections: List[DetectedSection] = []
        
        # Track header / contact before first explicit section
        current_section = "contact"
        current_title = "Contact Information"
        current_lines: List[str] = []
        start_line = 0

        for line_idx, line in enumerate(lines):
            if not line:
                continue
            
            # Check if this line is likely a section header
            matched_type, matched_title = cls._match_header(line)
            if matched_type:
                # Save previous section if it has content
                if current_lines:
                    sections.append(DetectedSection(
                        section_type=current_section,
                        title=current_title,
                        content="\n".join(current_lines).strip(),
                        start_line=start_line,
                        end_line=line_idx - 1
                    ))
                current_section = matched_type
                current_title = matched_title
                current_lines = []
                start_line = line_idx
            else:
                current_lines.append(line)

        # Append final section
        if current_lines:
            sections.append(DetectedSection(
                section_type=current_section,
                title=current_title,
                content="\n".join(current_lines).strip(),
                start_line=start_line,
                end_line=len(lines) - 1
            ))

        return sections

    @classmethod
    def _match_header(cls, line: str) -> Tuple[str, str]:
        # Filter out lines that are too long to be headers (> 45 chars) or contain sentences
        cleaned = line.strip(" :-\t#*").lower()
        if len(cleaned) > 45 or len(cleaned) < 3 or "." in cleaned:
            return "", ""
        
        for section_type, patterns in cls.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, cleaned, re.IGNORECASE):
                    return section_type, line.strip(" :#*")
        return "", ""
