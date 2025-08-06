# OCR Enhancement for PDF Processing

This document describes the OCR (Optical Character Recognition) enhancement added to the RAG API for processing PDF documents using Mistral OCR API.

## Overview

The OCR enhancement enables the RAG API to extract text from ALL PDF documents using Mistral's state-of-the-art OCR service. This ensures consistent text extraction from both regular and scanned PDF documents.

## Key Features

- **Universal OCR Processing**: ALL PDFs are processed through Mistral OCR API
- **High Accuracy**: Leverages Mistral's advanced OCR model (`mistral-ocr-latest`)
- **Cloud-Based**: Uses Mistral's cloud OCR service for optimal performance
- **Automatic Cleanup**: Uploaded files are automatically cleaned up after processing
- **Comprehensive Metadata**: Preserves detailed processing information

## How It Works

1. **File Upload**: PDF is uploaded to Mistral for OCR processing
2. **Signed URL Generation**: Mistral provides a secure URL for processing
3. **OCR Processing**: Text is extracted using `mistral-ocr-latest` model
4. **Text Retrieval**: Extracted text is retrieved from the response
5. **Cleanup**: Uploaded files are automatically deleted from Mistral

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MISTRAL_API_KEY` | **Yes** | API key for Mistral OCR service |

### Example Configuration

```bash
# Required: Mistral API key for OCR processing
MISTRAL_API_KEY=your-mistral-api-key-here
```

## Usage

The OCR enhancement is automatically integrated into the existing document loading pipeline. All PDFs are processed through OCR:

```python
# This will automatically use Mistral OCR for ALL PDFs
from app.utils.document_loader import get_loader

loader, known_type, file_ext = get_loader("document.pdf", "application/pdf", "path/to/file.pdf")
documents = loader.load()
```

## API Endpoints

All existing PDF processing endpoints automatically use Mistral OCR:

- `POST /embed` - Upload and embed PDF documents
- `POST /local/embed` - Embed local PDF files  
- `POST /embed-upload` - Upload PDF files for embedding

## Implementation Details

### MistralOCRPDFLoader Class

The enhancement is implemented through the `MistralOCRPDFLoader` class in `app/utils/ocr_pdf_loader.py`. This class:

- Processes ALL PDFs through Mistral OCR API
- Handles file upload and signed URL generation
- Extracts text from OCR responses
- Preserves metadata and source information
- Automatically cleans up uploaded files

### Dependencies

- `mistralai`: Official Mistral AI Python client
- `langchain-community`: Document loading framework

## Performance Considerations

- **Cloud Processing**: OCR is handled by Mistral's cloud infrastructure
- **API Calls**: Each PDF requires upload and processing API calls
- **Network Dependency**: Requires internet connectivity to Mistral's API
- **Processing Time**: OCR processing time depends on document size and complexity

## Error Handling

The system gracefully handles OCR failures:

1. If API key is missing, loader initialization fails with clear error message
2. If OCR processing fails, returns error document with failure details
3. Network failures are caught and logged appropriately
4. Failed uploads are cleaned up when possible

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `MISTRAL_API_KEY` environment variable is set
2. **Network Issues**: Check internet connectivity to Mistral's API
3. **API Limits**: Monitor API usage limits and quotas
4. **Large Files**: Very large PDFs may exceed API limits

### Logs

OCR processing is logged at INFO level:
- Client initialization
- File upload status
- OCR processing progress
- Cleanup operations

Example log entries:
```
INFO - Mistral OCR client initialized successfully
INFO - PDF uploaded successfully with ID: abc123
INFO - OCR processing completed successfully
INFO - OCR extraction successful: 1234 characters extracted
INFO - Cleaned up uploaded file: abc123
```

## Security Considerations

- **API Key Protection**: Keep your Mistral API key secure and never commit it to version control
- **File Upload**: Files are temporarily uploaded to Mistral for processing
- **Automatic Cleanup**: Files are automatically deleted after processing
- **Secure URLs**: Signed URLs are used for secure file access

## Testing

The OCR enhancement includes comprehensive tests:

- Unit tests for Mistral OCR functionality (`tests/utils/test_ocr_pdf_loader.py`)
- Integration tests with the document loading pipeline
- Configuration testing
- Error handling verification
- Mock testing for API interactions

Run tests with:
```bash
python -m pytest tests/utils/test_ocr_pdf_loader.py -v
```

## API Rate Limits

Be aware of Mistral API rate limits:
- Monitor your API usage
- Consider implementing retry logic for rate limit errors
- Plan capacity based on expected PDF processing volume

## Future Enhancements

Potential improvements for future versions:

- Batch processing for multiple PDFs
- OCR confidence scoring and filtering
- Custom OCR model configuration
- Local caching of OCR results
- Retry logic for transient failures