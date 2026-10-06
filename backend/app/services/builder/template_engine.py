from typing import Dict, Any, List, Optional
import html
from app.schemas.canonical_profile import CanonicalProfile

def get_val(field: Any, default: str = "") -> str:
    if field is None:
        return default
    if hasattr(field, "value"):
        v = field.value
        if isinstance(v, dict):
            return ", ".join(filter(None, [str(v.get("city", "")), str(v.get("region", "")), str(v.get("country_code", ""))]))
        return str(v) if v is not None else default
    if isinstance(field, dict):
        v = field.get("value")
        if v is not None:
            if isinstance(v, dict):
                return ", ".join(filter(None, [str(v.get("city", "")), str(v.get("region", "")), str(v.get("country_code", ""))]))
            return str(v)
        return str(field)
    return str(field)

class TemplateEngine:
    """
    ATS-Safe Resume Template Engine.
    Produces clean, semantic HTML with standard headings and selectable text.
    Zero tables for core layout. Strictly renders accepted/verified content.
    """

    TEMPLATES = ["classic", "modern_minimal", "compact", "fresher"]

    @classmethod
    def render(
        cls,
        profile: CanonicalProfile,
        template_id: str = "classic",
        mode: str = "clean_rebuild"
    ) -> str:
        # Strictly obtain renderable copy (strips unaccepted AI suggestions)
        renderable = profile.get_renderable_copy()
        template = template_id.lower() if template_id in cls.TEMPLATES else "classic"

        # Determine section order
        if mode == "fresher":
            sections = ["summary", "education", "projects", "skills", "certifications", "experience"]
        elif mode == "experienced":
            sections = ["summary", "experience", "skills", "projects", "education", "certifications"]
        else: # clean_rebuild, role_targeted
            sections = ["summary", "skills", "experience", "projects", "education", "certifications"]

        css = cls._get_template_css(template)
        header_html = cls._render_header(renderable, template)

        body_sections: List[str] = []
        for sec in sections:
            if sec == "summary":
                html_chunk = cls._render_summary(renderable)
            elif sec == "skills":
                html_chunk = cls._render_skills(renderable)
            elif sec == "experience":
                html_chunk = cls._render_experience(renderable)
            elif sec == "projects":
                html_chunk = cls._render_projects(renderable)
            elif sec == "education":
                html_chunk = cls._render_education(renderable)
            elif sec == "certifications":
                html_chunk = cls._render_certifications(renderable)
            else:
                html_chunk = ""
            
            if html_chunk:
                body_sections.append(html_chunk)

        body_content = "\n".join(body_sections)

        name_str = get_val(renderable.basics.name, "Resume")
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(name_str)}</title>
<style>
{css}
</style>
</head>
<body class="template-{template}">
<div class="resume-container">
{header_html}
<main class="resume-body">
{body_content}
</main>
</div>
</body>
</html>"""

    @classmethod
    def _render_header(cls, profile: CanonicalProfile, template: str) -> str:
        b = profile.basics
        name = html.escape(get_val(b.name, "Candidate Name"))
        headline = html.escape(get_val(b.label, ""))
        email_str = get_val(b.email, "")
        phone_str = get_val(b.phone, "")
        loc_str = get_val(b.location, "")

        contact_parts = []
        if email_str:
            contact_parts.append(f'<span class="contact-item">{html.escape(email_str)}</span>')
        if phone_str:
            contact_parts.append(f'<span class="contact-item">{html.escape(phone_str)}</span>')
        if loc_str:
            contact_parts.append(f'<span class="contact-item">{html.escape(loc_str)}</span>')

        for p in b.profiles:
            if p.url:
                contact_parts.append(
                    f'<span class="contact-item"><a href="{html.escape(p.url)}" target="_blank" rel="noopener">{html.escape(p.network)}</a></span>'
                )

        contacts_html = " &bull; ".join(contact_parts)

        return f"""<header class="resume-header">
    <h1 class="candidate-name">{name}</h1>
    {f'<p class="candidate-headline">{headline}</p>' if headline else ''}
    <div class="candidate-contacts">{contacts_html}</div>
</header>"""

    @classmethod
    def _render_summary(cls, profile: CanonicalProfile) -> str:
        summary_val = get_val(profile.basics.summary, "").strip()
        if not summary_val:
            return ""
        return f"""<section class="resume-section section-summary">
    <h2 class="section-title">Professional Summary</h2>
    <p class="summary-text">{html.escape(summary_val)}</p>
