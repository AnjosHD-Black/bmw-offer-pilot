import pytest

from backend_g05.vehicle_parser import normalize_vehicle_input as normalize_g05
from backend_g73.vehicle_parser import normalize_vehicle_input as normalize_g73


@pytest.mark.parametrize(
    "normalize_fn",
    [normalize_g05, normalize_g73],
)
def test_unknown_and_missing_price_are_separated(normalize_fn):
    result = normalize_fn(
        model="",
        color="",
        interior="",
        all_codes=["3AB", "ZZZ1"],
        priced_lines=["3AB Sitzheizung 500"],
        options_meta={"3AB": {"category": "optional", "text": "Sitzheizung"}},
    )

    assert result["unknown_codes"] == ["ZZZ1"]
    assert result["optional"][0]["code"] == "3AB"
    assert result["optional"][0]["price"] == 500.0
    assert "invalid_priced_codes" in result


@pytest.mark.parametrize(
    "normalize_fn",
    [normalize_g05, normalize_g73],
)
def test_priced_code_not_in_all_codes_is_reported(normalize_fn):
    result = normalize_fn(
        model="",
        color="",
        interior="",
        all_codes=["3AB"],
        priced_lines=["9ZZ Extra 450", "3AB Sitzheizung 500"],
        options_meta={"3AB": {"category": "optional", "text": "Sitzheizung"}},
    )

    assert "9ZZ" in result["invalid_priced_codes"]
    assert result["optional"][0]["code"] == "3AB"
