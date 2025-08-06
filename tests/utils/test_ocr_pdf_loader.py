import os
import tempfile
from unittest.mock import patch, MagicMock
from app.utils.ocr_pdf_loader import MistralOCRPDFLoader
from langchain_core.documents import Document

def test_mistral_ocr_loader_initialization():
    """Test that Mistral OCR PDF loader initializes correctly."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        # Test with API key
        loader = MistralOCRPDFLoader(tmp_path, api_key="test-api-key")
        assert loader.file_path == tmp_path
        assert loader.api_key == "test-api-key"
        
        # Test without API key should raise ValueError
        try:
            loader_no_key = MistralOCRPDFLoader(tmp_path, api_key=None)
            assert False, "Should raise ValueError for missing API key"
        except ValueError as e:
            assert "Mistral API key is required" in str(e)
            
    finally:
        os.unlink(tmp_path)

@patch('app.utils.ocr_pdf_loader.Mistral')
def test_mistral_ocr_successful_processing(mock_mistral):
    """Test successful OCR processing with Mistral API."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        # Mock Mistral client and responses
        mock_client = MagicMock()
        mock_mistral.return_value = mock_client
        
        # Mock file upload response
        mock_upload_response = MagicMock()
        mock_upload_response.id = "test-file-id"
        mock_client.files.upload.return_value = mock_upload_response
        
        # Mock file retrieve response
        mock_retrieve_response = MagicMock()
        mock_retrieve_response.filename = "test.pdf"
        mock_retrieve_response.size_bytes = 1234
        mock_client.files.retrieve.return_value = mock_retrieve_response
        
        # Mock signed URL response
        mock_signed_url = MagicMock()
        mock_signed_url.url = "https://example.com/signed-url"
        mock_client.files.get_signed_url.return_value = mock_signed_url
        
        # Mock OCR response
        mock_ocr_response = MagicMock()
        mock_ocr_response.text = "This is OCR extracted text from the PDF document."
        mock_client.ocr.process.return_value = mock_ocr_response
        
        # Mock file deletion
        mock_client.files.delete.return_value = None
        
        loader = MistralOCRPDFLoader(tmp_path, api_key="test-api-key")
        documents = loader.load()
        
        # Verify the document was created correctly
        assert len(documents) == 1
        assert "OCR extracted text" in documents[0].page_content
        assert documents[0].metadata["source"] == tmp_path
        assert documents[0].metadata["extraction_method"] == "mistral_ocr"
        assert documents[0].metadata["file_id"] == "test-file-id"
        
        # Verify API calls were made
        mock_client.files.upload.assert_called_once()
        mock_client.files.retrieve.assert_called_once_with(file_id="test-file-id")
        mock_client.files.get_signed_url.assert_called_once_with(file_id="test-file-id")
        mock_client.ocr.process.assert_called_once()
        mock_client.files.delete.assert_called_once_with(file_id="test-file-id")
        
    finally:
        os.unlink(tmp_path)

@patch('app.utils.ocr_pdf_loader.Mistral')
def test_mistral_ocr_with_pages(mock_mistral):
    """Test OCR processing when response has multiple pages."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        # Mock Mistral client and responses
        mock_client = MagicMock()
        mock_mistral.return_value = mock_client
        
        # Mock file upload and other responses
        mock_upload_response = MagicMock()
        mock_upload_response.id = "test-file-id"
        mock_client.files.upload.return_value = mock_upload_response
        
        mock_retrieve_response = MagicMock()
        mock_retrieve_response.filename = "test.pdf"
        mock_retrieve_response.size_bytes = 1234
        mock_client.files.retrieve.return_value = mock_retrieve_response
        
        mock_signed_url = MagicMock()
        mock_signed_url.url = "https://example.com/signed-url"
        mock_client.files.get_signed_url.return_value = mock_signed_url
        
        # Mock OCR response with pages
        mock_page1 = MagicMock()
        mock_page1.text = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.text = "Page 2 content"
        
        mock_ocr_response = MagicMock()
        mock_ocr_response.text = None  # No top-level text
        mock_ocr_response.pages = [mock_page1, mock_page2]
        mock_client.ocr.process.return_value = mock_ocr_response
        
        mock_client.files.delete.return_value = None
        
        loader = MistralOCRPDFLoader(tmp_path, api_key="test-api-key")
        documents = loader.load()
        
        # Verify documents were created for each page
        assert len(documents) == 2
        assert documents[0].page_content == "Page 1 content"
        assert documents[1].page_content == "Page 2 content"
        assert documents[0].metadata["page"] == 1
        assert documents[1].metadata["page"] == 2
        
    finally:
        os.unlink(tmp_path)

@patch('app.utils.ocr_pdf_loader.Mistral')
def test_mistral_ocr_failure_handling(mock_mistral):
    """Test error handling when OCR processing fails."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        # Mock Mistral client to raise an exception
        mock_client = MagicMock()
        mock_mistral.return_value = mock_client
        mock_client.files.upload.side_effect = Exception("API Error")
        
        loader = MistralOCRPDFLoader(tmp_path, api_key="test-api-key")
        documents = loader.load()
        
        # Should return error document
        assert len(documents) == 1
        assert documents[0].page_content == ""
        assert documents[0].metadata["extraction_method"] == "mistral_ocr_failed"
        assert "API Error" in documents[0].metadata["error"]
        
    finally:
        os.unlink(tmp_path)

def test_mistral_ocr_source_property():
    """Test the source property returns correct file path."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.4 fake pdf content")
        tmp_path = tmp_file.name
    
    try:
        loader = MistralOCRPDFLoader(tmp_path, api_key="test-api-key")
        assert loader.source == tmp_path
    finally:
        os.unlink(tmp_path)