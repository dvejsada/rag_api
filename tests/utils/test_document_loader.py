import os
from unittest.mock import patch, MagicMock
from app.utils.document_loader import get_loader, clean_text, process_documents
from langchain_core.documents import Document

def test_clean_text():
    text = "Hello\x00World"
    cleaned = clean_text(text)
    assert "\x00" not in cleaned
    assert cleaned == "HelloWorld"

def test_get_loader_text(tmp_path):
    # Create a temporary text file.
    file_path = tmp_path / "test.txt"
    file_path.write_text("Sample text")
    loader, known_type, file_ext = get_loader("test.txt", "text/plain", str(file_path))
    assert known_type is True
    assert file_ext == "txt"
    data = loader.load()
    # Check that data is loaded.
    assert data is not None

@patch('app.utils.document_loader.MISTRAL_API_KEY', 'test-api-key')
def test_get_loader_pdf(tmp_path):
    # Create a temporary PDF file
    file_path = tmp_path / "test.pdf"
    file_path.write_bytes(b"%PDF-1.4 fake pdf content")
    loader, known_type, file_ext = get_loader("test.pdf", "application/pdf", str(file_path))
    assert known_type is True
    assert file_ext == "pdf"
    # Check that we get the MistralOCRPDFLoader
    from app.utils.ocr_pdf_loader import MistralOCRPDFLoader
    assert isinstance(loader, MistralOCRPDFLoader)

def test_process_documents():
    docs = [
        Document(page_content="Page 1 content", metadata={"source": "dummy.txt", "page": 1}),
        Document(page_content="Page 2 content", metadata={"source": "dummy.txt", "page": 2}),
    ]
    processed = process_documents(docs)
    assert "dummy.txt" in processed
    assert "# PAGE 1" in processed
    assert "# PAGE 2" in processed