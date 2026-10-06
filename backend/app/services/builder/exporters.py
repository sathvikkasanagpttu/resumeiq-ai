import io
import json
from typing import Dict, Any, List, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from app.schemas.canonical_profile import CanonicalProfile
from app.services.builder.template_engine import TemplateEngine, get_val

class ResumeExporter:
    """
    Multi-format resume exporter.
    Supports: JSON (JSON Resume format), TXT, HTML, DOCX, PDF.
    All exports strictly consume CanonicalProfile.get_renderable_copy()
    guaranteeing zero unaccepted AI claims appear in exports.
    """

    @classmethod
    def to_json(cls, profile: CanonicalProfile) -> str:
        renderable = profile.get_renderable_copy()
        return json.dumps(renderable.model_dump(), indent=2, default=str)

    @classmethod
    def to_html(cls, profile: CanonicalProfile, template_id: str = "classic", mode: str = "clean_rebuild") -> str:
        return TemplateEngine.render(profile, template_id=template_id, mode=mode)

    @classmethod
    def to_txt(cls, profile: CanonicalProfile) -> str:
        r = profile.get_renderable_copy()
        lines: List[str] = []

        # Name and contact
        name_str = get_val(r.basics.name, "Candidate").upper()
        lines.append(name_str)
        headline_str = get_val(r.basics.label, "")
        if headline_str:
            lines.append(headline_str)

        contact_bits = []
        email_str = get_val(r.basics.email, "")
        phone_str = get_val(r.basics.phone, "")
        loc_str = get_val(r.basics.location, "")
        if email_str:
            contact_bits.append(email_str)
        if phone_str:
            contact_bits.append(phone_str)
        if loc_str:
            contact_bits.append(loc_str)
        for p in r.basics.profiles:
            if p.url:
                contact_bits.append(f"{p.network}: {p.url}")
        if contact_bits:
            lines.append(" | ".join(contact_bits))

        lines.append("")

        # Summary
        summary_val = get_val(r.basics.summary, "").strip()
        if summary_val:
            lines.append("PROFESSIONAL SUMMARY")
            lines.append("=" * 20)
            lines.append(summary_val)
            lines.append("")

        # Skills
        if r.skills:
            lines.append("SKILLS & TECHNOLOGIES")
            lines.append("=" * 20)
            for cat in r.skills:
                if cat.skills:
                    s_names = [s.normalized_name or s.name for s in cat.skills]
                    lines.append(f"{cat.category_name.capitalize()}: {', '.join(s_names)}")
            lines.append("")

        # Experience
        if r.experience:
            lines.append("EXPERIENCE")
            lines.append("=" * 20)
            for exp in r.experience:
                pos = get_val(exp.position, "")
                comp = get_val(exp.company, "")
                s_date = get_val(exp.start_date, "")
                e_date = get_val(exp.end_date, "Present")
                dates = f"{s_date} - {e_date}"
                lines.append(f"{pos} | {comp} ({dates})")
                loc = get_val(exp.location, "")
                if loc:
                    lines.append(f"Location: {loc}")
                for h in exp.highlights:
                    if h.value.strip():
                        lines.append(f"  - {h.value.strip()}")
                lines.append("")

        # Projects
        if r.projects:
            lines.append("PROJECTS")
            lines.append("=" * 20)
            for proj in r.projects:
                p_name = get_val(proj.name, "Project")
                p_url = get_val(proj.url, "")
                p_hdr = f"{p_name} ({p_url})" if p_url else p_name
                lines.append(p_hdr)
                desc = get_val(proj.description, "")
                if desc:
                    lines.append(f"  {desc}")
                if proj.technologies:
                    tech_names = [s.name for s in proj.technologies] if hasattr(proj.technologies[0], 'name') else [str(t) for t in proj.technologies]
                    lines.append(f"  Technologies: {', '.join(tech_names)}")
                for h in proj.highlights:
                    if h.value.strip():
                        lines.append(f"  - {h.value.strip()}")
                lines.append("")

        # Education
        if r.education:
            lines.append("EDUCATION")
            lines.append("=" * 20)
            for edu in r.education:
                inst = get_val(edu.institution, "")
                area = get_val(edu.area, "")
                stype = get_val(edu.study_type, "")
                deg = f"{stype} in {area}".strip() if stype and area else stype or area
                s_date = get_val(edu.start_date, "")
                e_date = get_val(edu.end_date, "")
                dates = f"{s_date} - {e_date}".strip(" -")
                lines.append(f"{inst} | {deg} ({dates})")
                score_val = get_val(edu.score, "")
                if score_val:
                    lines.append(f"  GPA: {score_val}")
            lines.append("")

        # Certifications
        if r.certifications:
            lines.append("CERTIFICATIONS")
            lines.append("=" * 20)
            for cert in r.certifications:
                c_name = get_val(cert.name, "")
                c_iss = get_val(cert.issuer, "")
                c_dt = get_val(cert.date, "")
                date_str = f" ({c_dt})" if c_dt else ""
                lines.append(f"- {c_name} - {c_iss}{date_str}")
            lines.append("")

        return "\n".join(lines).strip()

    @classmethod
    def to_docx(cls, profile: CanonicalProfile, template_id: str = "classic") -> bytes:
        r = profile.get_renderable_copy()
        doc = docx.Document()

        # Page margins (0.6 in)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.6)
            section.bottom_margin = Inches(0.6)
            section.left_margin = Inches(0.6)
            section.right_margin = Inches(0.6)

        # Candidate Name
        name_str = get_val(r.basics.name, "Candidate Name")
        p_name = doc.add_paragraph()
        run_name = p_name.add_run(name_str)
        run_name.bold = True
        run_name.font.size = Pt(18)
        run_name.font.color.rgb = RGBColor(15, 23, 42)

        headline_str = get_val(r.basics.label, "")
        if headline_str:
            p_head = doc.add_paragraph()
            run_head = p_head.add_run(headline_str)
            run_head.font.size = Pt(11)
            run_head.font.color.rgb = RGBColor(71, 85, 105)

        # Contacts
        contact_bits = []
        email_str = get_val(r.basics.email, "")
        phone_str = get_val(r.basics.phone, "")
        loc_str = get_val(r.basics.location, "")
        if email_str:
            contact_bits.append(email_str)
        if phone_str:
            contact_bits.append(phone_str)
        if loc_str:
            contact_bits.append(loc_str)
        for pr in r.basics.profiles:
            if pr.url:
                contact_bits.append(f"{pr.network}: {pr.url}")
        if contact_bits:
            p_contacts = doc.add_paragraph()
            run_c = p_contacts.add_run(" • ".join(contact_bits))
            run_c.font.size = Pt(9.5)
            run_c.font.color.rgb = RGBColor(71, 85, 105)

        # Helper for Section Heading
        def add_heading(title: str):
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            run = h.add_run(title.upper())
            run.font.size = Pt(11)
            run.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42)

        # Summary
        summary_val = get_val(r.basics.summary, "").strip()
        if summary_val:
            add_heading("Professional Summary")
            p_sum = doc.add_paragraph()
            p_sum.paragraph_format.space_after = Pt(6)
            run_s = p_sum.add_run(summary_val)
            run_s.font.size = Pt(10)

        # Skills
        if r.skills:
            add_heading("Skills & Technologies")
            for cat in r.skills:
                if cat.skills:
                    p_sk = doc.add_paragraph()
                    p_sk.paragraph_format.space_after = Pt(2)
                    run_cat = p_sk.add_run(f"{cat.category_name.capitalize()}: ")
                    run_cat.bold = True
                    run_cat.font.size = Pt(9.5)
                    s_names = [s.normalized_name or s.name for s in cat.skills]
                    run_val = p_sk.add_run(", ".join(s_names))
                    run_val.font.size = Pt(9.5)

        # Experience
        if r.experience:
            add_heading("Professional Experience")
            for exp in r.experience:
                pos = get_val(exp.position, "")
                comp = get_val(exp.company, "")
                p_exp_hdr = doc.add_paragraph()
                p_exp_hdr.paragraph_format.space_before = Pt(4)
                p_exp_hdr.paragraph_format.space_after = Pt(1)
                run_pos = p_exp_hdr.add_run(f"{pos} — {comp}")
                run_pos.bold = True
                run_pos.font.size = Pt(10.5)

                s_date = get_val(exp.start_date, "")
                e_date = get_val(exp.end_date, "Present")
                dates = f"{s_date} - {e_date}"
                run_dates = p_exp_hdr.add_run(f" ({dates})")
                run_dates.italic = True
                run_dates.font.size = Pt(9.5)
                run_dates.font.color.rgb = RGBColor(71, 85, 105)

                for h in exp.highlights:
                    if h.value.strip():
                        p_b = doc.add_paragraph(style='List Bullet')
                        p_b.paragraph_format.space_after = Pt(2)
                        run_b = p_b.add_run(h.value.strip())
                        run_b.font.size = Pt(9.5)

        # Projects
        if r.projects:
            add_heading("Projects")
            for proj in r.projects:
                p_name = get_val(proj.name, "Project")
                p_url = get_val(proj.url, "")
                p_pr = doc.add_paragraph()
                p_pr.paragraph_format.space_before = Pt(4)
                p_pr.paragraph_format.space_after = Pt(1)
                run_pname = p_pr.add_run(p_name)
                run_pname.bold = True
                run_pname.font.size = Pt(10)
                if p_url:
                    run_url = p_pr.add_run(f" ({p_url})")
                    run_url.font.size = Pt(9)
                    run_url.font.color.rgb = RGBColor(37, 99, 235)

                desc = get_val(proj.description, "")
                if desc:
                    p_desc = doc.add_paragraph()
                    p_desc.paragraph_format.space_after = Pt(2)
                    r_desc = p_desc.add_run(desc)
                    r_desc.font.size = Pt(9.5)

                for h in proj.highlights:
                    if h.value.strip():
                        p_b = doc.add_paragraph(style='List Bullet')
                        p_b.paragraph_format.space_after = Pt(2)
                        run_b = p_b.add_run(h.value.strip())
                        run_b.font.size = Pt(9.5)

        # Education
        if r.education:
            add_heading("Education")
            for edu in r.education:
                inst = get_val(edu.institution, "")
                area = get_val(edu.area, "")
                stype = get_val(edu.study_type, "")
                deg = f"{stype} in {area}".strip() if stype and area else stype or area
                s_date = get_val(edu.start_date, "")
                e_date = get_val(edu.end_date, "")
                dates = f"{s_date} - {e_date}".strip(" -")
                p_edu = doc.add_paragraph()
                p_edu.paragraph_format.space_after = Pt(2)
                r_inst = p_edu.add_run(f"{inst} — ")
                r_inst.bold = True
                r_inst.font.size = Pt(10)
                r_deg = p_edu.add_run(deg)
                r_deg.font.size = Pt(9.5)
                if dates:
                    r_dt = p_edu.add_run(f" | ({dates})")
                    r_dt.italic = True
                    r_dt.font.size = Pt(9)

        # Certifications
        if r.certifications:
            add_heading("Certifications")
            for cert in r.certifications:
                c_name = get_val(cert.name, "")
                c_iss = get_val(cert.issuer, "")
                p_c = doc.add_paragraph(style='List Bullet')
                p_c.paragraph_format.space_after = Pt(2)
                r_c = p_c.add_run(f"{c_name} — {c_iss}")
                r_c.font.size = Pt(9.5)

        out = io.BytesIO()
        doc.save(out)
        out.seek(0)
        return out.getvalue()

    @classmethod
    def to_pdf(cls, profile: CanonicalProfile, template_id: str = "classic") -> bytes:
        """
        Generates ATS-safe selectable text PDF document.
        Uses pure Python PDF 1.4 output with correct object xrefs.
        """
        txt_content = cls.to_txt(profile)
        lines = txt_content.splitlines()

        # Build PDF stream commands
        stream_cmds = ["BT", "/F1 10 Tf", "13 TL", "54 738 Td"]
        for line in lines:
            line_str = line.strip()
            if not line_str:
                stream_cmds.append("T*")
                continue
            # Escape PDF string literals
            escaped = line_str.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            # Standard ASCII encoding
            safe_text = escaped.encode("ascii", "replace").decode("ascii")
            stream_cmds.append(f"({safe_text}) '")

        stream_cmds.append("ET")
        stream_data = "\n".join(stream_cmds).encode("latin1")
        stream_len = len(stream_data)

        # Construct objects
        obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        obj3 = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        obj4 = b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        obj5 = f"5 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin1") + stream_data + b"\nendstream\nendobj\n"

        header = b"%PDF-1.4\n"
        offsets = []
        cur_offset = len(header)

        offsets.append(cur_offset)
        cur_offset += len(obj1)

        offsets.append(cur_offset)
        cur_offset += len(obj2)

        offsets.append(cur_offset)
        cur_offset += len(obj3)

        offsets.append(cur_offset)
        cur_offset += len(obj4)

        offsets.append(cur_offset)
        cur_offset += len(obj5)

        xref_str = f"xref\n0 6\n0000000000 65535 f \n"
        for off in offsets:
            xref_str += f"{off:010d} 00000 n \n"

        trailer_str = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{cur_offset}\n%%EOF"

        pdf_bytes = header + obj1 + obj2 + obj3 + obj4 + obj5 + xref_str.encode("latin1") + trailer_str.encode("latin1")
        return pdf_bytes
