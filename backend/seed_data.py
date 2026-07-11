"""
seed_data.py — Populates the database with realistic Data Centre EPC sample data.

Generates:
  - 1 admin user + 3 role users (engineer, auditor, contractor)
  - 2 source Documents (a spec PDF and a submittal PDF — file paths are mocked)
  - 10 SpecSection clauses covering real DC EPC domains (UPS, cooling, power, fire)
  - 3 Submittals with realistic vendor data
  - 3 NCRs (2 AI-drafted, 1 approved) representing real compliance deviations
  - 2 RFIEntry records

Usage:
    python seed_data.py

Run AFTER init_db.py.
"""

from database import SessionLocal
from models import (
    User, Document, SpecSection, Submittal, NonConformanceReport, RFIEntry,
    UserRole, DocumentType, SubmittalStatus, NCRStatus
)
from auth import get_password_hash
from datetime import datetime, timezone


SPEC_CLAUSES = [
    {
        "clause_number": "16600-3.1.1",
        "clause_title": "UPS System — Battery Runtime",
        "content": (
            "The Uninterruptible Power Supply (UPS) system shall provide a minimum battery "
            "backup runtime of 15 minutes at full rated load (500 kVA) under all operating "
            "conditions. Battery strings shall be valve-regulated lead-acid (VRLA) type rated "
            "for 10-year design life. Runtime shall be verified by factory acceptance test (FAT) "
            "documentation submitted prior to delivery."
        ),
        "page_number": 34,
    },
    {
        "clause_number": "16600-3.1.2",
        "clause_title": "UPS System — Efficiency",
        "content": (
            "The UPS system shall achieve a minimum efficiency of 96% in double-conversion "
            "mode at 100% load and 97% in eco-mode. Efficiency data shall be third-party "
            "verified and submitted as part of the product data submittal."
        ),
        "page_number": 35,
    },
    {
        "clause_number": "15700-3.2.1",
        "clause_title": "Precision Air Conditioning — Cooling Capacity",
        "content": (
            "Computer Room Air Conditioning (CRAC) units shall provide a minimum sensible "
            "cooling capacity of 60 kW per unit. Units shall be downflow configuration with "
            "raised floor plenum supply. Design airflow shall not exceed 8°C supply-return "
            "differential at full IT load. Total cooling redundancy shall be N+1."
        ),
        "page_number": 51,
    },
    {
        "clause_number": "15700-3.2.2",
        "clause_title": "Precision Air Conditioning — Refrigerant",
        "content": (
            "All CRAC units shall use R-410A refrigerant or approved HFO equivalent (R-32 "
            "or R-454B). R-22 refrigerants are strictly prohibited. Refrigerant type and "
            "GWP value shall be declared in the product submittal."
        ),
        "page_number": 52,
    },
    {
        "clause_number": "16100-2.3.1",
        "clause_title": "Power Distribution Unit — Rating",
        "content": (
            "Branch circuit PDUs shall be rated for a minimum of 42U rack-mount form factor. "
            "Input rating: 3-phase 400V, 32A. Total outlet capacity shall not be less than "
            "24 x C13 and 12 x C19 outlets per PDU. Each outlet shall include individual "
            "metering with ±1% accuracy."
        ),
        "page_number": 78,
    },
    {
        "clause_number": "16100-2.3.2",
        "clause_title": "Power Distribution Unit — Remote Monitoring",
        "content": (
            "PDUs shall support SNMP v2c and v3, Modbus TCP, and RESTful API for integration "
            "with the DCIM platform. Real-time per-outlet power monitoring (kW, kVAr, PF) "
            "shall be available. Data retention on-device shall be a minimum of 30 days at "
            "1-minute interval granularity."
        ),
        "page_number": 79,
    },
    {
        "clause_number": "15300-4.1.1",
        "clause_title": "Fire Suppression — Agent Type",
        "content": (
            "The data hall fire suppression system shall use a clean agent gaseous system "
            "compliant with NFPA 2001. Approved agents: FM-200 (HFC-227ea) or Novec 1230 "
            "(FK-5-1-12). Halon-based systems are prohibited. Design concentration shall "
            "achieve a 10% safety margin above the minimum extinguishing concentration (MEC) "
            "for Class C fires."
        ),
        "page_number": 112,
    },
    {
        "clause_number": "15300-4.1.2",
        "clause_title": "Fire Suppression — Discharge Time",
        "content": (
            "The clean agent shall be discharged to achieve design concentration within "
            "10 seconds of detection signal. Nozzle sizing and pipe network hydraulic "
            "calculations shall be submitted for review as part of the fire protection "
            "submittal package."
        ),
        "page_number": 113,
    },
    {
        "clause_number": "16700-2.1.1",
        "clause_title": "Generator — Rated Capacity",
        "content": (
            "Diesel generators shall be rated at a minimum Prime Power rating of 2000 kVA "
            "at 0.8 power factor, 400V, 50Hz, with 10% overload capacity for 1 hour in "
            "any 12-hour period. Generators shall comply with BS ISO 8528-1. Fuel tank "
            "capacity shall provide minimum 24-hour runtime at 75% load."
        ),
        "page_number": 145,
    },
    {
        "clause_number": "16700-2.1.2",
        "clause_title": "Generator — Transfer Time",
        "content": (
            "The Automatic Transfer Switch (ATS) shall transfer load to generator within "
            "10 seconds of utility failure detection. Generator shall reach rated voltage "
            "and frequency within 10 seconds of start signal. Total transfer time (utility "
            "failure to full load on generator) shall not exceed 20 seconds."
        ),
        "page_number": 146,
    },
]

