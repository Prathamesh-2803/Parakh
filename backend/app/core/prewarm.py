"""
Pre-warmed cache utility for Parakh.

Pre-populates the in-memory cache on startup for deterministic, zero-latency demos:
1. Product lookup: "What is the standard for motorcycle helmets?" / "What compliance do I need for LED bulbs?"
2. Scheme explanation: "Explain the ISI mark certification process."
3. License/HUID verification: "Verify BIS license CM/L-4151201"
4. Hindi query: "दोपहिया वाहन चालकों के लिए हेलमेट का मानक क्या है?"
"""

import logging
from typing import Dict, Any, List
from backend.app.core.cache import set_cached

logger = logging.getLogger("parakh.prewarm")

DEMO_PREWARM_ENTRIES: List[Dict[str, Any]] = [
    # 1. Product Lookup (Motorcycle Helmets)
    {
        "question": "What is the standard for motorcycle helmets?",
        "language": "en",
        "response": {
            "answer": (
                "In India, motorcycle helmets are governed by **IS 4151:2015** "
                "('Protective Helmets for Two-Wheeler Riders'). Under the Two Wheeler Helmets "
                "(Quality Control) Order, 2020, BIS certification under **ISI Mark (Scheme-I)** "
                "is strictly **mandatory**. Helmets must undergo rigorous tests including shock absorption, "
                "penetration resistance, retention system strength, and peripheral vision compliance before sale."
            ),
            "citations": [
                {
                    "source": "IS 4151:2015",
                    "section": "Clause 4 (Safety Requirements)",
                    "url": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails"
                },
                {
                    "source": "Two Wheeler Helmets (Quality Control) Order, 2020",
                    "section": "Order S.O. 4252(E)",
                    "url": "https://www.bis.gov.in/product-certification/qco-orders/"
                }
            ],
            "confidence": 0.98,
            "follow_up_suggestions": [
                "Which testing labs test helmets in India?",
                "How do I apply for an ISI license for helmets?",
                "How do I verify the ISI mark on a helmet?"
            ]
        }
    },
    # 1b. Product Lookup Alternative (LED Bulbs)
    {
        "question": "What compliance do I need for LED bulbs?",
        "language": "en",
        "response": {
            "answer": (
                "For manufacturing or selling self-ballasted LED lamps in India, compliance with **IS 16102 (Part 1):2012** "
                "(Safety Requirements) and **IS 16102 (Part 2):2012** (Performance Requirements) is **mandatory** under the "
                "Electronics and IT Goods (Compulsory Registration Order) under **CRS (Scheme-II)**."
            ),
            "citations": [
                {
                    "source": "IS 16102 (Part 1 & 2):2012",
                    "section": "Scope & Safety Regulations",
                    "url": "https://www.crsbis.in/BIS/"
                },
                {
                    "source": "MeitY Compulsory Registration Order",
                    "section": "Schedule Category: Lighting",
                    "url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/"
                }
            ],
            "confidence": 0.96,
            "follow_up_suggestions": [
                "What documents are required for CRS registration?",
                "Find accredited LED testing labs.",
                "What is the fee structure for CRS?"
            ]
        }
    },
    # 2. Scheme Explanation (ISI Certification Process)
    {
        "question": "Explain the ISI mark certification process.",
        "language": "en",
        "response": {
            "answer": (
                "The **ISI Mark Certification Scheme (Scheme-I)** operates under the BIS (Conformity Assessment) Regulations, 2018. "
                "The process involves: \n"
                "1. **Application Submission**: Online via the Manakonline portal with required documentation and application fee.\n"
                "2. **Factory Audit**: Preliminary physical inspection of manufacturing premises and quality control infrastructure by a BIS inspecting officer.\n"
                "3. **Sample Testing**: Independent testing of product samples in BIS or NABL-accredited labs.\n"
                "4. **Grant of License (CM/L)**: Issuance of license upon compliance with Indian Standards.\n"
                "5. **Surveillance**: Regular factory surveillance and market sampling to ensure ongoing conformity."
            ),
            "citations": [
                {
                    "source": "BIS Conformity Assessment Regulations, 2018",
                    "section": "Scheme I (ISI Mark)",
                    "url": "https://www.bis.gov.in/product-certification/conformity-assessment-schemes/"
                },
                {
                    "source": "Manakonline Portal Guidelines",
                    "section": "e-BIS Scheme-I User Manual",
                    "url": "https://www.manakonline.in/"
                }
            ],
            "confidence": 0.99,
            "follow_up_suggestions": [
                "What is the renewal period for an ISI license?",
                "What is the fee structure for MSMEs?",
                "What is the difference between ISI and CRS?"
            ]
        }
    },
    # 3. Verification (License CM/L-4151201)
    {
        "question": "Verify BIS license CM/L-4151201",
        "language": "en",
        "response": {
            "answer": (
                "**BIS License Verification Result:**\n\n"
                "- **License Number**: CM/L-4151201\n"
                "- **Status**: OPERATIVE (Valid until 2027-12-31)\n"
                "- **Manufacturer**: Steelbird Hi-Tech India Ltd. [DEMO DATA]\n"
                "- **Factory Address**: Plot No. 12, Industrial Area, Haridwar, Uttarakhand\n"
                "- **Product**: Protective Helmets for Two-Wheeler Riders\n"
                "- **Applicable Standard**: IS 4151:2015 (ISI Mark Scheme-I)\n\n"
                "*Note: For live real-time updates and brand-wise variants, verify on the official BIS portal at https://www.services.bis.gov.in/ or the BIS Care App.*"
            ),
            "citations": [
                {
                    "source": "BIS National Registry (CM/L-4151201)",
                    "section": "Conformity Assessment Database",
                    "url": "https://www.services.bis.gov.in/"
                }
            ],
            "confidence": 1.0,
            "follow_up_suggestions": [
                "Verify another license number.",
                "How do I verify a 6-digit gold HUID?",
                "How do I report a suspended or expired license in use?"
            ]
        }
    },
    # 4. Hindi Query (दोपहिया वाहन चालकों के लिए हेलमेट का मानक क्या है?)
    {
        "question": "दोपहिया वाहन चालकों के लिए हेलमेट का मानक क्या है?",
        "language": "hi",
        "response": {
            "answer": (
                "भारत में दोपहिया वाहन चालकों के सुरक्षात्मक हेलमेट के लिए भारतीय मानक **IS 4151:2015** लागू है। "
                "सड़क परिवहन एवं राजमार्ग मंत्रालय और बीआईएस के गुणवत्ता नियंत्रण आदेश (QCO) के तहत भारत में बिना वैध "
                "**ISI मार्क (Scheme-I)** के दोपहिया हेलमेट का निर्माण, आयात या बिक्री कानूनी रूप से प्रतिबंधित है। "
                "हेलमेट पर 7 या 8 अंकों का CM/L लाइसेंस नंबर और ISI मार्क होना अनिवार्य है।"
            ),
            "citations": [
                {
                    "source": "IS 4151:2015",
                    "section": "सुरक्षा आवश्यकताएँ एवं परीक्षण",
                    "url": "https://www.services.bis.gov.in/"
                },
                {
                    "source": "दोपहिया हेलमेट गुणवत्ता नियंत्रण आदेश",
                    "section": "QCO 2020",
                    "url": "https://www.bis.gov.in/product-certification/qco-orders/"
                }
            ],
            "confidence": 0.98,
            "follow_up_suggestions": [
                "हेलमेट परीक्षण प्रयोगशालाएं कहां हैं?",
                "ISI मार्क की प्रामाणिकता की जांच कैसे करें?",
                "हेलमेट निर्माण के लिए लाइसेंस कैसे प्राप्त करें?"
            ]
        }
    }
]


def prewarm_cache() -> int:
    """Pre-warm the cache with standard demo entries."""
    count = 0
    for entry in DEMO_PREWARM_ENTRIES:
        set_cached(entry["question"], entry["language"], entry["response"])
        count += 1
    logger.info(f"Pre-warmed cache with {count} authoritative demo entries.")
    return count
