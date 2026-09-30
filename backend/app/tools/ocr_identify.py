"""OCR-first product & material code identification module with image preprocessing."""

import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract

from backend.app.config import settings
from backend.app.schemas.scan import MaterialCodeMatch

logger = logging.getLogger("parakh.ocr")

# Common Tesseract paths on Windows
_TESSERACT_COMMON_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]


def _ensure_tesseract_cmd() -> Optional[str]:
    """
    Ensure pytesseract has a valid path to the tesseract executable.
    Checks settings / env vars first, then common Windows installation directories.
    """
    # 1. Check explicit setting or environment variable
    configured = getattr(settings, "TESSERACT_CMD", "") or os.getenv("TESSERACT_CMD", "")
    if configured and os.path.exists(configured):
        pytesseract.pytesseract.tesseract_cmd = configured
        return configured

    # 2. Check common paths
    for _t_path in _TESSERACT_COMMON_PATHS:
        if os.path.exists(_t_path):
            pytesseract.pytesseract.tesseract_cmd = _t_path
            return _t_path

    # 3. Check if tesseract is already available in PATH
    try:
        pytesseract.get_tesseract_version()
        return "tesseract"
    except Exception:
        return None


def check_tesseract_available() -> Tuple[bool, str]:
    """
    Check if Tesseract is installed and functional.
    Returns (is_available, version_or_error_message).
    """
    cmd = _ensure_tesseract_cmd()
    try:
        version = str(pytesseract.get_tesseract_version())
        logger.info(f"Tesseract OCR is available (version: {version}, path: {cmd})")
        return True, version
    except Exception as exc:
        err_msg = f"Tesseract OCR is NOT accessible: {exc}. Please install Tesseract or configure TESSERACT_CMD in .env"
        logger.warning(err_msg)
        return False, err_msg


# Initialize Tesseract path on module load
_ensure_tesseract_cmd()

# ---------------------------------------------------------------------------
# Regex patterns for BIS licenses, HUID, IS Standards, and Marks
# Reused across tools/verify.py and ocr_identify.py
# ---------------------------------------------------------------------------
LICENSE_PATTERN = re.compile(r"(?:CM/L|CW/L|CML|CM\s*/\s*L)[-\s:]*(\d{7,8})\b", re.IGNORECASE)
HUID_PATTERN = re.compile(r"HUID[-\s:]*([A-Z0-9]{6})\b", re.IGNORECASE)
IS_STANDARD_PATTERN = re.compile(r"\bIS\s*[:.-]?\s*(\d{3,5})(?:\s*\(PART\s*\d+\))?(?:\s*:\s*\d{4})?\b", re.IGNORECASE)

