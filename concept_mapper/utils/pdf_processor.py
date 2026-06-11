"""
PDF Processor Module
Extracts text from PDF files using PyMuPDF
"""

import fitz  # PyMuPDF
from typing import Dict, List, Tuple


class PDFProcessor:
    """Process PDF files and extract text with structure preservation."""
    
    def __init__(self):
        self.doc = None
    
    def open_pdf(self, pdf_path: str) -> bool:
        """Open a PDF file."""
        try:
            self.doc = fitz.open(pdf_path)
            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False
    
    def close_pdf(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()
            self.doc = None
    
    def get_page_count(self) -> int:
        """Get total number of pages."""
        if self.doc:
            return len(self.doc)
        return 0
    
    def extract_text_from_page(self, page_num: int) -> str:
        """Extract text from a specific page."""
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return ""
        
        page = self.doc[page_num]
        return page.get_text()
    
    def extract_all_text(self) -> str:
        """Extract text from all pages."""
        if not self.doc:
            return ""
        
        full_text = ""
        for page_num in range(len(self.doc)):
            page_text = self.extract_text_from_page(page_num)
            full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
            full_text += page_text
        
        return full_text
    
    def extract_text_with_structure(self) -> Dict:
        """
        Extract text while preserving chapter/section structure.
        Returns structured data with pages and sections.
        """
        if not self.doc:
            return {"pages": [], "full_text": ""}
        
        pages_data = []
        full_text = ""
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()
            
            # Detect chapter/section headers (simple heuristic)
            sections = self._detect_sections(text, page_num + 1)
            
            page_info = {
                "page_number": page_num + 1,
                "text": text,
                "sections": sections
            }
            pages_data.append(page_info)
            full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n{text}"
        
        return {
            "pages": pages_data,
            "full_text": full_text,
            "total_pages": len(self.doc)
        }
    
    def _detect_sections(self, text: str, page_num: int) -> List[Dict]:
        """
        Detect section headers in text.
        Simple heuristic: lines that are short, capitalized, or numbered.
        """
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if it looks like a header
            is_header = False
            
            # Short line (likely a title)
            if len(line) < 80 and len(line) > 5:
                # All caps or title case
                if line.isupper() or line[0].isupper():
                    is_header = True
            
            # Numbered section (e.g., "Chapter 1", "2.3 Section Title")
            if any(pattern in line.lower() for pattern in 
                   ['chapter', 'section', 'part', 'unit']):
                is_header = True
            
            if is_header:
                sections.append({
                    "title": line,
                    "line_number": i,
                    "page": page_num
                })
        
        return sections
    
    def extract_metadata(self) -> Dict:
        """Extract PDF metadata."""
        if not self.doc:
            return {}
        
        metadata = self.doc.metadata
        return {
            "title": metadata.get('title', ''),
            "author": metadata.get('author', ''),
            "subject": metadata.get('subject', ''),
            "creator": metadata.get('creator', ''),
            "producer": metadata.get('producer', ''),
            "creation_date": metadata.get('creationDate', ''),
            "modification_date": metadata.get('modDate', ''),
            "page_count": len(self.doc)
        }


def process_pdf(pdf_path: str) -> Tuple[str, Dict]:
    """
    Convenience function to process a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (full_text, metadata)
    """
    processor = PDFProcessor()
    
    if not processor.open_pdf(pdf_path):
        return "", {}
    
    result = processor.extract_text_with_structure()
    metadata = processor.extract_metadata()
    
    processor.close_pdf()
    
    return result["full_text"], metadata


if __name__ == "__main__":
    # Test the PDF processor
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        text, metadata = process_pdf(pdf_file)
        
        print(f"PDF Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print(f"\nExtracted {len(text)} characters")
        print(f"\nFirst 500 characters:\n{text[:500]}")
    else:
        print("Usage: python pdf_processor.py <pdf_file>")