SUBMITTALS = [
    {
        "submittal_number": "SUB-UPS-001",
        "title": "UPS System Product Data — Eaton 9PX 500kVA",
        "vendor_name": "Eaton Power Technologies",
        "spec_section_ref": "16600",
        "submitted_value": (
            "Eaton 9PX 500kVA UPS. Battery runtime: 10 minutes at full load (VRLA, 7-year "
            "design life). Double-conversion efficiency: 95.5%. Eco-mode efficiency: 98%."
        ),
        "status": SubmittalStatus.under_review,
    },
    {
        "submittal_number": "SUB-CRAC-001",
        "title": "CRAC Unit Product Data — Vertiv Liebert PDX 60kW",
        "vendor_name": "Vertiv Group",
        "spec_section_ref": "15700",
        "submitted_value": (
            "Vertiv Liebert PDX. Cooling capacity: 62 kW sensible. Downflow configuration. "
            "Refrigerant: R-410A. Airflow: 7.5°C supply-return differential at full load. "
            "N+1 redundancy confirmed."
        ),
        "status": SubmittalStatus.approved,
    },
    {
        "submittal_number": "SUB-PDU-001",
        "title": "PDU Product Data — Raritan PX3 Intelligent PDU",
        "vendor_name": "Raritan Inc.",
        "spec_section_ref": "16100",
        "submitted_value": (
            "Raritan PX3-5000 Series. Input: 3-phase 400V, 32A. Outlets: 24 x C13, "
            "12 x C19. Supports SNMP v2c only (SNMPv3 not supported on this model). "
            "Per-outlet metering ±1.5% accuracy. Data retention: 7 days at 5-minute intervals."
        ),
        "status": SubmittalStatus.rejected,
    },
]

