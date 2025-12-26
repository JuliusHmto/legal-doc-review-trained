"""
Legal Document Review System - Indonesian Law Knowledge Base
Pre-defined prompts and legal context for Indonesian law compliance review.
"""

# ============ Indonesian Law Categories ============

INDONESIAN_LAW_CATEGORIES = {
    "contract": {
        "name": "Contract Law (Hukum Perjanjian)",
        "key_laws": [
            "Kitab Undang-Undang Hukum Perdata (KUHPerdata/Burgerlijk Wetboek)",
            "UU No. 8 Tahun 1999 tentang Perlindungan Konsumen",
        ],
        "key_articles": [
            "Pasal 1313 KUHPerdata - Definisi Perjanjian",
            "Pasal 1320 KUHPerdata - Syarat Sah Perjanjian (sepakat, cakap, hal tertentu, sebab halal)",
            "Pasal 1338 KUHPerdata - Asas Kebebasan Berkontrak",
            "Pasal 1365 KUHPerdata - Perbuatan Melawan Hukum",
        ],
        "common_issues": [
            "Klausul eksonerasi yang berlebihan",
            "Syarat sah perjanjian tidak terpenuhi",
            "Klausul yang bertentangan dengan ketertiban umum",
            "Ketidakseimbangan hak dan kewajiban para pihak",
        ]
    },
    "employment": {
        "name": "Employment Law (Hukum Ketenagakerjaan)",
        "key_laws": [
            "UU No. 13 Tahun 2003 tentang Ketenagakerjaan",
            "UU No. 11 Tahun 2020 tentang Cipta Kerja (Omnibus Law)",
            "PP No. 35 Tahun 2021 tentang PKWT, Alih Daya, Waktu Kerja dan Istirahat",
            "PP No. 36 Tahun 2021 tentang Pengupahan",
        ],
        "key_articles": [
            "Pasal 56-59 UU 13/2003 - PKWT (Perjanjian Kerja Waktu Tertentu)",
            "Pasal 77-85 UU 13/2003 - Waktu Kerja, Istirahat, dan Cuti",
            "Pasal 88-98 UU 13/2003 - Pengupahan",
            "Pasal 150-172 UU 13/2003 - PHK dan Pesangon",
        ],
        "common_issues": [
            "PKWT melebihi batas waktu maksimal",
            "Upah di bawah UMR/UMP",
            "Tidak ada jaminan sosial (BPJS)",
            "Klausul non-compete yang berlebihan",
            "Jam kerja lembur tanpa kompensasi",
        ]
    },
    "corporate": {
        "name": "Corporate Law (Hukum Perusahaan)",
        "key_laws": [
            "UU No. 40 Tahun 2007 tentang Perseroan Terbatas",
            "UU No. 25 Tahun 2007 tentang Penanaman Modal",
            "UU No. 20 Tahun 2008 tentang UMKM",
        ],
        "key_articles": [
            "Pasal 7-14 UU 40/2007 - Pendirian PT",
            "Pasal 92-107 UU 40/2007 - Direksi",
            "Pasal 108-121 UU 40/2007 - Dewan Komisaris",
            "Pasal 127-137 UU 40/2007 - Penggabungan, Peleburan, dan Pengambilalihan",
        ],
        "common_issues": [
            "Kewenangan direksi tidak jelas",
            "Tidak ada mekanisme RUPS",
            "Benturan kepentingan tidak diatur",
            "Kewajiban pelaporan tidak lengkap",
        ]
    },
    "data_protection": {
        "name": "Data Protection (Perlindungan Data Pribadi)",
        "key_laws": [
            "UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi (UU PDP)",
            "UU No. 19 Tahun 2016 tentang ITE (perubahan UU 11/2008)",
            "PP No. 71 Tahun 2019 tentang PSTE",
        ],
        "key_articles": [
            "Pasal 1-5 UU PDP - Definisi dan Jenis Data Pribadi",
            "Pasal 20-33 UU PDP - Hak Subjek Data Pribadi",
            "Pasal 34-45 UU PDP - Kewajiban Pengendali Data",
            "Pasal 67-73 UU PDP - Sanksi Pidana",
        ],
        "common_issues": [
            "Tidak ada persetujuan eksplisit pengumpulan data",
            "Tidak ada mekanisme penghapusan data",
            "Transfer data lintas batas tanpa perlindungan",
            "Tidak ada kebijakan privasi yang jelas",
            "Penyimpanan data melebihi periode yang diperlukan",
        ]
    },
    "ecommerce": {
        "name": "E-Commerce Law (Hukum Perdagangan Elektronik)",
        "key_laws": [
            "PP No. 80 Tahun 2019 tentang Perdagangan Melalui Sistem Elektronik",
            "UU No. 19 Tahun 2016 tentang ITE",
            "UU No. 8 Tahun 1999 tentang Perlindungan Konsumen",
        ],
        "key_articles": [
            "Pasal 4-7 PP 80/2019 - Kewajiban Pelaku Usaha",
            "Pasal 14-17 PP 80/2019 - Syarat dan Ketentuan",
            "Pasal 18-21 PP 80/2019 - Perlindungan Konsumen",
        ],
        "common_issues": [
            "Informasi produk tidak lengkap",
            "Kebijakan pengembalian tidak jelas",
            "Tidak ada mekanisme penyelesaian sengketa",
            "Syarat dan ketentuan tidak transparan",
        ]
    },
    "tax": {
        "name": "Tax Law (Hukum Perpajakan)",
        "key_laws": [
            "UU No. 7 Tahun 2021 tentang HPP (Harmonisasi Peraturan Perpajakan)",
            "UU No. 36 Tahun 2008 tentang PPh",
            "UU No. 42 Tahun 2009 tentang PPN",
        ],
        "key_articles": [
            "Pasal 4 UU PPh - Objek Pajak Penghasilan",
            "Pasal 21-26 UU PPh - Pemotongan Pajak",
            "Pasal 4 UU PPN - Objek PPN",
        ],
        "common_issues": [
            "Kewajiban pemotongan pajak tidak jelas",
            "Tidak ada klausul gross-up",
            "PPN tidak diperhitungkan dalam harga",
        ]
    }
}