</section>"""

    @classmethod
    def _render_skills(cls, profile: CanonicalProfile) -> str:
        if not profile.skills:
            return ""
        skill_groups = []
        for cat in profile.skills:
            if not cat.skills:
                continue
            skills_names = [html.escape(s.normalized_name or s.name) for s in cat.skills]
            skill_groups.append(
                f'<div class="skill-category"><strong>{html.escape(cat.category_name.capitalize())}:</strong> {", ".join(skills_names)}</div>'
            )
        if not skill_groups:
            return ""
        return f"""<section class="resume-section section-skills">
    <h2 class="section-title">Skills & Technologies</h2>
    <div class="skills-list">{"".join(skill_groups)}</div>
</section>"""

    @classmethod
    def _render_experience(cls, profile: CanonicalProfile) -> str:
        if not profile.experience:
            return ""
        exp_entries = []
        for exp in profile.experience:
            comp = html.escape(get_val(exp.company, ""))
            pos = html.escape(get_val(exp.position, ""))
            loc = html.escape(get_val(exp.location, ""))
            s_date = get_val(exp.start_date, "")
            e_date = get_val(exp.end_date, "Present")
            dates = f"{s_date} - {e_date}"
            
            bullets_html = ""
            if exp.highlights:
                bullets = [f"<li>{html.escape(b.value)}</li>" for b in exp.highlights if b.value.strip()]
                if bullets:
                    bullets_html = f'<ul class="entry-bullets">{"".join(bullets)}</ul>'

            exp_entries.append(f"""<div class="entry experience-entry">
    <div class="entry-header">
        <div class="entry-title-row">
            <span class="entry-position"><strong>{pos}</strong></span>
            <span class="entry-dates"><time>{dates}</time></span>
        </div>
        <div class="entry-subtitle-row">
            <span class="entry-company">{comp}</span>
            {f'<span class="entry-location">{loc}</span>' if loc else ''}
        </div>
    </div>
    {bullets_html}
</div>""")

        return f"""<section class="resume-section section-experience">
    <h2 class="section-title">Professional Experience</h2>
    {"".join(exp_entries)}
</section>"""

    @classmethod
    def _render_projects(cls, profile: CanonicalProfile) -> str:
        if not profile.projects:
            return ""
        proj_entries = []
        for proj in profile.projects:
            name = html.escape(get_val(proj.name, "Project"))
            desc = html.escape(get_val(proj.description, ""))
            url_str = get_val(proj.url, "")
            link = f'<a href="{html.escape(url_str)}" target="_blank" rel="noopener">Link</a>' if url_str else ""
            
            tech_str = ""
            if proj.technologies:
                tech_names = [s.name for s in proj.technologies] if hasattr(proj.technologies[0], 'name') else [str(t) for t in proj.technologies]
                tech_str = f'<div class="project-tech"><em>Technologies: {", ".join([html.escape(t) for t in tech_names])}</em></div>'

            bullets_html = ""
            if proj.highlights:
                bullets = [f"<li>{html.escape(b.value)}</li>" for b in proj.highlights if b.value.strip()]
                if bullets:
                    bullets_html = f'<ul class="entry-bullets">{"".join(bullets)}</ul>'

            proj_entries.append(f"""<div class="entry project-entry">
    <div class="entry-header">
        <div class="entry-title-row">
            <span class="entry-position"><strong>{name}</strong></span>
            {f'<span class="entry-dates">{link}</span>' if link else ''}
        </div>
        {f'<div class="project-desc">{desc}</div>' if desc else ''}
        {tech_str}
    </div>
    {bullets_html}
</div>""")

        return f"""<section class="resume-section section-projects">
    <h2 class="section-title">Projects</h2>
    {"".join(proj_entries)}
</section>"""

    @classmethod
    def _render_education(cls, profile: CanonicalProfile) -> str:
        if not profile.education:
            return ""
        edu_entries = []
        for edu in profile.education:
            inst = html.escape(get_val(edu.institution, ""))
            area = html.escape(get_val(edu.area, ""))
            study_type = html.escape(get_val(edu.study_type, ""))
            degree_str = f"{study_type} in {area}" if study_type and area else study_type or area
            s_date = get_val(edu.start_date, "")
            e_date = get_val(edu.end_date, "")
            dates = f"{s_date} - {e_date}".strip(" -")
            score_val = get_val(edu.score, "")
            gpa = f" | GPA: {html.escape(score_val)}" if score_val else ""

            edu_entries.append(f"""<div class="entry education-entry">
    <div class="entry-header">
        <div class="entry-title-row">
            <span class="entry-position"><strong>{inst}</strong></span>
            <span class="entry-dates"><time>{dates}</time></span>
        </div>
        <div class="entry-subtitle-row">
            <span class="entry-degree">{degree_str}{gpa}</span>
        </div>
    </div>
