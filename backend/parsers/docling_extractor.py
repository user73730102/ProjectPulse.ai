"""
parsers/docling_extractor.py

This file has been completely rewritten to use a HYBRID EXTRACTION architecture.
It uses PyPDF for lightning-fast text extraction on native digital pages.
If a page is completely blank (e.g. a scanned drawing), it isolates that page,
converts it to an image, and uses Tesseract OCR to read it.

This drops the processing time of a 1000-page document from hours down to seconds/minutes.
"""

import logging
from typing import List
import pypdf
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

class SpecChunk:
    def __init__(self, clause_number: str, title: str, content: str, page: int):
        self.clause_number = clause_number
        self.title = title
        self.content = content
        self.page = page

def extract_spec_chunks(pdf_path: str) -> List[SpecChunk]:
    """
    Parses a specification PDF using hybrid PyPDF + Tesseract.
    """
    logger.info(f"Extracting text from {pdf_path} using Hybrid PyPDF/Tesseract Engine")
    chunks = []
    
    try:
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        logger.info(f"Document has {total_pages} pages. Starting extraction...")
        
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            text = page.extract_text()
            
            # If PyPDF finds more than 50 characters, we assume it's a native digital text page
            if text and len(text.strip()) > 50:
                chunks.append(SpecChunk(
                    clause_number="0.0",
                    title=f"Page {page_num}",
                    content=text.strip(),
                    page=page_num
                ))
            else:
                # The page has no text! It is likely a scanned image or blueprint.
                # We use pdf2image to extract JUST this single page, and run Tesseract OCR on it.
                logger.info(f"Page {page_num} appears to be a scanned image. Running Tesseract OCR...")
                try:
                    # convert_from_path can extract specific pages (1-indexed)
                    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=200)
                    if images:
                        ocr_text = pytesseract.image_to_string(images[0])
                        if ocr_text and len(ocr_text.strip()) > 20:
                            chunks.append(SpecChunk(
                                clause_number="0.0",
                                title=f"Scanned Page {page_num}",
                                content=ocr_text.strip(),
                                page=page_num
                            ))
                        else:
                            # Even OCR failed to find text
                            chunks.append(SpecChunk(
                                clause_number="0.0",
                                title=f"Blank/Unreadable Page {page_num}",
                                content="This page appears to be a blueprint or drawing with no readable text.",
                                page=page_num
                            ))
                except Exception as ocr_e:
                    logger.error(f"OCR failed on page {page_num}: {ocr_e}")
                    chunks.append(SpecChunk(
                        clause_number="0.0",
                        title=f"OCR Failed Page {page_num}",
                        content="The AI failed to run OCR on this scanned page.",
                        page=page_num
                    ))
                    
        # Ultimate fallback if somehow nothing worked
        if not chunks:
            logger.warning("Document yielded 0 chunks. Appending a placeholder chunk.")
            chunks.append(SpecChunk(
                clause_number="0.0",
                title="Unreadable Document",
                content="The AI could not read any text from this document. It may be a scanned image with unrecognizable text, or completely blank.",
                page=1
            ))
            
    except Exception as e:
        logger.error(f"Failed to parse PDF with Hybrid Extractor: {e}", exc_info=True)
        chunks.append(SpecChunk(
            clause_number="ERROR",
            title="Extraction Failed",
            content=f"Failed to parse document: {str(e)}",
            page=1
        ))

    logger.info(f"Extracted {len(chunks)} chunks from {pdf_path}")
    return chunks