NCRS = [
    {
        "ncr_number": "NCR-2024-001",
        "required_value": "Minimum 15 minutes battery runtime at full rated load (500 kVA). VRLA batteries, 10-year design life.",
        "submitted_value": "10 minutes battery runtime at full load. VRLA batteries, 7-year design life.",
        "deviation_description": (
            "CRITICAL DEVIATION: The submitted UPS (Eaton 9PX) provides only 10 minutes of "
            "battery runtime against the specified 15 minutes — a 33% shortfall. Additionally, "
            "the submitted battery design life is 7 years, which does not meet the 10-year "
            "specification requirement. Vendor must either (a) increase the number of battery "
            "strings to achieve the required 15-minute runtime, or (b) propose an alternative "
            "UPS configuration with compliant battery specifications."
        ),
        "severity": "Critical",
        "status": NCRStatus.pending_review,
        "ai_confidence": 0.97,
        "submittal_ref": "SUB-UPS-001",
        "clause_ref": "16600-3.1.1",
    },
    {
        "ncr_number": "NCR-2024-002",
        "required_value": "UPS double-conversion efficiency minimum 96% at 100% load.",
        "submitted_value": "UPS double-conversion efficiency 95.5% at full load.",
        "deviation_description": (
            "MAJOR DEVIATION: The submitted UPS efficiency of 95.5% in double-conversion mode "
            "falls below the specified minimum of 96% at 100% load. While the eco-mode "
            "efficiency (98%) exceeds the spec, the core double-conversion mode requirement "
            "is not met. Vendor to provide test certification from an accredited third-party "
            "lab demonstrating 96%+ efficiency, or propose an alternative compliant model."
        ),
        "severity": "Major",
        "status": NCRStatus.draft,
        "ai_confidence": 0.91,
        "submittal_ref": "SUB-UPS-001",
        "clause_ref": "16600-3.1.2",
    },
    {
        "ncr_number": "NCR-2024-003",
        "required_value": "SNMP v2c and v3, Modbus TCP, RESTful API. Per-outlet metering ±1% accuracy. 30-day data retention at 1-minute intervals.",
        "submitted_value": "SNMP v2c only. Per-outlet metering ±1.5% accuracy. 7-day data retention at 5-minute intervals.",
        "deviation_description": (
            "MAJOR DEVIATION (3 non-conformances): "
            "(1) Protocol: Submitted PDU supports SNMP v2c only; SNMPv3 and RESTful API are "
            "required by spec 16100-2.3.2. "
            "(2) Accuracy: Submitted metering accuracy of ±1.5% does not meet the ±1% "
            "specification. "
            "(3) Data retention: 7 days at 5-minute intervals does not meet the 30-day "
            "at 1-minute interval requirement. Vendor to propose an alternative PDU model "
            "compliant with all three requirements."
        ),
        "severity": "Major",
        "status": NCRStatus.approved,
        "ai_confidence": 0.95,
        "submittal_ref": "SUB-PDU-001",
        "clause_ref": "16100-2.3.2",
    },
]

RFI_ENTRIES = [
    {
        "question": "Why was the UPS submittal SUB-UPS-001 rejected?",
        "answer": (
            "Submittal SUB-UPS-001 (Eaton 9PX 500kVA) was flagged with two NCRs:\n\n"
            "1. **NCR-2024-001 (Critical)**: The submitted UPS provides only 10 minutes of battery "
            "runtime at full load, against the specified minimum of 15 minutes per clause 16600-3.1.1. "
            "The battery design life (7 years submitted vs. 10 years required) is also non-conformant.\n\n"
            "2. **NCR-2024-002 (Major)**: The double-conversion efficiency is 95.5%, below the 96% "
            "minimum specified in clause 16600-3.1.2.\n\n"
            "The submittal is currently under review pending vendor response to both NCRs."
        ),
        "citations": [
            {"document_id": 1, "clause_id": 1, "page": 34, "excerpt": "minimum battery backup runtime of 15 minutes at full rated load"},
            {"document_id": 1, "clause_id": 2, "page": 35, "excerpt": "minimum efficiency of 96% in double-conversion mode"},
        ],
        "retrieved_chunk_ids": [1, 2],
    },
    {
        "question": "What refrigerant types are approved for CRAC units?",
        "answer": (
            "Per specification clause 15700-3.2.2 (page 52), the approved refrigerants for CRAC units are:\n\n"
            "- **R-410A** (the current standard)\n"
            "- **R-32** (approved HFO equivalent)\n"
            "- **R-454B** (approved HFO equivalent)\n\n"
            "R-22 refrigerants are **strictly prohibited**. The refrigerant type and its GWP value "
            "must be declared in the product submittal. The CRAC submittal SUB-CRAC-001 (Vertiv Liebert PDX) "
            "was approved as it correctly specified R-410A."
        ),
        "citations": [
            {"document_id": 1, "clause_id": 4, "page": 52, "excerpt": "R-410A refrigerant or approved HFO equivalent. R-22 refrigerants are strictly prohibited."},
        ],
        "retrieved_chunk_ids": [4],
    },
]