</div>""")

        return f"""<section class="resume-section section-education">
    <h2 class="section-title">Education</h2>
    {"".join(edu_entries)}
</section>"""

    @classmethod
    def _render_certifications(cls, profile: CanonicalProfile) -> str:
        if not profile.certifications:
            return ""
        cert_entries = []
        for cert in profile.certifications:
            name = html.escape(get_val(cert.name, ""))
            issuer = html.escape(get_val(cert.issuer, ""))
            date = html.escape(get_val(cert.date, ""))
            cert_entries.append(f"""<div class="entry certification-entry">
    <div class="entry-header">
        <div class="entry-title-row">
            <span class="entry-position"><strong>{name}</strong> - {issuer}</span>
            {f'<span class="entry-dates"><time>{date}</time></span>' if date else ''}
        </div>
    </div>
</div>""")

        return f"""<section class="resume-section section-certifications">
    <h2 class="section-title">Certifications</h2>
    {"".join(cert_entries)}
</section>"""

    @classmethod
    def _get_template_css(cls, template: str) -> str:
        common_css = """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { color: #1e293b; background: #ffffff; line-height: 1.5; font-size: 10pt; }
        .resume-container { max-width: 8.5in; margin: 0 auto; padding: 0.5in 0.6in; background: #ffffff; }
        .resume-header { margin-bottom: 14pt; }
        .candidate-name { font-size: 18pt; font-weight: 700; line-height: 1.2; text-transform: uppercase; }
        .candidate-headline { font-size: 11pt; color: #475569; margin-top: 2pt; }
        .candidate-contacts { font-size: 9pt; color: #475569; margin-top: 4pt; }
        .candidate-contacts a { color: #2563eb; text-decoration: none; }
        .resume-section { margin-bottom: 12pt; }
        .section-title { font-size: 11pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #cbd5e1; padding-bottom: 2pt; margin-bottom: 6pt; }
        .entry { margin-bottom: 8pt; page-break-inside: avoid; }
        .entry-title-row { display: flex; justify-content: space-between; font-size: 10pt; }
        .entry-subtitle-row { display: flex; justify-content: space-between; font-size: 9.5pt; color: #475569; margin-bottom: 3pt; }
        .entry-bullets { margin-left: 18pt; margin-top: 3pt; font-size: 9.5pt; }
        .entry-bullets li { margin-bottom: 2.5pt; }
        .skill-category { font-size: 9.5pt; margin-bottom: 2.5pt; }
        .project-desc { font-size: 9.5pt; margin-top: 2pt; }
        .project-tech { font-size: 9pt; color: #475569; margin-top: 2pt; }
        @media print {
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .resume-container { padding: 0.4in; }
        }
        """

        if template == "modern_minimal":
            return common_css + """
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
            .section-title { color: #0f172a; border-bottom: 1.5px solid #0f172a; }
            .candidate-name { color: #0f172a; letter-spacing: 0.5px; }
            """
        elif template == "compact":
            return common_css + """
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 9pt; line-height: 1.35; }
            .resume-container { padding: 0.35in 0.45in; }
            .resume-header { margin-bottom: 8pt; }
            .candidate-name { font-size: 16pt; }
            .resume-section { margin-bottom: 8pt; }
            .entry { margin-bottom: 5pt; }
            .entry-bullets { margin-left: 14pt; margin-top: 2pt; font-size: 8.8pt; }
            .entry-bullets li { margin-bottom: 1.5pt; }
            """
        elif template == "fresher":
            return common_css + """
            body { font-family: "Georgia", serif; }
            .candidate-name { font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #1e3a8a; }
            .section-title { color: #1e3a8a; border-bottom: 1.5px solid #1e3a8a; }
            """
        else: # classic
            return common_css + """
            body { font-family: "Times New Roman", Times, Georgia, serif; }
            .candidate-name { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            .section-title { border-bottom: 1px solid #1e293b; }
            """