# Mapping of known Indian Standards to product taxonomy
KNOWN_STANDARDS: Dict[str, Dict[str, Any]] = {
    "2347": {
        "standard_no": "IS 2347",
        "product_name": "Domestic Pressure Cookers",
        "category": "Kitchen Appliances",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Domestic Pressure Cooker (Quality Control) Order 2020",
    },
    "4151": {
        "standard_no": "IS 4151",
        "product_name": "Helmets (Two-Wheeler Riders)",
        "category": "Safety Equipment",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Two-Wheeler Helmets (Quality Control) Order 2020",
    },
    "16102": {
        "standard_no": "IS 16102 (Part 1)",
        "product_name": "LED Lamps & Bulbs (Self-ballasted)",
        "category": "Lighting & Electronics",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Quality Control Order for LED Lamps 2017",
    },
    "14543": {
        "standard_no": "IS 14543",
        "product_name": "Packaged Drinking Water (Other than Mineral Water)",
        "category": "Food & Beverages",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Mandatory certification under Food Safety & Standards Regulations",
    },
    "13428": {
        "standard_no": "IS 13428",
        "product_name": "Packaged Natural Mineral Water",
        "category": "Food & Beverages",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Mandatory certification under Food Safety & Standards Regulations",
    },
    "3196": {
        "standard_no": "IS 3196 (Part 1)",
        "product_name": "LPG Gas Cylinders (Domestic)",
        "category": "Pressure Vessels",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Gas Cylinders Rules / Mandatory ISI",
    },
    "269": {
        "standard_no": "IS 269",
        "product_name": "Ordinary Portland Cement (43 Grade)",
        "category": "Construction Materials",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Cement (Quality Control) Order 2003",
    },
    "1786": {
        "standard_no": "IS 1786",
        "product_name": "High Strength Deformed Steel Bars (TMT Rebars)",
        "category": "Construction Materials",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Steel and Steel Products (Quality Control) Order",
    },
    "1417": {
        "standard_no": "IS 1417",
        "product_name": "Gold Jewellery and Artefacts",
        "category": "Precious Metals & Jewellery",
        "scheme": "HALLMARK",
        "mandatory": True,
        "notes": "Hallmarking of Gold Jewellery and Gold Artefacts Order 2020",
    },
    "2112": {
        "standard_no": "IS 2112",
        "product_name": "Silver Jewellery and Artefacts",
        "category": "Precious Metals & Jewellery",
        "scheme": "HALLMARK",
        "mandatory": False,
        "notes": "Voluntary hallmarking for silver articles",
    },
    "13252": {
        "standard_no": "IS 13252 (Part 1)",
        "product_name": "Mobile Phone Power Adapters & Chargers",
        "category": "Consumer Electronics",
        "scheme": "CRS",
        "mandatory": True,
        "notes": "Electronics and IT Goods (Requirement for Compulsory Registration) Order",
    },
    "16046": {
        "standard_no": "IS 16046 (Part 2)",
        "product_name": "Rechargeable Lithium-ion Batteries",
        "category": "Energy Storage & Electronics",
        "scheme": "CRS",
        "mandatory": True,
        "notes": "MeitY Compulsory Registration Scheme",
    },
    "1239": {
        "standard_no": "IS 1239 (Part 1)",
        "product_name": "Mild Steel Tubes & Pipes",
        "category": "Construction Materials",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Steel Tubes, Tubulars and Other Wrought Steel Fittings",
    },
    "4985": {
        "standard_no": "IS 4985",
        "product_name": "Unplasticized PVC Pipes for Potable Water Supplies",
        "category": "Plumbing & Piping",
        "scheme": "ISI",
        "mandatory": True,
        "notes": "Pipes for Potable Water Supplies",
    },
}

# In-memory dictionary cache of material codes reference data
_MATERIAL_CODES_CACHE: Optional[List[Dict[str, Any]]] = None


