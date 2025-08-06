# app/utils/ocr_pdf_loader.py
import os
import tempfile
import logging
from typing import List
from pathlib import Path

from langchain_core.documents import Document
from mistralai import Mistral

# Use standard logging
logger = logging.getLogger(__name__)


class MistralOCRPDFLoader:
    """
    PDF Loader that processes ALL PDFs using Mistral OCR API.
    No fallback to regular text extraction - all PDFs are processed via OCR.
    """

    def __init__(
        self,
        file_path: str,
        api_key: str = None,
    ):
        """
        Initialize the Mistral OCR PDF loader.

        Args:
            file_path: Path to the PDF file
            api_key: Mistral API key for OCR processing
        """
        self.file_path = file_path
        self.api_key = api_key
        
        if not self.api_key:
            raise ValueError("Mistral API key is required for OCR processing")
        
        # Initialize Mistral client
        try:
            self.client = Mistral(api_key=self.api_key)
            logger.info("Mistral OCR client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral client: {e}")
            raise

    def load(self) -> List[Document]:
        """
        Load PDF documents using Mistral OCR API.
        
        Returns:
            List of Document objects with OCR-extracted text
        """
        try:
            return self._extract_with_mistral_ocr()
        except Exception as e:
            logger.error(f"Mistral OCR extraction failed: {e}")
            # Return an empty document with metadata to indicate failure
            return [Document(
                page_content="", 
                metadata={
                    "source": self.file_path,
                    "page": 0,
                    "extraction_method": "mistral_ocr_failed",
                    "error": str(e)
                }
            )]

    def _extract_with_mistral_ocr(self) -> List[Document]:
        """
        Extract text from PDF using Mistral OCR API.
        
        Returns:
            List of Document objects with OCR-extracted text
        """
        documents = []
        
        try:
            # Step 1: Upload PDF file for OCR processing
            logger.info(f"Uploading PDF file for OCR: {self.file_path}")
            
            with open(self.file_path, "rb") as pdf_file:
                uploaded_pdf = self.client.files.upload(
                    file={
                        "file_name": os.path.basename(self.file_path),
                        "content": pdf_file,
                    },
                    purpose="ocr"
                )
            
            logger.info(f"PDF uploaded successfully with ID: {uploaded_pdf.id}")
            
            # Step 2: Retrieve file information
            retrieved_file = self.client.files.retrieve(file_id=uploaded_pdf.id)
            logger.info(f"Retrieved file info: {retrieved_file.filename}, size: {retrieved_file.size_bytes} bytes")
            
            # Step 3: Get signed URL for OCR processing
            signed_url = self.client.files.get_signed_url(file_id=uploaded_pdf.id)
            logger.info(f"Generated signed URL for OCR processing")
            
            # Step 4: Process with Mistral OCR
            logger.info("Starting OCR processing with Mistral...")
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url,
                },
                include_image_base64=True
            )
            
            logger.info("OCR processing completed successfully")
            
            # Step 5: Extract text from OCR response
            if hasattr(ocr_response, 'text') and ocr_response.text:
                # Create a single document with all OCR text
                documents.append(Document(
                    page_content=ocr_response.text,
                    metadata={
                        "source": self.file_path,
                        "extraction_method": "mistral_ocr",
                        "file_id": uploaded_pdf.id,
                        "file_size": retrieved_file.size_bytes,
                        "original_filename": retrieved_file.filename
                    }
                ))
                logger.info(f"OCR extraction successful: {len(ocr_response.text)} characters extracted")
            
            # If the response has pages or segments, process them
            elif hasattr(ocr_response, 'pages') and ocr_response.pages:
                for page_num, page in enumerate(ocr_response.pages, 1):
                    if hasattr(page, 'text') and page.text.strip():
                        documents.append(Document(
                            page_content=page.text,
                            metadata={
                                "source": self.file_path,
                                "page": page_num,
                                "extraction_method": "mistral_ocr",
                                "file_id": uploaded_pdf.id,
                                "file_size": retrieved_file.size_bytes,
                                "original_filename": retrieved_file.filename
                            }
                        ))
                logger.info(f"OCR extraction successful: {len(documents)} pages processed")
            
            # If the response has a different structure, try to extract text content
            elif hasattr(ocr_response, 'content'):
                content_text = str(ocr_response.content)
                if content_text.strip():
                    documents.append(Document(
                        page_content=content_text,
                        metadata={
                            "source": self.file_path,
                            "extraction_method": "mistral_ocr",
                            "file_id": uploaded_pdf.id,
                            "file_size": retrieved_file.size_bytes,
                            "original_filename": retrieved_file.filename
                        }
                    ))
                    logger.info(f"OCR extraction successful: {len(content_text)} characters extracted")
            
            else:
                # If no text was extracted, create an empty document
                logger.warning("No text content found in OCR response")
                documents.append(Document(
                    page_content="",
                    metadata={
                        "source": self.file_path,
                        "extraction_method": "mistral_ocr_no_text",
                        "file_id": uploaded_pdf.id,
                        "file_size": retrieved_file.size_bytes,
                        "original_filename": retrieved_file.filename
                    }
                ))
            
            # Clean up: Delete the uploaded file from Mistral
            try:
                self.client.files.delete(file_id=uploaded_pdf.id)
                logger.info(f"Cleaned up uploaded file: {uploaded_pdf.id}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up uploaded file {uploaded_pdf.id}: {cleanup_error}")
                
        except Exception as e:
            logger.error(f"Mistral OCR processing failed: {e}")
            raise
        
        return documents

    @property 
    def source(self) -> str:
        """Return the source file path."""
        return self.file_path