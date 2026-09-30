"""LLM gateway — one Gemini call per question, Groq fallback, mock mode."""

import asyncio
import json
import logging
import re
import time
from typing import Any
import base64

import httpx

from backend.app.config import settings

logger = logging.getLogger("parakh.llm")


# ---------------------------------------------------------------------------
# Mock provider enhancements — contextual follow-up Q&A for demo mode
# ---------------------------------------------------------------------------

# Knowledge base for common follow-up questions in mock mode
# Knowledge base for common follow-up questions in mock mode
FOLLOW_UP_KNOWLEDGE_BASE = {
    # Helmets (Two-Wheeler)
    "helmet": {
        "IS 4151": {
            "Which testing labs test helmets in India?": {
                "answer": "BIS-recognized laboratories for two-wheeler helmet testing under IS 4151:2015 include:\n• National Test House (NTH), Ghaziabad (NABL: TC-5021)\n• Central Institute of Road Transport (CIRT), Pune (NABL: TC-6184)\n• Northern Regional Testing Centre (Chandigarh)\n• Western Regional Testing Centre (Mumbai)\n• Shriram Institute for Industrial Research (Delhi)\nAll testing centres must possess active ISO/IEC 17025 NABL accreditation for IS 4151 dynamic impact attenuation and retention test protocols.",
                "citations": [{"source": "IS 4151:2015", "section": "Annex A & Lab Guidelines", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the specific impact testing parameters under IS 4151?", "What is the penalty for selling non-ISI helmets under BIS Act?", "What are the 5 steps to get an ISI mark license?"]
            },
            "Which NABL laboratories are accredited for helmet testing?": {
                "answer": "Accredited NABL laboratories for IS 4151 helmet testing include CIRT Pune (TC-6184), National Test House Ghaziabad (TC-5021), ARAI Pune, and Shriram Institute Delhi (TC-5289). Each laboratory is equipped with calibrated 300g drop rigs, spherical/flat anvils, and conditioned environmental test chambers (-10°C to +50°C).",
                "citations": [{"source": "NABL Directory / BIS Portal", "section": "Discipline: Mechanical Testing", "url": "https://www.nabl-india.org/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the specific impact testing parameters under IS 4151?", "What is the penalty for selling non-ISI helmets under BIS Act?", "How to verify ISI mark?"]
            },
            "What are the specific impact testing parameters under IS 4151?": {
                "answer": "Under IS 4151:2015 Clause 7, protective helmets must satisfy four critical mechanical test parameters:\n1. Impact Attenuation: Peak acceleration transmitted to the dummy headform must not exceed 300g when dropped at 7.5 m/s onto flat and hemispherical steel anvils.\n2. Retention System Dynamic Test: Dynamic displacement must not exceed 35 mm and residual displacement < 25 mm under a 10 kg drop mass.\n3. Rigidity Test: Transverse compressive load of 630 N across the shell must not cause deformation exceeding 40 mm.\n4. Audibility Test: Sound attenuation must be less than 10 dB across 500 Hz – 3000 Hz so the rider hears road traffic signals.",
                "citations": [{"source": "IS 4151:2015", "section": "Clause 7.1 - 7.5", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["Which NABL laboratories are accredited for helmet testing?", "What is the penalty for selling non-ISI helmets under BIS Act?", "What are the 5 steps to get an ISI mark license?"]
            },
            "What is the penalty for selling non-ISI helmets under BIS Act?": {
                "answer": "Manufacturing, importing, stocking, or selling non-BIS certified two-wheeler helmets is a cognizable criminal offense under Sections 17 & 29 of the Bureau of Indian Standards Act, 2016:\n• First Offense: Imprisonment for a term up to 2 years, or a monetary fine of minimum ₹2,00,000 (which may extend up to 10 times the value of manufactured or sold goods), or both.\n• Seizure & Confiscation: BIS Enforcement officers and police conduct search-and-seizure raids to seize uncertified inventory and confiscate plant machinery.\n• Commercial Ban: Retailers and e-commerce platforms selling non-compliant helmets face cancellation of trade licenses and platform de-listing.",
                "citations": [{"source": "BIS Act 2016", "section": "Section 29(3) & 29(4)", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What is the standard for motorcycle helmets?", "How can I verify if a helmet has genuine ISI mark?", "What are the 5 steps to get an ISI mark license?"]
            },
            "What is the standard for motorcycle helmets?": {
                "answer": "The mandatory national standard for two-wheeler motorcycle helmets in India is **IS 4151:2015** ('Protective Helmets for Two-Wheeler Riders'). Under the Two-Wheeler Helmets (Quality Control) Order, 2020 and Central Motor Vehicles Rule 138(4)(f), all protective helmets manufactured, imported, or sold in India must carry the standard ISI mark with valid CM/L license.",
                "citations": [{"source": "IS 4151:2015", "section": "Clause 1 (Scope)", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the specific impact testing parameters under IS 4151?", "Which testing labs test helmets in India?", "What is the penalty for selling non-ISI helmets under BIS Act?"]
            },
            "What are the mandatory testing and certification requirements for motorcycle helmets under IS 4151:2015?": {
                "answer": "Mandatory testing under IS 4151:2015 includes impact absorption (< 300g peak acceleration), chin strap retention strength (< 35mm displacement), rigidity (< 40mm deformation under 630N), and audibility (< 10dB loss). Manufacturers must establish an in-house laboratory, submit Form-V on Manakonline, undergo factory inspection, and pass independent third-party NABL testing before grant of CM/L license.",
                "citations": [{"source": "IS 4151:2015", "section": "Clauses 4, 7 & Scheme-I", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["Which NABL laboratories are accredited for helmet testing?", "What is the penalty for selling non-ISI helmets under BIS Act?", "What are the 5 steps to get an ISI mark license?"]
            },
            "What is the validity period of helmet certification?": {
                "answer": "ISI certification for helmets under IS 4151 is initially granted for 1 to 2 years. Renewal requires submission of annual production data, marking fees, surveillance factory audits, and successful verification of random market samples.",
                "citations": [{"source": "BIS Conformity Assessment Regulations 2018", "section": "Regulation 7", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.95,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "What is the penalty for selling non-ISI helmets under BIS Act?"]
            },
            "Are helmets mandatory for all two-wheeler riders?": {
                "answer": "Yes, as per Section 129 of the Motor Vehicles Act (amended 2019) and Central Motor Vehicles Rule 138(4)(f), wearing a BIS-certified helmet conforming to IS 4151 is mandatory for both rider and pillion passenger across all Indian states and Union Territories.",
                "citations": [{"source": "Motor Vehicles Act 1988", "section": "Section 129 & CMVR 138(4)(f)", "url": "https://morth.nic.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What is the penalty for selling non-ISI helmets under BIS Act?", "How can I verify if a helmet has genuine ISI mark?"]
            },
            "What are the key tests performed on helmets?": {
                "answer": "Key tests prescribed in IS 4151:2015 comprise: (1) Impact attenuation drop test onto flat and hemispherical anvils, (2) Dynamic retention and chin-strap slippage test, (3) Transverse shell rigidity test, (4) Audibility sound attenuation test, and (5) Field of peripheral vision test (>105° lateral).",
                "citations": [{"source": "IS 4151:2015", "section": "Clause 7 & Table 1", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the specific impact testing parameters under IS 4151?", "Which NABL laboratories are accredited for helmet testing?"]
            },
            "How can I verify if a helmet has genuine ISI mark?": {
                "answer": "To verify genuine ISI markings on a helmet:\n1. Look for the rectangular ISI logo with standard number 'IS 4151' on top.\n2. Verify the 7-digit CM/L (Certification Marks / License) number printed beneath the logo (format: CM/L-XXXXXXX).\n3. Enter the CM/L number on the official BIS portal (manakonline.in) or BIS Care mobile app to verify manufacturer details, operational status, and validity.",
                "citations": [{"source": "BIS Act 2016", "section": "Marking Regulations", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What is the penalty for selling non-ISI helmets under BIS Act?", "What are the 5 steps to get an ISI mark license?"]
            }
        }
    },

    # Gold Jewelry & Hallmarking
    "gold_jewelry": {
        "IS 1417": {
            "How do I verify a 6-digit Gold HUID number?": {
                "answer": "You can verify any 6-digit alphanumeric Gold HUID (e.g., A1B2C3) via:\n1. BIS Care Mobile App: Download 'BIS Care' from Google Play or Apple App Store, open 'Verify HUID', enter the 6-character code to inspect the registered Jeweller Name, Assaying Centre (AHC), Date of Hallmarking, Article Type (Ring, Bangle, Chain), and certified Purity (22K916, 18K750, 14K585).\n2. Parakh Registry Console: Open the 'Verify Registry' tab on this platform, select 'Gold Hallmarking (HUID)', and enter the code to inspect authentic assay records.",
                "citations": [{"source": "IS 1417:2016 / HUID Guidelines", "section": "Clause 8.1", "url": "https://www.bis.gov.in/hallmarking-overview/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What is the difference between 22K (916) and 18K (750) gold?", "What are the consumer compensation norms if gold purity is defective?", "Where can I get gold jewelry hallmarked in India?"]
            },
            "How does BIS verify 6-character HUID codes on gold jewellery?": {
                "answer": "BIS assigns a centralized cryptographic database where Assaying and Hallmarking Centres (AHCs) upload assay results before laser engraving. When you enter a 6-character HUID, the system retrieves the specific batch test report, assay center code, jeweler's BIS registration, and declared purity without revealing customer identity.",
                "citations": [{"source": "BIS Hallmarking Circular 2023", "section": "Digital Traceability Architecture", "url": "https://www.bis.gov.in/hallmarking-overview/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How do I verify a 6-digit Gold HUID number?", "What are the consumer compensation norms if gold purity is defective?"]
            },
            "What is the difference between 22K (916) and 18K (750) gold?": {
                "answer": "Under IS 1417:2016:\n• 22K Gold (916 Fineness): Contains 91.6% pure gold and 8.4% alloy (copper, silver, zinc). Commonly used for traditional Indian jewellery, wedding bangles, and chains.\n• 18K Gold (750 Fineness): Contains 75.0% pure gold and 25.0% alloy metals. Has higher tensile hardness and durability, making it ideal for stone-studded and diamond jewellery.",
                "citations": [{"source": "IS 1417:2016", "section": "Table 1 (Purity Grades)", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How do I verify a 6-digit Gold HUID number?", "What are the consumer compensation norms if gold purity is defective?"]
            },
            "What are the consumer compensation norms if gold purity is defective?": {
                "answer": "As per BIS Hallmarking Regulations, if a hallmarked jewellery piece is tested at a referral lab and found lower than marked fineness:\n1. The jeweller must refund the difference in gold purity value calculated on the date of purchase.\n2. In addition, the jeweller must pay compensation to the consumer equal to TWO TIMES the cost of purity deficiency plus all testing fees incurred.",
                "citations": [{"source": "BIS Hallmarking Regulations 2018", "section": "Regulation 12 (Compensation)", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How do I verify a 6-digit Gold HUID number?", "Where can I get gold jewelry hallmarked in India?"]
            },
            "Where can I get gold jewelry hallmarked in India?": {
                "answer": "Hallmarking is conducted exclusively at BIS-recognized Assaying and Hallmarking Centres (AHCs). Over 1,000+ AHCs operate across 288+ notified districts in India. Jewelers can find authorized centres using the 'Find AHC' locator on manakonline.in or the BIS Care app.",
                "citations": [{"source": "BIS Hallmarking Directorate", "section": "AHC Recognition Scheme", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How do I verify a 6-digit Gold HUID number?", "What does the 6-digit HUID on gold jewelry mean?"]
            },
            "What does the 6-digit HUID on gold jewelry mean?": {
                "answer": "HUID (Hallmark Unique Identification) is an alphanumeric laser-etched 6-character code uniquely assigned to every single piece of hallmarked jewellery. It provides complete provenance, linking the article to the testing AHC, jeweller registration, purity grade, and weight.",
                "citations": [{"source": "IS 1417:2016", "section": "Clause 8.1", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How do I verify a 6-digit Gold HUID number?", "What is the difference between 22K (916) and 18K (750) gold?"]
            },
            "Is hallmarking mandatory for all gold jewelry in India?": {
                "answer": "Yes. Under the Hallmarking of Gold Jewellery and Gold Artefacts Order, 2020, hallmarking with 6-digit HUID is mandatory across 288+ notified districts in India for all gold jewellery and artefacts exceeding 2 grams in weight.",
                "citations": [{"source": "Ministry of Consumer Affairs Order 2020", "section": "Hallmarking QCO", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How do I verify a 6-digit Gold HUID number?", "What are the consumer compensation norms if gold purity is defective?"]
            },
            "What purity standards are recognized for gold jewelry?": {
                "answer": "Under IS 1417:2016, recognized legal gold purities are: 24K (999), 23K (958), 22K (916), 20K (833), 18K (750), and 14K (585). Each hallmarked article must display the BIS logo, karat purity, and 6-digit HUID.",
                "citations": [{"source": "IS 1417:2016", "section": "Table 1", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What is the difference between 22K (916) and 18K (750) gold?", "How do I verify a 6-digit Gold HUID number?"]
            },
            "Explain the mandatory gold hallmarking rules, recognized purities, and 6-digit HUID verification process under IS 1417.": {
                "answer": "Under IS 1417:2016 and the 2020 Quality Control Order, hallmarking is mandatory in 288+ notified districts for gold articles > 2g. Every article must bear three marks: BIS logo, karat purity (e.g., 22K916), and the 6-digit laser-engraved HUID. Consumers verify the code instantly on the BIS Care app to inspect jeweler registration, assay date, and verified purity.",
                "citations": [{"source": "IS 1417:2016", "section": "Clause 5 & Table 1", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How do I verify a 6-digit Gold HUID number?", "What are the consumer compensation norms if gold purity is defective?"]
            }
        }
    },

    # Domestic Pressure Cookers
    "pressure_cooker": {
        "IS 2347": {
            "Which testing labs are recognized for domestic pressure cookers?": {
                "answer": "BIS-recognized laboratories for testing domestic pressure cookers under IS 2347:2017 include:\n• National Test House (Kolkata & Mumbai)\n• Regional Testing Centres (Chennai, New Delhi)\n• ERDA Testing Laboratory (Vadodara, Gujarat)\n• Shriram Institute for Industrial Research (Delhi)\nLaboratories must hold ISO/IEC 17025 NABL accreditation for hydrostatic proof pressure testing and safety valve burst verification.",
                "citations": [{"source": "IS 2347:2017", "section": "Lab Test Matrix", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the proof pressure requirements for pressure cookers?", "How does the fusible safety plug function under IS 2347?", "What are the 5 steps to get an ISI mark license?"]
            },
            "Which labs test pressure cookers in India?": {
                "answer": "Approved testing facilities include National Test House (Kolkata, Mumbai, Chennai), Central Mechanical Engineering Research Institute (CMERI Durgapur), and NABL-accredited commercial labs specializing in mechanical pressure vessel safety under IS 2347.",
                "citations": [{"source": "IS 2347:2017", "section": "Mechanical Testing Directory", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the proof pressure requirements for pressure cookers?", "What safety features are mandatory in pressure cookers?"]
            },
            "What are the proof pressure requirements for pressure cookers?": {
                "answer": "Under IS 2347:2017 Clause 7.2, every pressure cooker body and lid assembly must withstand a hydrostatic proof pressure of not less than 200 kPa (approx. 2.0 kgf/cm² or 2 bar) for a minimum of 2 minutes without leakage or permanent plastic deformation.",
                "citations": [{"source": "IS 2347:2017", "section": "Clause 7.2 (Hydrostatic Proof Test)", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["How does the fusible safety plug function under IS 2347?", "What safety features are mandatory in pressure cookers?", "What are the 5 steps to get an ISI mark license?"]
            },
            "How does the fusible safety plug function under IS 2347?": {
                "answer": "Under IS 2347:2017 Clause 7.6, the fusible safety plug contains a certified low-melting bismuth alloy. If the primary vent weight fails and the cooker boils dry, the temperature rises and the fusible plug melts between 130°C and 140°C, safely releasing excess pressure before dangerous rupture can occur.",
                "citations": [{"source": "IS 2347:2017", "section": "Clause 7.6 (Thermal Release)", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the proof pressure requirements for pressure cookers?", "Is ISI mark mandatory for all pressure cookers sold in India?"]
            },
            "What safety features are mandatory in pressure cookers?": {
                "answer": "Mandatory safety devices per IS 2347 include: (1) Primary weight valve pressure regulator, (2) Spring-loaded or fusible secondary safety release plug, (3) Gasket release system (GRS) to vent steam if vent tube clogs, and (4) Interlocking mechanism preventing opening under pressure.",
                "citations": [{"source": "IS 2347:2017", "section": "Clause 4 & Table 2", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the proof pressure requirements for pressure cookers?", "How often should pressure cooker safety valves be replaced?"]
            },
            "Is ISI mark mandatory for all pressure cookers sold in India?": {
                "answer": "Yes. Under the Domestic Pressure Cooker (Quality Control) Order, 2020, domestic pressure cookers cannot be manufactured, imported, or sold in India without standard ISI certification under IS 2347.",
                "citations": [{"source": "Domestic Pressure Cooker QCO 2020", "section": "Gazette Order", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "Which testing labs are recognized for domestic pressure cookers?"]
            },
            "How often should pressure cooker safety valves be replaced?": {
                "answer": "Safety valves and rubber gaskets should be inspected annually and replaced every 2 to 3 years, or immediately if any signs of hardening, pitting, or corrosion appear, using genuine ISI-marked replacement components.",
                "citations": [{"source": "IS 2347:2017", "section": "User Maintenance Instructions", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.95,
                "follow_up_suggestions": ["What are the proof pressure requirements for pressure cookers?", "What safety features are mandatory in pressure cookers?"]
            },
            "What are the mandatory safety features and QCO requirements for pressure cookers under IS 2347?": {
                "answer": "Under IS 2347:2017 and the Domestic Pressure Cookers QCO 2020, ISI certification is mandatory. Mandatory safety features include a primary weight valve, secondary fusible safety release plug (operating at 130-140°C), gasket release system, and 200 kPa hydrostatic proof pressure tolerance.",
                "citations": [{"source": "IS 2347:2017", "section": "Clause 4 & 7", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["Which testing labs are recognized for domestic pressure cookers?", "What are the 5 steps to get an ISI mark license?"]
            }
        }
    },

    # Packaged Drinking Water
    "packaged_water": {
        "IS 14543": {
            "What are the food-contact plastic limits under IS 9845?": {
                "answer": "Plastic bottles and caps for packaged drinking water must strictly comply with **IS 9845:1998** ('Overall Migration Limits for Plastics in Contact with Foodstuffs'):\n• Overall Migration Limit: Must not exceed 60 mg/kg or 10 mg/dm² into food simulants (distilled water, 3% acetic acid, 10% alcohol).\n• Heavy Metals: Heavy metal migration (lead, cadmium, mercury, chromium) must be undetectable.\n• Resin Identification: Containers must be molded from virgin PET resin and bear the triangular PET 1 recycling emblem as per IS 14534.",
                "citations": [{"source": "IS 9845:1998 / IS 14543", "section": "Clause 4.1 & Table 1", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What is the difference between IS 13428 (Mineral Water) and IS 14543?", "How to verify the CM/L license on a packaged water bottle?", "What are the 5 steps to get an ISI mark license?"]
            },
            "What is the difference between IS 13428 (Mineral Water) and IS 14543?": {
                "answer": "• **IS 14543**: Packaged Drinking Water (Other than Natural Mineral Water). Sourced from municipal or borewell sources and subjected to physical treatments (reverse osmosis, filtration, ozonation, remineralization).\n• **IS 13428**: Packaged Natural Mineral Water. Obtained directly from natural, protected subterranean sources (springs/artesian wells) with naturally occurring minerals, bottled at source with minimal filtration and no chemical alteration.",
                "citations": [{"source": "IS 14543 vs IS 13428", "section": "Product Definitions", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the food-contact plastic limits under IS 9845?", "How to verify the CM/L license on a packaged water bottle?"]
            },
            "How to verify the CM/L license on a packaged water bottle?": {
                "answer": "Look for the BIS ISI mark with 'IS 14543' above the pyramid logo and the 7-digit CM/L license number beneath it (e.g., CM/L-7123456). Enter this license number on the BIS Care App or Manakonline to verify manufacturer registration, plant address, and license validity.",
                "citations": [{"source": "BIS Act 2016", "section": "Marking Requirements", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the food-contact plastic limits under IS 9845?", "What are the 5 steps to get an ISI mark license?"]
            },
            "Which labs test packaged drinking water in India?": {
                "answer": "BIS-recognized water testing facilities include: Central Food Technological Research Institute (CFTRI Mysore), National Test House (Kolkata, Mumbai, Chennai), and NABL-accredited environmental and food laboratories specializing in pesticide residue analysis and microbial cultures.",
                "citations": [{"source": "IS 14543:2016", "section": "Testing Laboratory Directory", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the food-contact plastic limits under IS 9845?", "How to verify the CM/L license on a packaged water bottle?"]
            },
            "Is ISI mark mandatory for all packaged drinking water?": {
                "answer": "Yes. Under FSSAI Regulations and the Mandatory Certification of Packaged Drinking Water Order, no commercial bottled water can be manufactured or distributed without valid BIS ISI certification under IS 14543.",
                "citations": [{"source": "FSSAI / BIS Gazette Order", "section": "Mandatory Certification", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "What are the food-contact plastic limits under IS 9845?"]
            },
            "What are the mandatory testing parameters and microbiological requirements for packaged drinking water under IS 14543?": {
                "answer": "Under IS 14543:2016, packaged drinking water must pass zero-tolerance microbiological tests (E. coli, Coliform bacteria, Faecal Streptococci, Pseudomonas aeruginosa absent per 250ml), chemical parameter limits (TDS 75-500 mg/L, Lead < 0.01 mg/L, Arsenic < 0.01 mg/L), and pesticide residue limits (individual < 0.0001 mg/L).",
                "citations": [{"source": "IS 14543:2016", "section": "Table 1, 2 & 3", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the food-contact plastic limits under IS 9845?", "What is the difference between IS 13428 (Mineral Water) and IS 14543?"]
            }
        }
    },

    # LED Lamps & Lighting
    "led_lamp": {
        "IS 16102": {
            "What testing labs certify LED lamps in India?": {
                "answer": "BIS-recognized testing laboratories for LED lighting under IS 16102 include Electronics Regional Test Laboratories (ERTL East, North, West, South), Central Power Research Institute (CPRI Bengaluru), and National Test House.",
                "citations": [{"source": "IS 16102:2012", "section": "Testing Facility Directory", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["Are LED lamps mandatory for all applications?", "What is the certification procedure and CRS registration requirement for LED lamps under IS 16102?"]
            },
            "What is the certification procedure and CRS registration requirement for LED lamps under IS 16102?": {
                "answer": "Self-ballasted LED lamps for general lighting are covered under Compulsory Registration Scheme (CRS, Scheme-II) governed by MeitY and BIS under IS 16102 (Part 1 & 2). Manufacturers submit product samples to a BIS-recognized lab, obtain test reports, and register online through the BIS CRS portal to secure an R-number.",
                "citations": [{"source": "CRS Order / IS 16102", "section": "Scheme II Regulations", "url": "https://www.crsbis.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What testing labs certify LED lamps in India?", "What is the energy efficiency requirement for LED lamps?"]
            },
            "Are LED lamps mandatory for all applications?": {
                "answer": "Yes, under the Quality Control Order for LED Lamps (2017) and CRO Order, domestic and commercial self-ballasted LED lamps are under mandatory CRS registration with BIS.",
                "citations": [{"source": "QCO for LED Lamps 2017", "section": "Mandatory Notification", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What testing labs certify LED lamps in India?", "What is the energy efficiency requirement for LED lamps?"]
            },
            "What is the energy efficiency requirement for LED lamps?": {
                "answer": "LED lamps must achieve a minimum luminous efficacy of 80 to 100 lumens/watt as per IS 16102 (Part 2) and BEE Star Labeling norms, with harmonic distortion (THD) controlled within specified electrical limits.",
                "citations": [{"source": "IS 16102 (Part 2)", "section": "Performance Requirements", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.95,
                "follow_up_suggestions": ["What testing labs certify LED lamps in India?", "Can LED lamps be used in enclosed fixtures?"]
            }
        }
    },

    # TMT Steel Bars
    "tmt_steel": {
        "IS 1786": {
            "What are the mechanical property requirements and QCO order status for TMT steel bars under IS 1786?": {
                "answer": "High-strength deformed steel bars (TMT) are governed by **IS 1786:2008** under mandatory Steel Quality Control Order. Grades include Fe 415, Fe 500, Fe 550, and Fe 600 (with 'D' variants for enhanced earthquake ductility). Mandatory parameters: 0.2% proof stress, minimum elongation (14.5% to 18%), bend and rebend test, and strict sulfur/phosphorus chemical limits (< 0.040% each).",
                "citations": [{"source": "IS 1786:2008", "section": "Table 3 & Mechanical Specifications", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "How to verify ISI mark?"]
            }
        }
    },

    # Licensing, Roadmap & General BIS
    "licensing": {
        "Manakonline": {
            "What are the 5 steps to get an ISI mark license?": {
                "answer": "Securing a BIS ISI Mark license (Scheme-I) on Manakonline involves 5 sequential stages:\n1. Online Application: Register on manakonline.in, fill Form-V, upload factory layout, machinery list, and pay ₹1,000 application fee.\n2. In-House Test Laboratory: Set up dedicated in-house test equipment conforming to the Scheme of Inspection and Testing (SIT).\n3. Factory Inspection Audit: A BIS Technical Officer audits the plant, examines production controls, and witnesses live batch testing.\n4. Independent Lab Testing: Samples drawn during the inspection are sealed and dispatched to an independent NABL laboratory for testing.\n5. Grant of License (CM/L): Upon receipt of conforming test reports, BIS issues the operative CM/L number authorizing the manufacturer to affix the ISI mark.",
                "citations": [{"source": "BIS Conformity Assessment Regulations 2018", "section": "Scheme I (Grant of License)", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["Explain the ISI mark certification process and fee structure.", "How long does the Manakonline application process take?", "How can I search recognized NABL testing laboratories?"]
            },
            "Explain the ISI mark certification process and fee structure.": {
                "answer": "The ISI certification fee structure consists of:\n• Application Fee: ₹1,000 (one-time non-refundable)\n• Factory Audit Inspection Charge: ₹7,000 per person-day for officer visit\n• Third-Party Sample Testing Fees: As charged by the NABL laboratory (typically ₹10,000 - ₹50,000 depending on standard)\n• Annual Marking Fee: Variable rate (e.g. ₹50,000 to ₹1,50,000 based on minimum production volume)\nMicro and Small enterprises (MSMEs) and women entrepreneurs receive up to 50% concession on application and marking fees.",
                "citations": [{"source": "BIS Schedule of Fees", "section": "Regulation 6 & Fee Guidelines", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "How long does the Manakonline application process take?"]
            },
            "How long does the Manakonline application process take?": {
                "answer": "Under the simplified normal procedure, processing takes 60 to 90 days from application submission to grant of license. Under the 'Tatkal' / Option-2 simplified scheme (where initial passing test reports are pre-submitted from a recognized lab), licenses can be granted within 30 days after factory inspection.",
                "citations": [{"source": "e-BIS Citizen Charter", "section": "Timeline Guidelines", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "Explain the ISI mark certification process and fee structure?"]
            },
            "How do I apply for ISI license?": {
                "answer": "Apply online at the official BIS portal (manakonline.in) under 'Product Certification (e-BIS)'. Create an applicant profile, select the Indian Standard (e.g., IS 4151, IS 2347), upload factory documents, and submit testing facilities details as per Scheme of Inspection and Testing.",
                "citations": [{"source": "Manakonline User Guide", "section": "Step-by-step SOP", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "Explain the ISI mark certification process and fee structure."]
            },
            "How do I apply for ISI?": {
                "answer": "To apply for an ISI mark license, register on manakonline.in, submit manufacturing facility blueprints, set up in-house testing instruments, pass independent NABL lab test verification, and complete the BIS officer factory audit.",
                "citations": [{"source": "BIS Scheme I", "section": "Application Process", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "Explain the ISI mark certification process and fee structure."]
            },
            "How to verify ISI mark?": {
                "answer": "Verify an ISI mark by checking three elements: (1) The standard ISI logo, (2) The IS standard number on top (e.g., IS 4151), and (3) The 7-digit CM/L number below. Verify the CM/L number in the BIS Care App or on manakonline.in to confirm authenticity and active license status.",
                "citations": [{"source": "BIS Act 2016", "section": "Standard Mark Verification", "url": "https://www.manakonline.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What is the penalty for selling non-ISI helmets under BIS Act?", "What are the 5 steps to get an ISI mark license?"]
            },
            "How can I search recognized NABL testing laboratories?": {
                "answer": "Search authorized testing facilities using the 'BIS Recognized Labs' directory on bis.gov.in or the NABL accredited laboratory portal (nabl-india.org). Search by standard number (e.g. IS 4151, IS 2347) or discipline to find laboratories certified for testing and calibration.",
                "citations": [{"source": "BIS Laboratory Network", "section": "Lab Recognition Scheme", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.98,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "Explain the ISI mark certification process and fee structure."]
            },
            "What other standards exist?": {
                "answer": "BIS has published over 21,000 Indian Standards covering 14 broad technical sectors, including Mechanical, Civil, Chemical, Electronics & IT, Food & Agriculture, Textiles, and Metallurgy. Key mandatory consumer standards include IS 4151 (Helmets), IS 2347 (Pressure Cookers), IS 1417 (Gold Hallmarking), IS 14543 (Packaged Water), and IS 1786 (TMT Steel).",
                "citations": [{"source": "BIS Standards Catalogue", "section": "Overview", "url": "https://www.services.bis.gov.in/"}],
                "confidence": 0.95,
                "follow_up_suggestions": ["What is the standard for motorcycle helmets?", "What are the 5 steps to get an ISI mark license?"]
            }
        }
    }
}


def _format_kb_response(item_data: Any, standard_code: str) -> dict[str, Any]:
    """Format KB item into standardized dict response with citations and suggestions."""
    if isinstance(item_data, dict):
        return {
            "answer": item_data.get("answer", ""),
            "citations": item_data.get("citations", [{"source": standard_code, "section": "Technical Specification", "url": "https://www.bis.gov.in/"}]),
            "confidence": item_data.get("confidence", 0.98),
            "follow_up_suggestions": item_data.get("follow_up_suggestions", ["What other standards exist?", "How do I apply for ISI?"])
        }
    return {
        "answer": str(item_data),
        "citations": [{"source": standard_code, "section": "Technical Specification", "url": "https://www.bis.gov.in/"}],
        "confidence": 0.95,
        "follow_up_suggestions": ["What other standards exist?", "How do I apply for ISI?"]
    }


def _questions_match(prompt: str, question: str) -> bool:
    """Check if prompt matches question exactly (after normalization)."""
    prompt_clean = re.sub(r'[^\w\s]', '', prompt).lower().strip()
    question_clean = re.sub(r'[^\w\s]', '', question).lower().strip()
    return prompt_clean == question_clean


def _partial_question_match(prompt: str, question: str) -> bool:
    """Check if prompt contains key terms from question or vice versa."""
    prompt_words = set(re.findall(r'\b\w+\b', prompt.lower()))
    question_words = set(re.findall(r'\b\w+\b', question.lower()))

    stop_words = {"what", "is", "the", "are", "can", "how", "do", "which", "where", "when", "why", "a", "an", "of", "in", "on", "at", "to", "for", "under", "and"}
    prompt_words -= stop_words
    question_words -= stop_words

    if not question_words or not prompt_words:
        return False
    
    overlap = len(prompt_words & question_words)
    return (overlap / len(question_words) >= 0.5) or (overlap / len(prompt_words) >= 0.5) or (overlap >= 3)


def _find_contextual_follow_up(prompt: str, context: str) -> dict[str, Any] | None:
    """
    Find a contextual follow-up answer based on prompt across all standards in knowledge base.
    Returns structured dict if match found, None otherwise.
    """
    clean_q = prompt
    if "USER QUESTION:" in prompt:
        parts = prompt.split("USER QUESTION:")[1]
        clean_q = parts.split("LANGUAGE INSTRUCTION:")[0].split("OUTPUT")[0].strip()

    clean_q_lower = clean_q.lower().strip()

    # Pass 1: Exact question match across ALL categories
    for topic, standards in FOLLOW_UP_KNOWLEDGE_BASE.items():
        for standard_code, q_dict in standards.items():
            for question, item_data in q_dict.items():
                if _questions_match(clean_q_lower, question.lower()):
                    return _format_kb_response(item_data, standard_code)

    # Pass 2: Keyword overlap / partial question match across ALL categories
    for topic, standards in FOLLOW_UP_KNOWLEDGE_BASE.items():
        for standard_code, q_dict in standards.items():
            for question, item_data in q_dict.items():
                if _partial_question_match(clean_q_lower, question.lower()):
                    return _format_kb_response(item_data, standard_code)

    return None


# ---------------------------------------------------------------------------
# Mock provider (MOCK_LLM=true) — zero cost, always works
# ---------------------------------------------------------------------------

async def _mock_generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Return structured JSON mock response — used for testing and dev."""
    logger.info("mock_generate called (MOCK_LLM=true)")

    # 1. First check if this question matches our authoritative follow-up knowledge base
    follow_up_data = _find_contextual_follow_up(prompt, context)
    if follow_up_data:
        # Check if language translation was requested
        if "Respond in fluent, natural Hindi" in prompt or "Respond in Hindi" in prompt:
            follow_up_data["answer"] = f"(हिंदी अनुवाद) {follow_up_data['answer']}"
            follow_up_data["follow_up_suggestions"] = ["आवेदन प्रक्रिया क्या है?", "शुल्क कितनी है?", "मानक विवरण क्या है?"]
        elif "Respond in fluent, natural Marathi" in prompt or "Respond in Marathi" in prompt:
            follow_up_data["answer"] = f"(मराठी अनुवाद) {follow_up_data['answer']}"
            follow_up_data["follow_up_suggestions"] = ["अर्ज कसा करावा?", "शुल्क किती आहे?"]
        elif "Respond in fluent, natural Tamil" in prompt or "Respond in Tamil" in prompt:
            follow_up_data["answer"] = f"(தமிழ் விளக்கம்) {follow_up_data['answer']}"
            follow_up_data["follow_up_suggestions"] = ["விண்ணப்பிப்பது எப்படி?", "கட்டணம் எவ்வளவு?"]

        mock_json = json.dumps(follow_up_data, ensure_ascii=False)
        return {
            "text": mock_json,
            "provider": "mock",
            "model": "mock",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }

    # 2. Handle language-specific generic mock responses
    if "Respond in fluent, natural Hindi" in prompt or "Respond in Hindi" in prompt:
        mock_json = json.dumps({
            "answer": "यह एक मॉक उत्तर है (MOCK_LLM=true)। भारत में लागू मुख्य मानक IS 4151 (हेलमेट) और IS 2347 (प्रेशर कुकर) हैं।",
            "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
            "confidence": 0.9,
            "follow_up_suggestions": ["आवेदन प्रक्रिया क्या है?", "शुल्क कितनी है?"]
        }, ensure_ascii=False)
    elif "Respond in fluent, natural Marathi" in prompt or "Respond in Marathi" in prompt:
        mock_json = json.dumps({
            "answer": "हे एक मॉक उत्तर आहे (MOCK_LLM=true). लागू मानक IS 4151 आणि IS 2347 आहे.",
            "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
            "confidence": 0.9,
            "follow_up_suggestions": ["अर्ज कसा करावा?", "शुल्क किती आहे?"]
        }, ensure_ascii=False)
    elif "Respond in fluent, natural Tamil" in prompt or "Respond in Tamil" in prompt:
        mock_json = json.dumps({
            "answer": "இது ஒரு மாதிரி பதில் (MOCK_LLM=true). பொருந்தக்கூடிய தரநிலைகள் IS 4151 மற்றும் IS 2347.",
            "citations": [{"source": "IS 4151", "section": "Clause 1", "url": "https://www.bis.gov.in/"}],
            "confidence": 0.9,
            "follow_up_suggestions": ["விண்ணப்பிப்பது எப்படி?", "கட்டணம் எவ்வளவு?"]
        }, ensure_ascii=False)
    else:
        # 3. Generate response from context for first-time queries
        context_answer = _generate_contextual_answer(prompt, context)
        if context_answer:
            mock_json = json.dumps({
                "answer": context_answer,
                "citations": [{"source": "SQL Database", "section": "Product Category", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.90,
                "follow_up_suggestions": ["Which testing labs test helmets in India?", "How do I apply for ISI license?", "How to verify ISI mark?"]
            }, ensure_ascii=False)
        else:
            # Safe grounded fallback
            mock_json = json.dumps({
                "answer": "Based on retrieved official BIS records, Indian Standards (IS) establish mandatory testing and quality benchmarks under Scheme-I (ISI Mark) and Scheme-IV (Hallmarking). For complete regulatory specifications, please consult https://www.bis.gov.in/.",
                "citations": [{"source": "BIS Act 2016", "section": "Section 14 & 15", "url": "https://www.bis.gov.in/"}],
                "confidence": 0.90,
                "follow_up_suggestions": ["What are the 5 steps to get an ISI mark license?", "What is the standard for motorcycle helmets?"]
            }, ensure_ascii=False)

    return {
        "text": mock_json,
        "provider": "mock",
        "model": "mock",
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }


def _generate_contextual_answer(prompt: str, context: str) -> str | None:
    """
    Generate a grounded answer from the provided context for first-time questions.
    Extracts key information from SQL tool results in the context (last occurrence).
    """
    if not context or not context.strip():
        return None
    
    # Extract product info from context (SQL tool results - take LAST occurrence)
    import re
    
    # Find all occurrences and take the last one (SQL tool results are appended at the end)
    product_matches = list(re.finditer(r'Product:\s*([^\n]+)', context))
    standard_matches = list(re.finditer(r'Standard:\s*([^\n]+)', context))
    scheme_matches = list(re.finditer(r'Scheme:\s*([^\n]+)', context))
    mandatory_matches = list(re.finditer(r'Mandatory:\s*([^\n]+)', context))
    qco_matches = list(re.finditer(r'QCO Order:\s*([^\n]+)', context))
    
    if not product_matches:
        return None

    # Take the last match (SQL tool result is appended last)
    product = product_matches[-1].group(1).strip()
    standard = standard_matches[-1].group(1).strip() if standard_matches else "Not specified"
    scheme = scheme_matches[-1].group(1).strip() if scheme_matches else "Not specified"
    mandatory = mandatory_matches[-1].group(1).strip() if mandatory_matches else "Unknown"
    qco = qco_matches[-1].group(1).strip() if qco_matches else "Not specified"
    
    # Build answer based on product type
    if "helmet" in product.lower():
        return (
            f"In India, {product} are governed by **{standard}** "
            f"('Protective Helmets for Two-Wheeler Riders'). "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Helmets must undergo rigorous tests "
            f"including shock absorption, penetration resistance, "
            f"retention system strength, and peripheral vision compliance before sale."
        )
    elif "led" in product.lower() or "lamp" in product.lower() or "bulb" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Products must meet safety and photometric "
            f"performance requirements as per the standard."
        )
    elif "pressure cooker" in product.lower() or "cooker" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Cookers must pass hydraulic pressure test, "
            f"blow-off valve testing, and thermal shock resistance."
        )
    elif "gold" in product.lower() or "jewellery" in product.lower() or "jewelry" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, hallmarking under **{scheme}** "
            f"is **mandatory**. Each article must bear a 6-digit HUID "
            f"for traceability and purity verification."
        )
    elif "water" in product.lower():
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **mandatory**. Water must meet microbiological, chemical, "
            f"and physical quality parameters."
        )
    else:
        # Generic template
        mandatory_text = "mandatory" if "true" in mandatory.lower() else "voluntary"
        return (
            f"{product} in India are governed by **{standard}**. "
            f"Under the {qco}, BIS certification under **{scheme}** "
            f"is **{mandatory_text}**."
        )


# ---------------------------------------------------------------------------
# Gemini provider (primary)
# ---------------------------------------------------------------------------

async def _gemini_generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Call Google Gemini via the REST API (keeps dependencies light)."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = settings.GEMINI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )

    # Build the request body — single user turn with optional context
    parts: list[dict] = []
    if context:
        parts.append({"text": f"Context:\n{context}\n\n"})
    parts.append({"text": prompt})

    body = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=body)
        if resp.status_code != 200:
            logger.error("Gemini API error %d: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()

    # Extract generated text
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected Gemini response structure: %s", data)
        raise RuntimeError("Failed to parse Gemini response") from exc

    usage = data.get("usageMetadata", {})
    return {
        "text": text,
        "provider": "gemini",
        "model": model,
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
        },
    }


async def _gemini_vision_generate(prompt: str, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """Call Google Gemini Vision via the REST API with inline image data."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = settings.GEMINI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )

    # Encode image bytes to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Build the request body with inline image data
    parts: list[dict] = []
    parts.append({
        "inline_data": {
            "mime_type": mime_type,
            "data": image_base64
        }
    })
    parts.append({"text": prompt})

    body = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=body)
        if resp.status_code != 200:
            logger.error("Gemini Vision API error %d: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()

    # Extract generated text
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected Gemini Vision response structure: %s", data)
        raise RuntimeError("Failed to parse Gemini Vision response") from exc

    usage = data.get("usageMetadata", {})
    return {
        "text": text,
        "provider": "gemini",
        "model": model,
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
        },
    }


# ---------------------------------------------------------------------------
# Groq provider (fallback)
# ---------------------------------------------------------------------------

async def _groq_generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Call Groq chat completions API as fallback."""
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    model = settings.GROQ_MODEL
    url = "https://api.groq.com/openai/v1/chat/completions"

    messages: list[dict] = []
    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    body = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": 1024}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url, json=body, headers={"Authorization": f"Bearer {api_key}"}
        )
        if resp.status_code != 200:
            logger.error("Groq API error %d: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {
        "text": text,
        "provider": "groq",
        "model": model,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        },
    }


# ---------------------------------------------------------------------------
# Public entry point with retry + fallback
# ---------------------------------------------------------------------------

async def generate(prompt: str, context: str = "") -> dict[str, Any]:
    """Generate an LLM response.  Order: mock → Gemini (with retry) → Groq."""

    # --- Mock mode (no cost) ---
    if settings.MOCK_LLM:
        return await _mock_generate(prompt, context)

    # --- Gemini with exponential backoff ---
    last_exc: Exception | None = None
    for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
        try:
            return await _gemini_generate(prompt, context)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            delay = settings.LLM_RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                "Gemini attempt %d/%d failed (%s) — retrying in %.1fs",
                attempt,
                settings.LLM_MAX_RETRIES,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    logger.error("Gemini exhausted retries; falling back to Groq")

    # --- Groq fallback ---
    try:
        return await _groq_generate(prompt, context)
    except Exception as exc:  # noqa: BLE001
        logger.error("Groq fallback also failed: %s", exc)
        raise RuntimeError(
            "All LLM providers failed. Please try again later."
        ) from last_exc


async def generate_vision(prompt: str, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """Generate an LLM response from image. Order: mock → Gemini (with retry)."""
    # --- Mock mode (no cost) ---
    if settings.MOCK_LLM:
        return await _mock_vision_generate(prompt, image_bytes, mime_type)

    # --- Gemini Vision with exponential backoff ---
    last_exc: Exception | None = None
    for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
        try:
            return await _gemini_vision_generate(prompt, image_bytes, mime_type)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            delay = settings.LLM_RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                "Gemini Vision attempt %d/%d failed (%s) — retrying in %.1fs",
                attempt,
                settings.LLM_MAX_RETRIES,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    logger.error("Gemini Vision exhausted retries")
    raise RuntimeError(
        "Gemini Vision failed after retries. Please try again later."
    ) from last_exc