def get_material_codes_reference() -> List[Dict[str, Any]]:
    """Load material codes reference list from seed file."""
    global _MATERIAL_CODES_CACHE
    if _MATERIAL_CODES_CACHE is not None:
        return _MATERIAL_CODES_CACHE

    seed_path = Path(__file__).resolve().parents[3] / "data" / "seed" / "material_codes.json"
    if seed_path.exists():
        try:
            _MATERIAL_CODES_CACHE = json.loads(seed_path.read_text(encoding="utf-8"))
            return _MATERIAL_CODES_CACHE
        except Exception as exc:
            logger.warning(f"Could not load material_codes.json: {exc}")

    # Fallback built-in list
    _MATERIAL_CODES_CACHE = [
        {"category": "plastic_resin_code", "code": "1", "label": "PETE / PET", "material_name": "Polyethylene Terephthalate", "common_uses": "Packaged drinking water bottles, soft drink bottles, food jars", "notes": "Widely recycled; commonly used for clear beverage containers", "applicable_standards": []},
        {"category": "plastic_resin_code", "code": "2", "label": "HDPE", "material_name": "High-Density Polyethylene", "common_uses": "Milk jugs, detergent bottles, chemical drums, pipes", "notes": "Chemical and moisture resistant", "applicable_standards": []},
        {"category": "plastic_resin_code", "code": "3", "label": "PVC", "material_name": "Polyvinyl Chloride", "common_uses": "Plumbing pipes, cable insulation, window frames", "notes": "Rigid and flexible vinyl polymer", "applicable_standards": []},
        {"category": "plastic_resin_code", "code": "4", "label": "LDPE", "material_name": "Low-Density Polyethylene", "common_uses": "Plastic bags, squeeze bottles, shrink wrap", "notes": "Flexible packaging polymer", "applicable_standards": []},
        {"category": "plastic_resin_code", "code": "5", "label": "PP", "material_name": "Polypropylene", "common_uses": "Food containers, yogurt cups, bottle caps, automotive parts", "notes": "High thermal resistance", "applicable_standards": []},
        {"category": "plastic_resin_code", "code": "6", "label": "PS", "material_name": "Polystyrene", "common_uses": "Disposable cutlery, foam cups, CD cases", "notes": "Rigid or expanded polystyrene", "applicable_standards": []},
        {"category": "plastic_resin_code", "code": "7", "label": "OTHER / PC", "material_name": "Polycarbonate / Other Plastics", "common_uses": "Reusable water bottles, food containers, electronics housings", "notes": "Polycarbonate and mixed polymer resins", "applicable_standards": []},
        {"category": "gold_hallmark", "code": "999", "label": "24K", "material_name": "24 Karat Fine Gold (99.9% purity)", "common_uses": "Gold bullion bars, minted coins", "notes": "Highest commercial gold purity", "applicable_standards": []},
        {"category": "gold_hallmark", "code": "916", "label": "22K", "material_name": "22 Karat Gold (91.6% purity)", "common_uses": "Traditional Indian gold jewellery, bangles, chains, rings", "notes": "Mandatory hallmark purity grade", "applicable_standards": []},
        {"category": "gold_hallmark", "code": "875", "label": "21K", "material_name": "21 Karat Gold (87.5% purity)", "common_uses": "Fine jewellery, rings", "notes": "Recognized gold hallmark grade", "applicable_standards": []},
        {"category": "gold_hallmark", "code": "750", "label": "18K", "material_name": "18 Karat Gold (75.0% purity)", "common_uses": "Diamond-studded jewellery, modern rings, watches", "notes": "High hardness gold alloy", "applicable_standards": []},
        {"category": "gold_hallmark", "code": "585", "label": "14K", "material_name": "14 Karat Gold (58.5% purity)", "common_uses": "Lightweight jewellery, daily wear", "notes": "Recognized hallmark grade", "applicable_standards": []},
        {"category": "gold_hallmark", "code": "375", "label": "9K", "material_name": "9 Karat Gold (37.5% purity)", "common_uses": "Fashion jewellery, charms", "notes": "Minimum gold hallmark purity grade", "applicable_standards": []},
        {"category": "silver_hallmark", "code": "925", "label": "Sterling Silver", "material_name": "Sterling Silver (92.5% purity)", "common_uses": "Silver jewellery, utensils, tableware", "notes": "Standard sterling silver alloy", "applicable_standards": []},
        {"category": "silver_hallmark", "code": "900", "label": "Coin Silver", "material_name": "Coin Silver (90.0% purity)", "common_uses": "Silver coins, traditional medallions", "notes": "Coin silver alloy", "applicable_standards": []},
        {"category": "metal_grade", "code": "SS304", "label": "Grade 304 / AISI 304", "material_name": "Austenitic Stainless Steel (18/8)", "common_uses": "Kitchen sinks, cookware, pressure cookers, food equipment", "notes": "Austenitic stainless steel", "needs_research": True, "applicable_standards": []},
        {"category": "metal_grade", "code": "SS316", "label": "Grade 316 / AISI 316", "material_name": "Marine Grade Stainless Steel (18/10/2)", "common_uses": "Marine hardware, chemical containers", "notes": "Molybdenum-bearing stainless steel", "needs_research": True, "applicable_standards": []},
        {"category": "metal_grade", "code": "FE500", "label": "Fe 500 / Fe 500D", "material_name": "High Yield Strength Deformed TMT Steel Bars", "common_uses": "Reinforced concrete construction", "notes": "TMT rebars", "needs_research": True, "applicable_standards": []},
    ]
    return _MATERIAL_CODES_CACHE


