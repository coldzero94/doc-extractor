"""
PDF Universal Data Extractor
Main extraction pipeline with multi-engine fallback strategy
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# PDF processing libraries
import pdfplumber
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("docling not available, falling back to other engines")

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract not available, OCR features disabled")


@dataclass
class ExtractionResult:
    """Standardized extraction result structure"""
    extraction_info: Dict[str, Any]
    content: Dict[str, Any]
    metadata: Dict[str, Any]


class PDFAnalyzer:
    """Analyze PDF to determine processing strategy"""
    
    @staticmethod
    def analyze_pdf(file_path: str) -> Dict[str, Any]:
        """
        Analyze PDF characteristics to determine optimal processing strategy
        Returns analysis result with processing recommendations
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                has_text = False
                has_images = False
                estimated_scan_pages = []
                
                # Sample first few pages for analysis
                sample_pages = min(5, total_pages)
                
                for i, page in enumerate(pdf.pages[:sample_pages]):
                    text = page.extract_text()
                    if text and text.strip():
                        has_text = True
                    
                    # Check for images
                    if page.images:
                        has_images = True
                    
                    # Estimate if page is scanned (little/no extractable text)
                    if not text or len(text.strip()) < 50:
                        estimated_scan_pages.append(i)
                
                # Determine processing strategy
                if not has_text and has_images:
                    strategy = "ocr_heavy"
                elif has_text and not has_images:
                    strategy = "text_extraction"
                else:
                    strategy = "hybrid"
                
                file_size = Path(file_path).stat().st_size
                
                return {
                    "pages": total_pages,
                    "has_text": has_text,
                    "has_images": has_images,
                    "estimated_scan_pages": estimated_scan_pages,
                    "file_size": file_size,
                    "processing_strategy": strategy
                }
                
        except Exception as e:
            logging.error(f"PDF analysis failed: {e}")
            # Return minimal analysis even if failed
            return {
                "pages": 1,
                "has_text": False,
                "has_images": False,
                "estimated_scan_pages": [0],
                "file_size": 0,
                "processing_strategy": "fallback"
            }


