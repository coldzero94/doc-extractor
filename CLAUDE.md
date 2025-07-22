# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **universal PDF data extraction pipeline** project in early development stage. The core principle is **"never fail"** - the system must extract something from any PDF input, targeting 0% failure rate through a multi-engine fallback architecture.

## Architecture

### Multi-Engine Fallback Strategy
```
PDF Input → docling (primary) → pdfplumber (fallback) → OCR (last resort) → Structured Output
```

The system uses **progressive degradation**:
1. **docling**: Primary engine for comprehensive PDF analysis and extraction
2. **pdfplumber**: Fallback for text-based PDFs when docling fails
3. **Tesseract/CLOVA OCR**: Last resort for scanned documents
4. **Fallback structure**: Always return something, even if minimal

### Core Technology Stack
- **Primary Language**: Python
- **Main Engine**: docling (PDF analysis and extraction)
- **Text Extraction**: pdfplumber  
- **OCR Engines**: Tesseract, CLOVA OCR
- **Data Processing**: pandas, regular expressions
- **Output Formats**: JSON, CSV

## Key Implementation Principles

### Error Handling Philosophy
```python
# CRITICAL: Never let the entire pipeline fail
for engine_name, extractor in engines:
    try:
        result = extractor(pdf_path)
        if is_valid_result(result):
            return result, engine_name
    except Exception as e:
        log_error(engine_name, e)
        continue

# Always return something, even if empty
return empty_result_structure(), "fallback"
```

### Processing Pipeline Structure
1. **Document Analysis**: Determine PDF type (text/scan/hybrid) and processing strategy
2. **Multi-Engine Extraction**: Try engines in order until success
3. **Result Validation**: Check extraction quality and confidence scores
4. **Output Standardization**: Always return consistent JSON structure with metadata

### Success Criteria
- **P0 Priority**: 100% success rate (never fail to extract something)
- **P1 Priority**: 80%+ accuracy for tables/images extraction  
- **P2 Priority**: 60%+ accuracy for metadata/layout information

## Expected Output Structure
All extractions must return standardized JSON with:
```json
{
  "extraction_info": {
    "status": "success|partial|fallback",
    "engine_used": ["docling", "tesseract"],
    "confidence": 0.85,
    "processing_time": "2.3s"
  },
  "content": {
    "raw_text": "...",
    "pages": [...],
    "tables": [...], 
    "images": [...]
  },
  "metadata": {
    "total_pages": 5,
    "text_extraction_method": "native|ocr|hybrid"
  }
}
```

## Development Guidelines

### Testing Strategy
Test with diverse PDF types:
- **Text PDFs**: Regular documents with selectable text
- **Scanned PDFs**: Image-only documents requiring OCR
- **Hybrid PDFs**: Mixed text and scanned content
- **Corrupted PDFs**: Damaged or password-protected files
- **Large PDFs**: 100+ page documents for performance testing

### Performance Targets
- **Processing Speed**: <2 seconds per page average
- **Text Accuracy**: 85%+ for text-based, 70%+ for scanned PDFs
- **Memory Usage**: Handle large files without memory overflow

### Code Organization
When implementing, follow the planned structure:
- Separate modules for each extraction engine
- Centralized error handling and logging
- Configurable fallback chain
- Comprehensive result validation
- Batch processing capabilities

## Current Status
**Project is in planning phase** - no source code exists yet. All implementation needs to be built from scratch following the architectural guidelines in `docs/data_extractor.md`.