def preprocess_image_variants(base_image: Image.Image) -> List[Image.Image]:
    """
    Generate multiple preprocessed image variations to maximize OCR character extraction
    across glare, curved plastic, low contrast, and small engraved text.
    """
    variants: List[Image.Image] = []

    # 1. Base image (ensure standard RGB mode)
    rgb_img = base_image.convert("RGB") if base_image.mode not in ("RGB", "L") else base_image
    variants.append(rgb_img)

    # 2. Grayscale with Autocontrast and High Contrast
    gray = ImageOps.grayscale(rgb_img)
    gray_autocontrast = ImageOps.autocontrast(gray)
    enhancer = ImageEnhance.Contrast(gray_autocontrast)
    high_contrast = enhancer.enhance(2.0)
    variants.append(high_contrast)

    # 3. Upscaled 2x with Sharpening (Essential for small embossed / engraved stamps)
    w, h = gray.size
    upscaled = gray.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    upscaled_sharp = upscaled.filter(ImageFilter.SHARPEN)
    variants.append(upscaled_sharp)

    # 4. Adaptive thresholding / Binarization (Otsu-like via PIL point threshold)
    try:
        # Calculate mean luminance
        histogram = gray.histogram()
        total_pixels = sum(histogram)
        if total_pixels > 0:
            weighted_sum = sum(i * count for i, count in enumerate(histogram))
            mean_thresh = int(weighted_sum / total_pixels)
            binarized = gray.point(lambda p: 255 if p > mean_thresh else 0, mode="1")
            variants.append(binarized.convert("L"))
    except Exception as e:
        logger.debug(f"Thresholding preprocessing skipped: {e}")

    # 5. Inverted Grayscale (for light text engraved on dark or metallic surfaces)
    inverted = ImageOps.invert(gray)
    variants.append(inverted)

    return variants


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using pytesseract OCR with multi-pass preprocessing.
    Combines extracted tokens across image variants to handle glare and curved/embossed text.
    """
    if not image_bytes:
        logger.warning("Empty image bytes provided to OCR")
        return ""

    cmd = _ensure_tesseract_cmd()
    if not cmd:
        logger.warning("Tesseract command not found. OCR extraction skipped.")
        return ""

    try:
        base_image = Image.open(io.BytesIO(image_bytes))
        variants = preprocess_image_variants(base_image)

        extracted_texts: List[str] = []
        seen_lines: set[str] = set()

        for idx, variant in enumerate(variants):
            try:
                # Use standard layout analysis (PSM 11 or default 3)
                txt = pytesseract.image_to_string(variant)
                if txt and txt.strip():
                    for line in txt.splitlines():
                        cleaned_line = line.strip()
                        if cleaned_line and cleaned_line not in seen_lines:
                            seen_lines.add(cleaned_line)
                            extracted_texts.append(cleaned_line)
            except Exception as pass_exc:
                logger.debug(f"OCR pass {idx} encountered error: {pass_exc}")

        combined_text = "\n".join(extracted_texts)
        logger.info(f"pytesseract extracted {len(combined_text)} characters across {len(variants)} passes: {combined_text[:120]!r}")
        return combined_text
    except Exception as exc:
        logger.warning(f"pytesseract OCR extraction failed: {exc}")
        return ""


def match_material_code(extracted_text: str) -> Optional[MaterialCodeMatch]:
    """
    Match OCR-extracted text against Indian Standards (IS), material codes,
    resin codes, hallmark purities, and metal grades using exact and fuzzy pattern matching.

    Also checks for BIS license and HUID marks.

    Returns:
        MaterialCodeMatch with confidence score, or None if no match found.
    """
    if not extracted_text or not extracted_text.strip():
        logger.debug("No text provided for material code matching")
        return None

    raw_text = extracted_text
    # Normalize: uppercase and collapse consecutive spaces
    upper_text = re.sub(r"\s+", " ", raw_text.upper()).strip()
    logger.debug(f"Matching against normalized text: {upper_text!r}")

    # 1. Check for BIS license or HUID in text
    detected_license = None
    license_match = LICENSE_PATTERN.search(upper_text)
    if license_match:
        lic_digits = license_match.group(1)
        detected_license = f"CM/L-{lic_digits}"
        logger.debug(f"Detected license pattern: {detected_license}")

    detected_huid = None
    huid_match = HUID_PATTERN.search(upper_text)
    if huid_match:
        raw_huid = huid_match.group(1).upper()
        detected_huid = f"HUID-{raw_huid[:2]}-{raw_huid[2:]}"
        logger.debug(f"Detected HUID pattern: {detected_huid}")

    # Reference lookup dictionary by (category, code)
    ref_list = get_material_codes_reference()
    ref_by_key = {(r["category"], r["code"]): r for r in ref_list}

    def _build_match(
        category: str,
        code: str,
        confidence: float,
        matched_fragment: str,
        material_name_override: Optional[str] = None,
        common_uses_override: Optional[str] = None,
        notes_override: Optional[str] = None,
    ) -> MaterialCodeMatch:
        ref = ref_by_key.get((category, code), {})
        mat_name = material_name_override or ref.get("material_name", code)
        return MaterialCodeMatch(
            category=category,
            code=code,
            label=ref.get("label", code),
            material_name=mat_name,
            common_uses=common_uses_override or ref.get("common_uses"),
            notes=notes_override or ref.get("notes"),
            confidence=confidence,
            raw_matched_text=matched_fragment,
            detected_license=detected_license,
            detected_huid=detected_huid,
        )

    # -----------------------------------------------------------------------
    # 2. Priority Check: Indian Standard Number (e.g. IS 2347, IS 4151, IS 16102)
    # -----------------------------------------------------------------------
    is_match = IS_STANDARD_PATTERN.search(upper_text)
    if is_match:
        std_num = is_match.group(1)
        if std_num in KNOWN_STANDARDS:
            std_info = KNOWN_STANDARDS[std_num]
            logger.info(f"Direct match found for standard: IS {std_num} ({std_info['product_name']})")
            return MaterialCodeMatch(
                category="indian_standard",
                code=std_info["standard_no"],
                label=std_info["standard_no"],
                material_name=f"{std_info['product_name']} ({std_info['standard_no']})",
                common_uses=f"Product category: {std_info['category']}",
                notes=std_info["notes"],
                confidence=0.95,
                raw_matched_text=is_match.group(0),
                detected_license=detected_license,
                detected_huid=detected_huid,
            )

    # -----------------------------------------------------------------------
    # 3. Plastic Resin Codes (1 to 7)
    # -----------------------------------------------------------------------
    # 7 - Polycarbonate / Other (Check first because "PC" is frequent and specific)
    if re.search(r"\b(?:7\s*PC|7\s*P\s*C|POLYCARBONATE|OTHER\s*7|7\s*OTHER)\b", upper_text):
        return _build_match("plastic_resin_code", "7", 0.95, "7 (PC / Polycarbonate)")
    if re.search(r"\bPC\b", upper_text) and not re.search(r"\b(?:PIECE|PCS|PRICE|PACK)\b", upper_text):
        return _build_match("plastic_resin_code", "7", 0.90, "PC")
    if re.search(r"\bP[\s.]*C\.?\b|\bP\.C\.?", upper_text):
        return _build_match("plastic_resin_code", "7", 0.80, "P C (Polycarbonate)")

    # 1 - PET / PETE
    if re.search(r"\b(?:1\s*PETE?|PETE|PET|1\s*ET|POLYETHYLENE\s*TEREPHTHALATE)\b", upper_text):
        return _build_match("plastic_resin_code", "1", 0.95, "1 (PETE / PET)")
    if re.search(r"\bP[\s.]*E[\s.]*T\.?\b|\bP\.E\.T\.?", upper_text):
        return _build_match("plastic_resin_code", "1", 0.80, "P E T")

    # 2 - HDPE
    if re.search(r"\b(?:2\s*HDPE|HDPE|HIGH\s*DENSITY\s*POLYETHYLENE)\b", upper_text):
        return _build_match("plastic_resin_code", "2", 0.95, "2 (HDPE)")
    if re.search(r"\bH[\s.]*D[\s.]*P[\s.]*E\.?\b|\bH\.D\.P\.E\.?", upper_text):
        return _build_match("plastic_resin_code", "2", 0.80, "H D P E")

    # 3 - PVC
    if re.search(r"\b(?:3\s*PVC|PVC|POLYVINYL\s*CHLORIDE)\b", upper_text):
        return _build_match("plastic_resin_code", "3", 0.95, "3 (PVC)")
    if re.search(r"\bP[\s.]*V[\s.]*C\.?\b|\bP\.V\.C\.?", upper_text):
        return _build_match("plastic_resin_code", "3", 0.80, "P V C")

    # 4 - LDPE
    if re.search(r"\b(?:4\s*LDPE|LDPE|LOW\s*DENSITY\s*POLYETHYLENE)\b", upper_text):
        return _build_match("plastic_resin_code", "4", 0.95, "4 (LDPE)")
    if re.search(r"\bL[\s.]*D[\s.]*P[\s.]*E\.?\b|\bL\.D\.P\.E\.?", upper_text):
        return _build_match("plastic_resin_code", "4", 0.80, "L D P E")

    # 5 - PP
    if re.search(r"\b(?:5\s*PP|POLYPROPYLENE)\b", upper_text):
        return _build_match("plastic_resin_code", "5", 0.95, "5 (PP / Polypropylene)")
    if re.search(r"\bPP\b", upper_text) and not re.search(r"\b(?:PAGES|PER)\b", upper_text):
        return _build_match("plastic_resin_code", "5", 0.90, "PP")
    if re.search(r"\bP[\s.]*P\.?\b|\bP\.P\.?", upper_text):
        return _build_match("plastic_resin_code", "5", 0.80, "P P")

    # 6 - PS
    if re.search(r"\b(?:6\s*PS|POLYSTYRENE)\b", upper_text):
        return _build_match("plastic_resin_code", "6", 0.95, "6 (PS / Polystyrene)")
    if re.search(r"\bPS\b", upper_text):
        return _build_match("plastic_resin_code", "6", 0.85, "PS")
    if re.search(r"\bP[\s.]*S\.?\b|\bP\.S\.?", upper_text):
        return _build_match("plastic_resin_code", "6", 0.75, "P S")

    # Single digit resin code in explicit resin/recycle context
    resin_match = re.search(r"\b(?:RECYCLE|RESIN|PLASTIC|CODE|TYPE|#)\s*([1-7])\b", upper_text)
    if resin_match:
        digit = resin_match.group(1)
        return _build_match("plastic_resin_code", digit, 0.75, f"Resin Code {digit}")

    # -----------------------------------------------------------------------
    # 4. Gold Hallmark Purity Marks
    # -----------------------------------------------------------------------
    if re.search(r"\b(?:999|24\s*K(?:T|ARAT)?|24K999|999\s*24K)\b", upper_text):
        return _build_match("gold_hallmark", "999", 0.95, "999 (24K Gold)")

    if re.search(r"\b(?:916|22\s*K(?:T|ARAT)?|22K916|916\s*22K)\b", upper_text):
        return _build_match("gold_hallmark", "916", 0.95, "916 (22K Gold)")
    if re.search(r"\b9\s*1\s*6\b", upper_text):
        return _build_match("gold_hallmark", "916", 0.80, "9 1 6 (22K Gold)")

    if re.search(r"\b(?:875|21\s*K(?:T|ARAT)?|21K875|875\s*21K)\b", upper_text):
        return _build_match("gold_hallmark", "875", 0.95, "875 (21K Gold)")

    if re.search(r"\b(?:750|18\s*K(?:T|ARAT)?|18K750|750\s*18K)\b", upper_text):
        return _build_match("gold_hallmark", "750", 0.95, "750 (18K Gold)")

    if re.search(r"\b(?:585|14\s*K(?:T|ARAT)?|14K585|585\s*14K)\b", upper_text):
        return _build_match("gold_hallmark", "585", 0.95, "585 (14K Gold)")

    if re.search(r"\b(?:375|9\s*K(?:T|ARAT)?|9K375|375\s*9K)\b", upper_text):
        return _build_match("gold_hallmark", "375", 0.95, "375 (9K Gold)")

    # -----------------------------------------------------------------------
    # 5. Silver Hallmark Purity Marks
    # -----------------------------------------------------------------------
    if re.search(r"\b(?:925|STERLING|925\s*SILVER|SILVER\s*925)\b", upper_text):
        return _build_match("silver_hallmark", "925", 0.95, "925 (Sterling Silver)")
    if re.search(r"\b9\s*2\s*5\b", upper_text):
        return _build_match("silver_hallmark", "925", 0.80, "9 2 5 (Silver)")

    if re.search(r"\b(?:900|COIN\s*SILVER|900\s*SILVER|SILVER\s*900)\b", upper_text):
        return _build_match("silver_hallmark", "900", 0.95, "900 (Coin Silver)")

    # -----------------------------------------------------------------------
    # 6. Metal Grades
    # -----------------------------------------------------------------------
    if re.search(r"\b(?:SS\s*304|AISI\s*304|GRADE\s*304|SUS\s*304|304\s*SS|304\s*STAINLESS)\b", upper_text):
        return _build_match("metal_grade", "SS304", 0.95, "SS 304 (Stainless Steel)")

    if re.search(r"\b(?:SS\s*316|AISI\s*316|GRADE\s*316|SUS\s*316|316\s*SS|316L)\b", upper_text):
        return _build_match("metal_grade", "SS316", 0.95, "SS 316 (Marine Stainless Steel)")

    if re.search(r"\b(?:FE\s*500(?:D)?|TMT\s*500(?:D)?|500D\s*TMT)\b", upper_text):
        return _build_match("metal_grade", "FE500", 0.95, "Fe 500 (TMT Rebar)")

    # -----------------------------------------------------------------------
    # 7. Fallback: If no standard / material code but a valid BIS license was detected
    # -----------------------------------------------------------------------
    if detected_license:
        logger.debug(f"Building match from detected license: {detected_license}")
        return MaterialCodeMatch(
            category="bis_license",
            code=detected_license,
            label="BIS License",
            material_name=f"BIS Certified Product ({detected_license})",
            common_uses="Standard product under BIS Certification Scheme",
            notes="Identified from CM/L license number stamp",
            confidence=0.95,
            raw_matched_text=detected_license,
            detected_license=detected_license,
            detected_huid=detected_huid,
        )

    # -----------------------------------------------------------------------
    # 8. Fallback: If no material code but a valid HUID was detected
    # -----------------------------------------------------------------------
    if detected_huid:
        logger.debug(f"Building match from detected HUID: {detected_huid}")
        return MaterialCodeMatch(
            category="gold_hallmark",
            code="HUID",
            label="Gold HUID",
            material_name="Hallmarked Gold/Silver Jewellery with HUID",
            common_uses="Precious metal jewellery registered with Assaying & Hallmarking Centre",
            notes="Identified from 6-digit Hallmark Unique Identification (HUID)",
            confidence=0.95,
            raw_matched_text=detected_huid,
            detected_license=detected_license,
            detected_huid=detected_huid,
        )

    return None
