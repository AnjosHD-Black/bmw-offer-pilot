import re
from typing import List, Dict

# ======================================================
# PRICE LINE PARSER
# ======================================================
PRICE_LINE_REGEX = re.compile(
    r"^(?P<code>[A-Za-z0-9]{3,6})\s+(?P<text>.+?)\s+(?P<price>\d[\d.,]*\d|\d)$"
)


def _parse_price(raw: str) -> float:
    """
    Wandelt Preistexte in Zahlen um, egal ob mit Tausenderpunkt
    ('1.999,00'), englischem Format ('1,999.00') oder ohne Trenner
    ('1999.00', '8989898') geschrieben.
    """
    value = raw.strip()

    if "." in value and "," in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        last_group = value.split(",")[-1]
        if len(last_group) == 3:
            value = value.replace(",", "")
        else:
            value = value.replace(",", ".")
    elif "." in value:
        last_group = value.split(".")[-1]
        if len(last_group) == 3:
            value = value.replace(".", "")

    return float(value)


def _resolve_price_code(raw_code: str, known_codes=None) -> str:
    """
    Manche Systeme liefern 6-stellige Codes vor dem Preis, wobei nur die
    letzten 3 oder 4 Zeichen der eigentliche Options-Code sind
    (z.B. '1406AC' -> '6AC'). Die ersten 2 oder 3 Zeichen werden ignoriert.
    """
    code = raw_code.strip().upper()
    if len(code) != 6:
        return code

    last_four = code[2:]
    last_three = code[3:]

    if known_codes:
        if last_four in known_codes:
            return last_four
        if last_three in known_codes:
            return last_three

    return last_four


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


def parse_priced_lines(lines: List[str], known_codes=None) -> Dict[str, float]:
    """
    Extrahiert Preise aus z.B.:
    '3AB Sitzheizung 100'
    '3AD M-Lenkrad 3000'
    '1406AC Sonderausstattung 100' (6-stellig, nur '6AC' zaehlt)

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

        code = _resolve_price_code(match.group("code"), known_codes)
        price = _parse_price(match.group("price"))
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
    known_codes = set(normalized_all_codes) | set(options_meta.keys())
    priced_prices = parse_priced_lines(priced_lines, known_codes=known_codes)
    total_occurrences: Dict[str, int] = {}
    for raw_code in all_codes:
        code = raw_code.strip().upper() if isinstance(raw_code, str) else raw_code
        total_occurrences[code] = total_occurrences.get(code, 0) + 1

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

        code = _resolve_price_code(match.group("code"), known_codes)
        ambiguous_meta = options_meta.get(code)
        is_single_ambiguous_code = (
            isinstance(ambiguous_meta, list)
            and total_occurrences.get(code, 0) == 1
        )
        if code in normalized_all_codes and not is_single_ambiguous_code:
            continue
        if re.fullmatch(r"ADD\d+", code):
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
    # CODES AUFLOESEN (mit Vorkommen-Logik fuer mehrdeutige Codes)
    # ----------------------------
    # Manche Codes bedeuten je nach Vorkommen etwas anderes, z.B. '300'
    # beim ersten Mal Standard-Ausstattung, beim zweiten Mal die Farbe.
    # options_meta kann dafuer statt eines dicts eine Liste von dicts enthalten.
    base_buckets = {
        "base_vehicle": None,
        "exterior_color": None,
        "interior_color": None,
        "interior_trim": None,
    }

    occurrence_counts: Dict[str, int] = {}
    for raw_code in all_codes:
        code = raw_code.strip().upper() if isinstance(raw_code, str) else raw_code
        meta_entry = options_meta.get(code)
        if not meta_entry:
            continue

        occurrence_index = occurrence_counts.get(code, 0)
        occurrence_counts[code] = occurrence_index + 1

        if isinstance(meta_entry, list):
            if not meta_entry:
                continue
            if occurrence_index == 0:
                meta = next(
                    (entry for entry in meta_entry if entry.get("category") == "standard"),
                    meta_entry[0]
                )
            else:
                meta = next(
                    (entry for entry in meta_entry if entry.get("category") == "exterior_color"),
                    meta_entry[-1]
                )
        else:
            meta = meta_entry

        category = meta.get("category")
        text = (
            meta.get("text")
            or meta.get("label")
            or meta.get("description")
            or code
        )
        # Bei mehrdeutigen Codes (mehrfach in all_codes) bekommt nur das
        # letzte Vorkommen den eingegebenen Preis, alle davor sind 0.0.
        is_last_occurrence = occurrence_index == total_occurrences[code] - 1
        is_ambiguous_code = isinstance(meta_entry, list)
        price = (
            priced_prices.get(code, 0.0)
            if is_last_occurrence and (not is_ambiguous_code or total_occurrences[code] > 1)
            else 0.0
        )

        if category in base_buckets:
            base_buckets[category] = {
                "code": code,
                "text": text,
                "price": price
            }
            result["total_price"] += price
            continue

        if category == "security_package":
            result["security_package"] = {
                "code": code,
                "text": text,
                "price": price
            }
            result["total_price"] += price
            continue

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

    result.update(base_buckets)

    return result
