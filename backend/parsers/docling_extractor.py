"""
parsers/docling_extractor.py (Renamed internally to use pypdf for MSYS2 compatibility)

Extracts text from PDF spec documents and splits them into section chunks.
We use pure Python `pypdf` here to avoid C-extension compilation issues on MSYS2 Windows.
For production (Step 6), this should be swapped back to `docling` for accurate table/layout parsing.
"""

import logging
from typing import List
from pypdf import PdfReader
import re

logger = logging.getLogger(__name__)

class SpecChunk:
    def __init__(self, clause_number: str, title: str, content: str, page: int):
        self.clause_number = clause_number
        self.title = title
        self.content = content
        self.page = page


def extract_spec_chunks(pdf_path: str) -> List[SpecChunk]:
    """
    Parses a specification PDF using pypdf.
    Attempts to identify clause numbers like '1.1', '2.3.4' to split the text.
    """
    logger.info(f"Extracting text from {pdf_path} using pypdf")
    chunks = []
    
    try:
        reader = PdfReader(pdf_path)
        current_clause = None
        current_title = None
        current_content = []
        current_page = 1
        
        # Simple regex for clause numbers like "1.2", "1.2.3", "PART 1"
        clause_pattern = re.compile(r"^(\d+\.\d+(?:\.\d+)?|PART \d+)\s*(.*)", re.IGNORECASE)

        for i, page in enumerate(reader.pages):
            page_num = i + 1
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                match = clause_pattern.match(line)
                if match:
                    # Save previous chunk
                    if current_clause and current_content:
                        chunks.append(SpecChunk(
                            clause_number=current_clause,
                            title=current_title or "Untitled Section",
                            content="\n".join(current_content),
                            page=current_page
                        ))
                    
                    # Start new chunk
                    current_clause = match.group(1).strip()
                    current_title = match.group(2).strip()
                    current_content = [line]
                    current_page = page_num
                else:
                    if not current_clause:
                        # Top of document before first clause
                        current_clause = "0.0"
                        current_title = "General"
                        current_page = page_num
                    current_content.append(line)
                    
        # Add final chunk
        if current_clause and current_content:
            chunks.append(SpecChunk(
                clause_number=current_clause,
                title=current_title or "Untitled Section",
                content="\n".join(current_content),
                page=current_page
            ))
            
    except Exception as e:
        logger.error(f"Failed to parse PDF with pypdf: {e}")
        # Return at least one chunk so the system doesn't break
        chunks.append(SpecChunk(
            clause_number="ERROR",
            title="Extraction Failed",
            content=f"Failed to parse document: {str(e)}",
            page=1
        ))

    logger.info(f"Extracted {len(chunks)} chunks from {pdf_path}")
    return chunks