# ============ Training Module Generation Prompt ============

TRAINING_MODULE_PROMPT = """
Create a structured training module with the following JSON structure:

{
    "document_type": "Type of document (e.g., Employment Contract, Service Agreement, NDA)",
    "summary": "Brief summary of the document (2-3 sentences)",
    "key_parties": ["List of parties involved"],
    "effective_date": "Effective date if mentioned (null if not found)",
    "clauses": [
        {
            "clause_title": "Title or number of the clause",
            "clause_text": "Full text or summary of the clause",
            "category": "Category (e.g., Employment Terms, Liability, Payment, Termination)",
            "key_points": ["Key points from this clause"],
            "potential_issues": ["Potential legal issues or concerns"],
            "relevant_laws": ["Relevant Indonesian laws (use full law names with articles)"]
        }
    ],
    "overall_assessment": "Overall assessment of the document quality and compliance",
    "applicable_laws": ["List of all Indonesian laws applicable to this document"],
    "risk_areas": ["High-risk areas that need attention"],
    "recommendations": ["General recommendations for improvement"]
}

Focus on Indonesian law compliance. Identify:
1. Any clauses that may violate Indonesian law
2. Missing mandatory provisions under Indonesian law
3. Clauses that are unfair or potentially unenforceable
4. Areas where the document could be strengthened

Be specific about which Indonesian laws and articles are relevant.
"""


# ============ Compliance Review Prompt ============

COMPLIANCE_REVIEW_SYSTEM_PROMPT = """You are an expert Indonesian legal compliance reviewer. 
Your task is to analyze legal documents against current Indonesian law and identify compliance issues.

You have extensive knowledge of:
- Kitab Undang-Undang Hukum Perdata (KUHPerdata)
- UU No. 13 Tahun 2003 tentang Ketenagakerjaan (updated by UU Cipta Kerja)
- UU No. 40 Tahun 2007 tentang Perseroan Terbatas
- UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi
- UU No. 8 Tahun 1999 tentang Perlindungan Konsumen
- PP No. 80 Tahun 2019 tentang Perdagangan Elektronik
- And other relevant Indonesian laws and regulations

For each issue found, provide:
1. Clear description of the issue
2. Specific law/article that is violated or not complied with
3. Severity level (HIGH, MEDIUM, LOW)
4. Recommendation for fixing the issue

Always respond in valid JSON format."""


COMPLIANCE_REVIEW_PROMPT = """
Analyze this document for compliance with Indonesian law.

Document Content:
{document_content}

Training Module Analysis:
{training_module}

Additional Context from Knowledge Base:
{rag_context}

Provide a comprehensive compliance review with the following JSON structure:

{{
    "compliance_score": <0-100 integer>,
    "status": "COMPLIANT" | "NEEDS_REVIEW" | "NON_COMPLIANT",
    "summary": "Brief summary of compliance status",
    "issues": [
        {{
            "severity": "HIGH" | "MEDIUM" | "LOW",
            "category": "Category of issue (e.g., Employment Law, Data Protection)",
            "description": "Clear description of the issue",
            "clause_reference": "Reference to specific clause if applicable",
            "law_reference": "Specific Indonesian law and article violated",
            "recommendation": "How to fix this issue"
        }}
    ],
    "recommendations": ["List of general recommendations"],
    "law_references": [
        {{
            "law": "Full name of the law",
            "relevance": "Why this law is relevant"
        }}
    ],
    "compliant_areas": ["Areas where the document is compliant"],
    "missing_provisions": ["Required provisions that are missing"]
}}

Scoring Guidelines:
- 90-100: Fully compliant, minor suggestions only
- 70-89: Mostly compliant, some issues need attention
- 50-69: Needs significant review, multiple compliance issues
- 30-49: Non-compliant, major issues found
- 0-29: Severely non-compliant, document needs complete revision

Be thorough but fair. Consider Indonesian business practices and legal standards.
"""


def get_law_context(categories: list[str] = None) -> str:
    """Get relevant Indonesian law context based on categories."""
    if not categories:
        categories = list(INDONESIAN_LAW_CATEGORIES.keys())
    
    context_parts = []
    for cat in categories:
        if cat in INDONESIAN_LAW_CATEGORIES:
            law_info = INDONESIAN_LAW_CATEGORIES[cat]
            context_parts.append(f"""
=== {law_info['name']} ===
Key Laws:
{chr(10).join('- ' + law for law in law_info['key_laws'])}

Key Articles:
{chr(10).join('- ' + article for article in law_info['key_articles'])}

Common Issues:
{chr(10).join('- ' + issue for issue in law_info['common_issues'])}
""")
    
    return "\n".join(context_parts)
