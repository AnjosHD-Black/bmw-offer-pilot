import tempfile
from pathlib import Path

from openpyxl import Workbook

from backend_g05.excel_import import parse_excel_option_data


def test_parse_excel_option_data_extracts_code_label_and_price():
    wb = Workbook()
    ws = wb.active
    ws.title = 'Data'
    ws.append(['Material', 'Positionsbezeichung', 'Nettopreis', 'Währung'])
    ws.append(['BMW 3AB Zusatzpaket', 'Sitzheizung', 500, 'EUR'])
    ws.append(['Paket 10G', 'Sportpaket', 0, 'EUR'])
    ws.append(['Text 4A1 extra', 'LED', 1200, 'EUR'])

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / 'options.xlsx'
        wb.save(path)

        result = parse_excel_option_data(path)

    assert result['all_codes'] == ['3AB', '10G', '4A1']
    assert result['priced_lines'] == [
        '3AB Sitzheizung 500',
        '10G Sportpaket 0',
        '4A1 LED 1200',
    ]
    assert result['currency'] == 'EUR'