class MultiEngineExtractor:
    """Main extraction class with multi-engine fallback"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engines = [
            ("docling", self._docling_extract),
            ("pdfplumber", self._pdfplumber_extract),
            ("tesseract", self._tesseract_extract)
        ]
    
    def extract(self, pdf_path: str) -> ExtractionResult:
        """
        Main extraction method with fallback strategy
        Never fails - always returns something
        """
        start_time = time.time()
        
        # Step 1: Analyze PDF
        analysis = PDFAnalyzer.analyze_pdf(pdf_path)
        
        # Step 2: Try extraction engines in order
        for engine_name, extractor in self.engines:
            try:
                self.logger.info(f"Trying {engine_name} extraction for {pdf_path}")
                result = extractor(pdf_path, analysis)
                
                if self._is_valid_result(result):
                    processing_time = time.time() - start_time
                    
                    return ExtractionResult(
                        extraction_info={
                            "file_name": Path(pdf_path).name,
                            "processing_time": f"{processing_time:.2f}s",
                            "engine_used": [engine_name],
                            "status": "success",
                            "confidence": result.get("confidence", 0.8)
                        },
                        content=result.get("content", {}),
                        metadata=result.get("metadata", {})
                    )
                    
            except Exception as e:
                self.logger.error(f"{engine_name} extraction failed: {e}")
                continue
        
        # Step 3: Last resort - return minimal structure
        self.logger.warning(f"All engines failed for {pdf_path}, returning fallback result")
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            extraction_info={
                "file_name": Path(pdf_path).name,
                "processing_time": f"{processing_time:.2f}s",
                "engine_used": ["fallback"],
                "status": "fallback",
                "confidence": 0.1
            },
            content={
                "raw_text": f"Failed to extract content from {Path(pdf_path).name}",
                "pages": [],
                "tables": [],
                "images": []
            },
            metadata={
                "total_pages": analysis.get("pages", 0),
                "text_extraction_method": "fallback"
            }
        )
    
    def _docling_extract(self, pdf_path: str, analysis: Dict) -> Dict[str, Any]:
        """Extract using docling engine"""
        if not DOCLING_AVAILABLE:
            raise ImportError("docling not available")
        
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        # Convert docling result to standardized format
        return {
            "content": {
                "raw_text": result.document.export_to_text(),
                "pages": [],  # TODO: Extract page-by-page content
                "tables": [],  # TODO: Extract tables
                "images": []   # TODO: Extract images
            },
            "metadata": {
                "total_pages": analysis.get("pages", 0),
                "text_extraction_method": "native"
            },
            "confidence": 0.9
        }
    
    def _pdfplumber_extract(self, pdf_path: str, analysis: Dict) -> Dict[str, Any]:
        """Extract using pdfplumber engine"""
        with pdfplumber.open(pdf_path) as pdf:
            pages_content = []
            tables = []
            raw_text = ""
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                raw_text += page_text + "\n"
                
                pages_content.append({
                    "page_num": i + 1,
                    "text": page_text,
                    "tables": [],
                    "images": []
                })
                
                # Extract tables
                page_tables = page.extract_tables()
                if page_tables:
                    for j, table in enumerate(page_tables):
                        tables.append({
                            "page": i + 1,
                            "table_id": j,
                            "data": table
                        })
            
            return {
                "content": {
                    "raw_text": raw_text,
                    "pages": pages_content,
                    "tables": tables,
                    "images": []
                },
                "metadata": {
                    "total_pages": len(pdf.pages),
                    "text_extraction_method": "native"
                },
                "confidence": 0.8 if raw_text.strip() else 0.3
            }
    
    def _tesseract_extract(self, pdf_path: str, analysis: Dict) -> Dict[str, Any]:
        """Extract using OCR (last resort)"""
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract not available")
        
        # Convert PDF to images and OCR each page
        # This is a simplified implementation
        raw_text = "OCR extraction placeholder - implementation needed"
        
        return {
            "content": {
                "raw_text": raw_text,
                "pages": [],
                "tables": [],
                "images": []
            },
            "metadata": {
                "total_pages": analysis.get("pages", 0),
                "text_extraction_method": "ocr"
            },
            "confidence": 0.6
        }
    
    def _is_valid_result(self, result: Dict) -> bool:
        """Validate extraction result quality"""
        if not result or not isinstance(result, dict):
            return False
        
        content = result.get("content", {})
        raw_text = content.get("raw_text", "")
        
        # Must have some text content
        return bool(raw_text and raw_text.strip())


def extract_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Main API function for PDF extraction
    Always returns a result, never fails completely
    """
    extractor = MultiEngineExtractor()
    result = extractor.extract(pdf_path)
    
    # Convert to dictionary for JSON serialization
    return {
        "extraction_info": result.extraction_info,
        "content": result.content,
        "metadata": result.metadata
    }


def save_extraction_results(pdf_path: str, result: Dict[str, Any]) -> Tuple[str, str]:
    """
    Save extraction results to JSON and TXT files
    Returns paths of saved files
    """
    pdf_path_obj = Path(pdf_path)
    
    # Save as JSON file
    json_output = pdf_path_obj.with_suffix('.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Save raw text as TXT file
    txt_output = pdf_path_obj.with_suffix('.txt')
    with open(txt_output, 'w', encoding='utf-8') as f:
        f.write(result['content']['raw_text'])
    
    return str(json_output), str(txt_output)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python extractor.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Extract data
    result = extract_pdf(pdf_file)
    
    # Save to files
    json_path, txt_path = save_extraction_results(pdf_file, result)
    print(f"JSON output saved to: {json_path}")
    print(f"Text output saved to: {txt_path}")
    
    # Print result as JSON to console
    print(json.dumps(result, indent=2, ensure_ascii=False))