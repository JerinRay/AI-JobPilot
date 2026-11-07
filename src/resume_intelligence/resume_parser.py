
import os
import sys
from pathlib import Path

from pypdf import PdfReader
from docx import Document


def extract_pdf_text(file_path):
    reader = PdfReader(file_path)

    extracted_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            extracted_text.append(text)

    return "\n".join(extracted_text), len(reader.pages)


def extract_docx_text(file_path):
    document = Document(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs), 1


def parse_resume(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {file_path}")

    extension = path.suffix.lower()

    if extension == ".pdf":
        text, page_count = extract_pdf_text(path)

    elif extension == ".docx":
        text, page_count = extract_docx_text(path)

    else:
        raise ValueError("Only PDF and DOCX files are supported.")

    return {
        "file_name": path.name,
        "file_type": extension,
        "character_count": len(text),
        "page_count": page_count,
        "text": text
    }


def save_extracted_text(text):
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "extracted_resume.txt"
    output_file.write_text(text, encoding="utf-8")

    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.resume_intelligence.resume_parser <resume_path>")
        sys.exit(1)

    resume_path = sys.argv[1]

    try:
        result = parse_resume(resume_path)

        save_extracted_text(result["text"])

        print("\nRESUME PARSING SUCCESSFUL")
        print("-------------------------")
        print("File:", result["file_name"])
        print("Type:", result["file_type"])
        print("Pages:", result["page_count"])
        print("Characters:", result["character_count"])
        print("\nExtracted text preview:\n")
        print(result["text"][:1500])

    except Exception as error:
        print("Error:", error)
