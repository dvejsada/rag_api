import os
import tempfile
from unittest.mock import patch, MagicMock
from app.utils.ocr_pdf_loader import OCREnabledPDFLoader
from langchain_core.documents import Document

def test_ocr_pdf_loader_initialization():
    """Test that OCR PDF loader initializes correctly."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        loader = OCREnabledPDFLoader(
            tmp_path, 
            extract_images=True,
            use_ocr_fallback=True,
            min_text_threshold=100
        )
        assert loader.file_path == tmp_path
        assert loader.extract_images == True
        assert loader.use_ocr_fallback == True
        assert loader.min_text_threshold == 100
    finally:
        os.unlink(tmp_path)

def test_ocr_pdf_loader_without_ocr():
    """Test OCR PDF loader with OCR disabled."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        loader = OCREnabledPDFLoader(tmp_path, use_ocr_fallback=False)
        assert loader.use_ocr_fallback == False
        assert loader._ocr_engine is None
    finally:
        os.unlink(tmp_path)

@patch('app.utils.ocr_pdf_loader.PyPDFLoader')
def test_ocr_pdf_loader_sufficient_text(mock_pdf_loader):
    """Test that regular PDF extraction is used when sufficient text is found."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        # Mock PyPDFLoader to return sufficient text
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [
            Document(page_content="This is a document with sufficient text content to pass the threshold test.", metadata={"page": 1})
        ]
        mock_pdf_loader.return_value = mock_loader_instance
        
        loader = OCREnabledPDFLoader(tmp_path, min_text_threshold=50)
        documents = loader.load()
        
        assert len(documents) == 1
        assert "sufficient text content" in documents[0].page_content
        mock_pdf_loader.assert_called()
    finally:
        os.unlink(tmp_path)

def test_combine_ocr_results():
    """Test OCR results combination functionality."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        loader = OCREnabledPDFLoader(tmp_path)
        
        # Mock OCR results - format: [bbox, text, confidence]
        ocr_results = [
            [[[10, 10], [50, 10], [50, 30], [10, 30]], "Hello", 0.95],
            [[[60, 10], [100, 10], [100, 30], [60, 30]], "World", 0.92],
            [[[10, 40], [80, 40], [80, 60], [10, 60]], "Second line", 0.88],
        ]
        
        combined_text = loader._combine_ocr_results(ocr_results)
        assert "Hello World" in combined_text
        assert "Second line" in combined_text
        assert combined_text.count('\n') >= 1  # Should have line breaks
    finally:
        os.unlink(tmp_path)

def test_ocr_pdf_loader_source_property():
    """Test the source property returns correct file path."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        loader = OCREnabledPDFLoader(tmp_path)
        assert loader.source == tmp_path
    finally:
        os.unlink(tmp_path)