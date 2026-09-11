import re
from typing import List, Dict

# ======================================================
# PRICE LINE PARSER
# ======================================================
PRICE_LINE_REGEX = re.compile(
    r"^(?P<code>[A-Z0-9]{3,4})\s+(?P<text>.+?)\s+(?P<price>\d+(?:[.,]\d+)?)$"
)


def _normalize_codes(codes: List[str]) -> List[str]:
    normalized = []
    seen = set()

    for code in codes or []:
        if not isinstance(code, str):
            continue

        value = code.strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{3,4}", value):
            continue

        if value in seen:
            continue

        seen.add(value)
        normalized.append(value)

    return normalized


def parse_priced_lines(lines: List[str]) -> Dict[str, float]:
    """
    Extrahiert Preise aus z.B.:
    '3AB Sitzheizung 100'
    '3AD M-Lenkrad 3000'

    Wenn keine Preise angegeben sind, ignoriere die Zeile.
    """
    prices: Dict[str, float] = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = PRICE_LINE_REGEX.match(line)
        if not match:
            continue

        code = match.group("code").upper()
        price = float(match.group("price").replace(",", "."))
        prices[code] = price

    return prices


# ======================================================
# NORMALIZER (FINAL & STABLE)
# ======================================================
def normalize_vehicle_input(
    *,
    model: str,
    color: str,
    interior: str,
    all_codes: List[str],
    priced_lines: List[str],
    options_meta: Dict
) -> Dict:
    """
    Baut die finale strukturierte Fahrzeugdarstellung.

    Regeln:
    - all_codes ist die Master-Liste der Fahrzeugcodes
    - priced_lines ist ein optionales Preis-Subset
    - Codes ohne Preis sind erlaubt, sofern sie in all_codes stehen
    - unbekannte Codes bleiben sichtbar in unknown_codes
    - priced_lines-Codes, die nicht in all_codes stehen und keine ADD-Variante sind,
      werden in invalid_priced_codes gesammelt
    """

    normalized_all_codes = _normalize_codes(all_codes)
    priced_prices = parse_priced_lines(priced_lines)

    invalid_priced_codes = []
    seen_invalid = set()
    for line in priced_lines or []:
        if not isinstance(line, str):
            continue

        line = line.strip()
        if not line:
            continue

        match = PRICE_LINE_REGEX.match(line)
        if not match:
            continue

        code = match.group("code").upper()
        if code in normalized_all_codes or re.fullmatch(r"ADD\d+", code):
            continue

        if code in seen_invalid:
            continue
        seen_invalid.add(code)
        invalid_priced_codes.append(code)

    result = {
        "base_vehicle": None,
        "exterior_color": None,
        "interior_color": None,
        "interior_trim": None,
        "security_package": None,
        "standard": [],
        "optional": [],
        "security": [],
        "unknown_codes": [],
        "invalid_priced_codes": invalid_priced_codes,
        "total_price": 0.0
    }

    # Unbekannte Codes behalten, damit sie spaeter in Excel angezeigt werden koennen.
    seen_unknown = set()
    for code in normalized_all_codes:
        if code in options_meta or code in seen_unknown:
            continue
        seen_unknown.add(code)
        result["unknown_codes"].append(code)

    # ----------------------------
    # BASE VEHICLE (separate buckets)
    # ----------------------------
    base_buckets = {
        "base_vehicle": None,
        "exterior_color": None,
        "interior_color": None,
        "interior_trim": None,
    }

    for code in all_codes:
        meta = options_meta.get(code)
        if not meta:
            continue

        category = meta.get("category")
        if category in base_buckets:
            text = (
                meta.get("text")
                or meta.get("label")
                or meta.get("description")
                or code
            )

            base_buckets[category] = {
                "code": code,
                "text": text,
                "price": priced_prices.get(code, 0.0)
            }
            result["total_price"] += priced_prices.get(code, 0.0)
            continue
        if category == "security_package":
            text = (
                meta.get("text")
                or meta.get("label")
                or meta.get("description")
                or code
            )

            result["security_package"] = {
                "code": code,
                "text": text,
                "price": priced_prices.get(code, 0.0)
            }
            result["total_price"] += priced_prices.get(code, 0.0)

    result.update(base_buckets)

    # ----------------------------
    # ALL OTHER CODES (NICHT BASE)
    # ----------------------------
    for code in all_codes:
        meta = options_meta.get(code)
        if not meta:
            continue

        category = meta.get("category")
        if category in base_buckets or category == "security_package":
            continue

        text = (
            meta.get("text")
            or meta.get("label")
            or meta.get("description")
            or code
        )

        price = priced_prices.get(code, 0.0)

        item = {
            "code": code,
            "text": text,
            "price": price
        }

        if category == "standard":
            result["standard"].append(item)
        elif category == "optional":
            result["optional"].append(item)
        elif category == "security":
            result["security"].append(item)

        result["total_price"] += price

    return result
