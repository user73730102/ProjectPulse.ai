"""
parsers/docling_extractor.py

Extracts text from PDF spec documents and splits them into hierarchical section chunks using IBM Docling.
This production-grade parser natively understands document layouts, tables, and nested headers.
"""

import logging
from typing import List

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.chunking import HierarchicalChunker
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.document import InputFormat

logger = logging.getLogger(__name__)

class SpecChunk:
    def __init__(self, clause_number: str, title: str, content: str, page: int):
        self.clause_number = clause_number
        self.title = title
        self.content = content
        self.page = page


def extract_spec_chunks(pdf_path: str) -> List[SpecChunk]:
    """
    Parses a specification PDF using IBM Docling.
    Uses HierarchicalChunker to intelligently chunk the document based on its visual structure.
    """
    logger.info(f"Extracting text from {pdf_path} using Docling")
    chunks = []
    
    try:
        # Initialize Docling with default options (which includes OCR)
        converter = DocumentConverter()
        chunker = HierarchicalChunker()
        
        # Parse the document (this downloads OCR models on first run and is CPU intensive)
        result = converter.convert(pdf_path)
        doc = result.document
        
        # Generate semantic chunks
        doc_chunks = list(chunker.chunk(doc))
        
        if not doc_chunks:
            # Fallback for simple documents where HierarchicalChunker yields nothing
            logger.warning("HierarchicalChunker returned empty. Falling back to raw Markdown export.")
            md_text = doc.export_to_markdown()
            if md_text and md_text.strip():
                chunks.append(SpecChunk(
                    clause_number="0.0",
                    title="Document Content",
                    content=md_text.strip(),
                    page=1
                ))
        
        for chunk in doc_chunks:
            # Safely extract metadata provided by Docling
            title = "Untitled Section"
            clause_number = "0.0"
            page_num = 1
            
            if chunk.meta:
                # Get heading string if available
                if getattr(chunk.meta, 'heading', None):
                    title = chunk.meta.heading
                
                # Try to extract the first page number from provenance items
                if getattr(chunk.meta, 'doc_items', None):
                    for item in chunk.meta.doc_items:
                        if hasattr(item, 'prov') and item.prov:
                            # docling's provenance typically has page_no
                            page_num = item.prov[0].page_no
                            break
                            
            chunks.append(SpecChunk(
                clause_number=clause_number,
                title=title,
                content=chunk.text,
                page=page_num
            ))
            
    except Exception as e:
        logger.error(f"Failed to parse PDF with Docling: {e}", exc_info=True)
        # Return at least one chunk so the system doesn't break completely
        chunks.append(SpecChunk(
            clause_number="ERROR",
            title="Extraction Failed",
            content=f"Failed to parse document: {str(e)}",
            page=1
        ))

    logger.info(f"Extracted {len(chunks)} chunks from {pdf_path}")
    return chunks
