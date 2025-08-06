# OCR Enhancement for PDF Processing

This document describes the OCR (Optical Character Recognition) enhancement added to the RAG API for processing scanned PDF documents.

## Overview

The OCR enhancement enables the RAG API to extract text from scanned PDF documents that contain images of text rather than selectable text. This is accomplished using the `rapidocr-onnxruntime` library, which is already included in the project dependencies.

## Key Features

- **Automatic Fallback**: When regular PDF text extraction yields insufficient content, the system automatically attempts OCR
- **Configurable Threshold**: You can set the minimum amount of text required before OCR fallback is triggered
- **Non-Breaking**: Existing functionality for text-based PDFs remains unchanged
- **Configurable**: OCR can be enabled/disabled via environment variables

## How It Works

1. **Regular PDF Processing**: First, the system attempts normal text extraction using PyPDFLoader
2. **Content Evaluation**: If the extracted text is below the configured threshold, OCR processing is triggered
3. **OCR Processing**: The PDF is processed using the unstructured library to extract images, then OCR is applied
4. **Text Combination**: OCR results are intelligently combined to maintain reading order

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PDF_USE_OCR_FALLBACK` | `True` | Enable/disable OCR fallback when text extraction is insufficient |
| `PDF_OCR_MIN_TEXT_THRESHOLD` | `50` | Minimum characters needed to consider text extraction successful |
| `PDF_EXTRACT_IMAGES` | `False` | Whether to extract images during PDF processing |

### Example Configuration

```bash
# Enable OCR fallback (default)
PDF_USE_OCR_FALLBACK=True

# Set threshold to 100 characters
PDF_OCR_MIN_TEXT_THRESHOLD=100

# Enable image extraction
PDF_EXTRACT_IMAGES=True
```

## Usage

The OCR enhancement is automatically integrated into the existing document loading pipeline. No code changes are required to use it:

```python
# This will automatically use OCR for scanned PDFs
from app.utils.document_loader import get_loader

loader, known_type, file_ext = get_loader("scanned_document.pdf", "application/pdf", "path/to/file.pdf")
documents = loader.load()
```

## API Endpoints

All existing PDF processing endpoints automatically benefit from OCR enhancement:

- `POST /embed` - Upload and embed PDF documents
- `POST /local/embed` - Embed local PDF files
- `POST /embed-upload` - Upload PDF files for embedding

## Implementation Details

### OCREnabledPDFLoader Class

The enhancement is implemented through the `OCREnabledPDFLoader` class in `app/utils/ocr_pdf_loader.py`. This class:

- Extends the existing PDF loading functionality
- Uses PyPDFLoader for regular text extraction
- Falls back to OCR when text content is insufficient
- Combines OCR results intelligently to maintain reading order
- Preserves metadata and source information

### Dependencies

- `rapidocr-onnxruntime`: OCR processing engine
- `unstructured`: Advanced PDF processing and image extraction
- `opencv-python-headless`: Image processing for OCR
- `langchain-community`: Document loading framework

## Performance Considerations

- **Regular PDFs**: No performance impact (uses standard PyPDFLoader)
- **Scanned PDFs**: OCR processing adds processing time but enables text extraction from previously inaccessible documents
- **Memory Usage**: OCR processing requires additional memory for image processing
- **Caching**: Consider implementing caching for frequently processed documents

## Error Handling

The system gracefully handles OCR failures:

1. If OCR initialization fails, the system falls back to regular PDF processing
2. If OCR processing fails, the original PDF extraction results are returned
3. Detailed logging helps with troubleshooting OCR issues

## Troubleshooting

### Common Issues

1. **OCR Not Working**: Check that `PDF_USE_OCR_FALLBACK=True` and required dependencies are installed
2. **Poor OCR Results**: Adjust `PDF_OCR_MIN_TEXT_THRESHOLD` to fine-tune when OCR is triggered
3. **Performance Issues**: Consider disabling OCR for documents that don't need it

### Logs

OCR processing is logged at INFO level:
- OCR engine initialization
- Fallback triggers
- Processing success/failure

Example log entries:
```
INFO - OCR engine initialized successfully
INFO - PDF extraction returned minimal text (25 chars), attempting OCR fallback
INFO - OCR extraction successful: 3 pages processed
```

## Future Enhancements

Potential improvements for future versions:

- Support for additional OCR engines
- Batch OCR processing for multiple documents
- OCR confidence scoring and filtering
- Custom OCR model configuration
- Image preprocessing for better OCR accuracy

## Testing

The OCR enhancement includes comprehensive tests:

- Unit tests for OCR functionality (`tests/utils/test_ocr_pdf_loader.py`)
- Integration tests with the document loading pipeline
- Configuration testing
- Error handling verification

Run tests with:
```bash
python -m pytest tests/utils/test_ocr_pdf_loader.py -v
```