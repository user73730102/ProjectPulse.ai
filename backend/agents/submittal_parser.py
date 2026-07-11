"""
agents/submittal_parser.py

Parses an uploaded Submittal PDF, extracts the raw text, and uses Gemini
to intelligently extract the vendor name, title, spec reference, and a summary
of all submitted values/parameters for later compliance checking.
"""

import logging
import json
import re
import pypdf
from typing import Dict, Any

from llm_router import call_llm, TaskType

logger = logging.getLogger(__name__)

def parse_submittal_pdf(pdf_path: str, original_filename: str) -> list[Dict[str, Any]]:
    """
    Extracts text from a submittal PDF and uses LLM to structure the metadata.
    Returns a list of products found in the document.
    """
    logger.info(f"Parsing submittal PDF: {pdf_path}")
    
    # 1. Extract text using PyPDF (fast and works for digital submittals)
    try:
        reader = pypdf.PdfReader(pdf_path)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text.strip())
        
        extracted_text = "\n".join(full_text)
        
        if not extracted_text.strip():
            logger.warning(f"No text extracted from {pdf_path}. It might be a scanned image.")
            extracted_text = f"Filename: {original_filename}\n(Scanned Document - No Text Available)"
            
    except Exception as e:
        logger.error(f"Failed to read submittal PDF: {e}")
        extracted_text = f"Filename: {original_filename}\n(Failed to read PDF)"

    extracted_text = extracted_text[:100000]

    # 2. Ask Gemini to extract structured JSON (Array of products)
    prompt = f"""You are a Data Centre EPC Quality Engineer parsing a vendor submittal document.
    
Read the following text extracted from a Submittal PDF (Cut-sheet / Product Data):
---
{extracted_text}
---

Vendors often include MULTIPLE different products or equipment types in a single catalog or submittal PDF.
Your task is to identify EACH distinct product/equipment being submitted and extract its information into a structured JSON array.

For each product found, extract:
1. "title": The name of the equipment or material (e.g. "Air Cooled Chiller", "Backup Generator")
2. "vendor_name": The name of the manufacturer or vendor.
3. "spec_section_ref": The project specification section this product is for (if mentioned, e.g. "16600" or "3.1.2"). Leave null if not found.
4. "submitted_value": A consolidated, highly detailed technical summary of all specifications, ratings, dimensions, and capacities provided for THIS SPECIFIC PRODUCT. Include ALL numbers, voltages, efficiencies, etc.

Output ONLY valid JSON in this exact format (an array of objects):
[
  {{
      "title": "<string>",
      "vendor_name": "<string>",
      "spec_section_ref": "<string or null>",
      "submitted_value": "<string>"
  }}
]
"""

    try:
        raw_response = call_llm(TaskType.REASONING, prompt)
        
        # Clean markdown
        raw_response = re.sub(r"```json|```", "", raw_response).strip()
        
        parsed_data = json.loads(raw_response)
        
        if not isinstance(parsed_data, list):
            parsed_data = [parsed_data]
            
        logger.info(f"Successfully parsed {len(parsed_data)} product(s) from submittal.")
        return parsed_data
        
    except Exception as e:
        logger.error(f"Failed to extract submittal data via LLM: {e}")
        # Fallback to basic info if LLM fails
        return [{
            "title": original_filename.replace(".pdf", ""),
            "vendor_name": "Unknown Vendor",
            "spec_section_ref": None,
            "submitted_value": extracted_text[:1000] + "\n...(truncated)",
        }]
