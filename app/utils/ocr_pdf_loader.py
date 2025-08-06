# app/utils/ocr_pdf_loader.py
import os
import tempfile
import logging
from typing import List, Iterator, Union
import cv2
import numpy as np
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from rapidocr_onnxruntime import RapidOCR

# Use standard logging
logger = logging.getLogger(__name__)


class OCREnabledPDFLoader:
    """
    PDF Loader that can fallback to OCR when text extraction is insufficient.
    Uses PyPDFLoader first, then OCR if text content is minimal.
    """

    def __init__(
        self,
        file_path: str,
        extract_images: bool = False,
        use_ocr_fallback: bool = True,
        min_text_threshold: int = 50,
        ocr_config: dict = None,
    ):
        """
        Initialize the OCR-enabled PDF loader.

        Args:
            file_path: Path to the PDF file
            extract_images: Whether to extract images using PyPDFLoader
            use_ocr_fallback: Whether to use OCR when text extraction is insufficient
            min_text_threshold: Minimum number of characters to consider text extraction successful
            ocr_config: Configuration for RapidOCR
        """
        self.file_path = file_path
        self.extract_images = extract_images
        self.use_ocr_fallback = use_ocr_fallback
        self.min_text_threshold = min_text_threshold
        self.ocr_config = ocr_config or {}
        
        # Initialize OCR engine if needed
        self._ocr_engine = None
        if self.use_ocr_fallback:
            try:
                self._ocr_engine = RapidOCR(**self.ocr_config)
                logger.info("OCR engine initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OCR engine: {e}")
                self.use_ocr_fallback = False

    def load(self) -> List[Document]:
        """
        Load PDF documents, using OCR fallback if needed.
        
        Returns:
            List of Document objects
        """
        documents = []
        
        # First, try regular PDF text extraction
        try:
            pdf_loader = PyPDFLoader(self.file_path, extract_images=self.extract_images)
            pdf_documents = pdf_loader.load()
            
            # Check if we have sufficient text content
            total_text_length = sum(len(doc.page_content.strip()) for doc in pdf_documents)
            
            if total_text_length >= self.min_text_threshold:
                logger.info(f"Regular PDF extraction successful: {total_text_length} characters extracted")
                return pdf_documents
            else:
                logger.info(f"PDF extraction returned minimal text ({total_text_length} chars), attempting OCR fallback")
                
        except Exception as e:
            logger.warning(f"PDF text extraction failed: {e}, attempting OCR fallback")
        
        # Fallback to OCR if enabled and needed
        if self.use_ocr_fallback and self._ocr_engine:
            try:
                ocr_documents = self._extract_with_ocr()
                if ocr_documents:
                    logger.info(f"OCR extraction successful: {len(ocr_documents)} pages processed")
                    return ocr_documents
                else:
                    logger.warning("OCR extraction returned no results")
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
        
        # If all else fails, return the original PDF extraction (even if minimal)
        try:
            pdf_loader = PyPDFLoader(self.file_path, extract_images=self.extract_images)
            return pdf_loader.load()
        except Exception as e:
            logger.error(f"All PDF extraction methods failed: {e}")
            # Return an empty document with metadata to indicate failure
            return [Document(
                page_content="", 
                metadata={
                    "source": self.file_path,
                    "page": 0,
                    "extraction_method": "failed",
                    "error": str(e)
                }
            )]

    def _extract_with_ocr(self) -> List[Document]:
        """
        Extract text from PDF using OCR.
        
        Returns:
            List of Document objects with OCR-extracted text
        """
        documents = []
        
        try:
            # Convert PDF to images using OpenCV and pdf2image alternative
            # Since we don't want to add pdf2image dependency, we'll use a simpler approach
            # with PyPDF and image extraction combined with OCR
            
            # Try to use unstructured library's image extraction if available
            from unstructured.partition.pdf import partition_pdf
            
            # Use unstructured to extract images from PDF for OCR
            with tempfile.TemporaryDirectory() as temp_dir:
                elements = partition_pdf(
                    filename=self.file_path,
                    extract_images_in_pdf=True,
                    extract_image_block_types=["Image", "Table"],
                    extract_image_block_output_dir=temp_dir
                )
                
                # Process extracted images with OCR
                image_files = list(Path(temp_dir).glob("*.jpg")) + list(Path(temp_dir).glob("*.png"))
                
                if image_files:
                    for i, image_path in enumerate(sorted(image_files)):
                        try:
                            # Run OCR on the image
                            result, _ = self._ocr_engine(str(image_path))
                            
                            if result:
                                # Combine OCR results into text
                                page_text = self._combine_ocr_results(result)
                                
                                if page_text.strip():
                                    documents.append(Document(
                                        page_content=page_text,
                                        metadata={
                                            "source": self.file_path,
                                            "page": i + 1,
                                            "extraction_method": "ocr",
                                            "image_source": str(image_path)
                                        }
                                    ))
                        except Exception as e:
                            logger.warning(f"OCR failed for image {image_path}: {e}")
                            continue
                
                # Also try to extract text elements from unstructured
                text_elements = [elem for elem in elements if hasattr(elem, 'text') and elem.text.strip()]
                if text_elements and not documents:  # Only use if OCR didn't work
                    for i, element in enumerate(text_elements):
                        documents.append(Document(
                            page_content=element.text,
                            metadata={
                                "source": self.file_path,
                                "page": i + 1,
                                "extraction_method": "unstructured_text",
                                "element_type": type(element).__name__
                            }
                        ))
                
        except ImportError:
            logger.warning("Unstructured library not available for advanced PDF processing")
            # Fallback to simpler OCR approach would go here
            # For now, we'll rely on the unstructured library that's already in requirements
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
        
        return documents

    def _combine_ocr_results(self, ocr_results: List) -> str:
        """
        Combine OCR results into readable text.
        
        Args:
            ocr_results: Results from RapidOCR
            
        Returns:
            Combined text string
        """
        if not ocr_results:
            return ""
        
        # Sort results by position (top to bottom, left to right)
        sorted_results = sorted(ocr_results, key=lambda x: (x[0][0][1], x[0][0][0]))  # Sort by Y then X
        
        # Combine text with appropriate spacing
        text_lines = []
        current_line_y = None
        current_line_text = []
        
        for result in sorted_results:
            bbox, text, confidence = result
            y_pos = bbox[0][1]  # Top Y coordinate
            
            # If this is a new line (different Y position), start a new line
            if current_line_y is None or abs(y_pos - current_line_y) > 10:  # 10 pixel threshold
                if current_line_text:
                    text_lines.append(" ".join(current_line_text))
                current_line_text = [text]
                current_line_y = y_pos
            else:
                current_line_text.append(text)
        
        # Add the last line
        if current_line_text:
            text_lines.append(" ".join(current_line_text))
        
        return "\n".join(text_lines)

    @property 
    def source(self) -> str:
        """Return the source file path."""
        return self.file_path