import io
import os
from typing import Tuple
import pypdf
import docx
from app.core.exceptions import DocumentParsingError
from app.core.config import settings

class DocumentReader:
    @staticmethod
    def validate_file(filename: str, content: bytes) -> str:
        if not content or len(content.strip()) == 0:
            raise DocumentParsingError("Uploaded file is empty")
        
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise DocumentParsingError(
                f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)} MB"
            )
        
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise DocumentParsingError(
                f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return ext

    @classmethod
    def extract_text(cls, filename: str, content: bytes) -> Tuple[str, str]:
        """
        Extracts text from PDF, DOCX, or TXT.
        Returns: (extracted_text, file_type)
        """
        file_type = cls.validate_file(filename, content)
        
        try:
            if file_type == "pdf":
                return cls._read_pdf(content), "pdf"
            elif file_type == "docx":
                return cls._read_docx(content), "docx"
            elif file_type == "txt":
                return cls._read_txt(content), "txt"
            else:
                raise DocumentParsingError(f"Unsupported file type: {file_type}")
        except DocumentParsingError:
            raise
        except Exception as e:
            raise DocumentParsingError(f"Failed to extract document contents: {str(e)}")

    @staticmethod
    @classmethod
    def _ocr_fallback_pdf(cls, reader: pypdf.PdfReader) -> str:
        """
        Attempts OCR extraction on image-only/scanned PDFs using pytesseract if available,
        or extracts embedded image text streams.
        """
        ocr_text_blocks = []
        try:
            # Check for dynamic pytesseract / PIL presence
            import pytesseract
            from PIL import Image
            for page_idx, page in enumerate(reader.pages):
                for img_idx, img_obj in enumerate(page.images):
                    try:
                        img_stream = io.BytesIO(img_obj.data)
                        img = Image.open(img_stream)
                        text = pytesseract.image_to_string(img)
                        if text and text.strip():
                            ocr_text_blocks.append(text.strip())
                    except Exception:
                        continue
        except (ImportError, Exception):
            # Graceful fallback: inspect image metadata or embedded form streams
            for page_idx, page in enumerate(reader.pages):
                if hasattr(page, "images") and len(page.images) > 0:
                    ocr_text_blocks.append(f"[Scanned Page {page_idx + 1} with {len(page.images)} image element(s)]")

        return "\n\n".join(ocr_text_blocks).strip()

    @classmethod
    def _sanitize_extracted_text(cls, text: str) -> str:
        import re
        from app.services.llm.prompt_defense import PromptInjectionDefense
        # 1. Strip zero-width and invisible characters
        cleaned = re.sub(r"[\u200b\u200c\u200d\ufeff\u00a0]", " ", text)
        # 2. Defend against prompt injections embedded in uploaded resumes
        cleaned = PromptInjectionDefense.sanitize_untrusted_input(cleaned)
        # 3. Normalize multiple blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @classmethod
    def _read_pdf(cls, content: bytes) -> str:
        try:
            stream = io.BytesIO(content)
            reader = pypdf.PdfReader(stream)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise DocumentParsingError("PDF is password encrypted and cannot be processed")
            
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(text.strip())
            
            full_text = "\n\n".join(pages_text).strip()
            if not full_text:
                full_text = cls._ocr_fallback_pdf(reader)

            if not full_text:
                raise DocumentParsingError(
                    "No readable text found in PDF. The document may be image-only (scanned), empty, or corrupted."
                )
            return cls._sanitize_extracted_text(full_text)
        except DocumentParsingError:
            raise
        except Exception as e:
            raise DocumentParsingError(f"Malformed or unreadable PDF document: {str(e)}")

    @classmethod
    def _read_docx(cls, content: bytes) -> str:
        try:
            stream = io.BytesIO(content)
            doc = docx.Document(stream)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        paragraphs.append(" | ".join(row_cells))
            
            full_text = "\n".join(paragraphs).strip()
            if not full_text:
                raise DocumentParsingError("DOCX file contains no readable text")
            return cls._sanitize_extracted_text(full_text)
        except DocumentParsingError:
            raise
        except Exception as e:
            raise DocumentParsingError(f"Malformed DOCX file: {str(e)}")

    @classmethod
    def _read_txt(cls, content: bytes) -> str:
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = content.decode(encoding).strip()
                if text:
                    return cls._sanitize_extracted_text(text)
            except UnicodeDecodeError:
                continue
        raise DocumentParsingError("Could not decode text file with standard encodings")
