import os
import tempfile
import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from excel_import import parse_excel_option_data


app = FastAPI(title="Excel Upload API")


@app.post("/upload/excel-options")
async def upload_excel_options(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Nur .xlsx Dateien erlaubt")

    try:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = Path(tmp.name)

        data = parse_excel_option_data(tmp_path)

        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        return JSONResponse(content={
            "all_codes": data["all_codes"],
            "priced_lines": data["priced_lines"],
            "currency": data["currency"],
        })

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Excel-Import fehlgeschlagen: {exc}")