def seed():
    db = SessionLocal()
    try:
        # Check if already seeded
        existing_admin = db.query(User).filter(User.email == "admin@projectpulse.ai").first()
        if existing_admin:
            print("Database already seeded. Skipping seeding.")
            return

        # ---- Users ----
        print("Seeding users...")
        users = {
            "admin": User(email="admin@projectpulse.ai", full_name="Admin User", hashed_password=get_password_hash("admin123"), role=UserRole.pm, is_active=True),
            "engineer": User(email="engineer@projectpulse.ai", full_name="Sarah Chen", hashed_password=get_password_hash("engineer123"), role=UserRole.engineer, is_active=True),
            "auditor": User(email="auditor@projectpulse.ai", full_name="James Okafor", hashed_password=get_password_hash("auditor123"), role=UserRole.auditor, is_active=True),
            "contractor": User(email="contractor@eaton.com", full_name="Mike Patel", hashed_password=get_password_hash("contractor123"), role=UserRole.contractor, is_active=True),
        }
        for u in users.values():
            db.add(u)
        db.flush()

        # ---- Documents ----
        print("Seeding documents...")
        spec_doc = Document(
            filename="DC-EPC-Specification-Rev3.pdf",
            original_name="DC-EPC-Specification-Rev3.pdf",
            file_path="uploads/specs/DC-EPC-Specification-Rev3.pdf",  # Mocked path
            doc_type=DocumentType.specification,
            project_id="DC-PROJ-2024-001",
            uploaded_by=users["admin"].id,
            page_count=180,
            is_processed=True,
        )
        submittal_doc = Document(
            filename="SUB-UPS-001-Eaton9PX-ProductData.pdf",
            original_name="Eaton 9PX 500kVA Product Datasheet.pdf",
            file_path="uploads/submittals/SUB-UPS-001-Eaton9PX-ProductData.pdf",
            doc_type=DocumentType.submittal,
            project_id="DC-PROJ-2024-001",
            uploaded_by=users["contractor"].id,
            page_count=12,
            is_processed=True,
        )
        db.add(spec_doc)
        db.add(submittal_doc)
        db.flush()

        # ---- SpecSections ----
        print("Seeding spec sections (clauses)...")
        clause_map = {}
        for i, clause_data in enumerate(SPEC_CLAUSES):
            section = SpecSection(
                document_id=spec_doc.id,
                clause_number=clause_data["clause_number"],
                clause_title=clause_data["clause_title"],
                content=clause_data["content"],
                page_number=clause_data["page_number"],
                embedding=None,  # Embeddings generated by ingestion worker, not seed
                chunk_index=i,
            )
            db.add(section)
            db.flush()
            clause_map[clause_data["clause_number"]] = section

        # ---- Submittals ----
        print("Seeding submittals...")
        submittal_map = {}
        for sub_data in SUBMITTALS:
            sub = Submittal(
                submittal_number=sub_data["submittal_number"],
                title=sub_data["title"],
                vendor_name=sub_data["vendor_name"],
                document_id=submittal_doc.id if "UPS" in sub_data["submittal_number"] else None,
                spec_section_ref=sub_data["spec_section_ref"],
                submitted_value=sub_data["submitted_value"],
                status=sub_data["status"],
            )
            db.add(sub)
            db.flush()
            submittal_map[sub_data["submittal_number"]] = sub

        # ---- NCRs ----
        print("Seeding NCRs...")
        for ncr_data in NCRS:
            ncr = NonConformanceReport(
                ncr_number=ncr_data["ncr_number"],
                submittal_id=submittal_map[ncr_data["submittal_ref"]].id,
                clause_id=clause_map[ncr_data["clause_ref"]].id,
                raised_by=users["engineer"].id,
                approved_by=users["admin"].id if ncr_data["status"] == NCRStatus.approved else None,
                required_value=ncr_data["required_value"],
                submitted_value=ncr_data["submitted_value"],
                deviation_description=ncr_data["deviation_description"],
                severity=ncr_data["severity"],
                status=ncr_data["status"],
                ai_confidence=ncr_data["ai_confidence"],
            )
            db.add(ncr)

        # ---- RFI Entries ----
        print("Seeding RFI entries...")
        for rfi_data in RFI_ENTRIES:
            rfi = RFIEntry(
                question=rfi_data["question"],
                answer=rfi_data["answer"],
                citations=rfi_data["citations"],
                asked_by=users["engineer"].id,
                retrieved_chunk_ids=rfi_data["retrieved_chunk_ids"],
            )
            db.add(rfi)

        db.commit()
        print("\n✅ Seed data inserted successfully!")
        print("\nTest credentials:")
        print("  PM/Admin  : admin@projectpulse.ai / admin123")
        print("  Engineer  : engineer@projectpulse.ai / engineer123")
        print("  Auditor   : auditor@projectpulse.ai / auditor123")
        print("  Contractor: contractor@eaton.com / contractor123")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
