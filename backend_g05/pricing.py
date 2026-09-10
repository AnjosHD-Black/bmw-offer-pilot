from datetime import datetime
from typing import Dict, Any


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def get_price_for_date(option: Dict[str, Any], date_str: str) -> float:
    target_date = parse_date(date_str)
    valid_price = 0.0

    for rule in option.get("prices", []):
        rule_date = parse_date(rule["from"])
        if target_date >= rule_date:
            valid_price = rule["price"]

    return valid_price


def resolve_option(code: str, options_data: Dict[str, Any], date_str: str) -> Dict[str, Any]:
    if code not in options_data:
        raise ValueError(f"Unbekannter Options-Code: {code}")

    option = options_data[code]
    price = get_price_for_date(option, date_str)

    return {
        "code": code,
        "type": option.get("type"),
        "description": option.get("description"),
        "price": price
    }


def resolve_multiple_options(codes: list, options_data: Dict[str, Any], date_str: str) -> list:
    return [resolve_option(code, options_data, date_str) for code in codes]
