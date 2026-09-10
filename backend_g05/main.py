import os
import json
import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vehicle_parser import normalize_vehicle_input
from excel_builder import build_excel
from excel_import import parse_excel_option_data
# from pdf_builder import build_pdf   # später aktivieren


# ======================================================
# APP
# ======================================================
app = FastAPI(title="BMW Offer Pilot API")

# CORS - Erlaube Frontend-Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "https://bmw-offer-pilot.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ======================================================
# HEALTH CHECK
# ======================================================
@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "BMW Offer Pilot API",
        "endpoints": ["/generate", "/debug/parse", "/docs"]
    }


# ======================================================
# REQUEST SCHEMA
# ======================================================
class GenerateRequest(BaseModel):
    date: str
    model: str
    color: str
    interior: str
    priced_lines: List[str]
    all_codes: List[str]
    format: str  # "excel" | "pdf"


# ======================================================
# LOAD OPTIONS META
# ======================================================
def load_options():
    path = os.path.join(BASE_DIR, "options_meta_g05.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_additions_options():
    path = os.path.join(BASE_DIR, "additions_options_g05.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ======================================================
# DEBUG PARSER (SEHR WICHTIG)
# ======================================================
@app.post("/debug/parse")
def debug_parse(req: GenerateRequest):
    options_meta = load_options()

    parsed = normalize_vehicle_input(
        model=req.model,
        color=req.color,
        interior=req.interior,
        all_codes=req.all_codes,
        priced_lines=req.priced_lines,
        options_meta=options_meta
    )

    return parsed


# ======================================================
# GENERATE EXCEL / PDF
# ======================================================
@app.post("/generate")
def generate(req: GenerateRequest):
    options_meta = load_options()

    parsed = normalize_vehicle_input(
        model=req.model,
        color=req.color,
        interior=req.interior,
        all_codes=req.all_codes,
        priced_lines=req.priced_lines,
        options_meta=options_meta
    )

    if req.format.lower() == "excel":
        file_path = build_excel(parsed)

        return FileResponse(
            file_path,
            filename="BMW_Quotation.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # if req.format.lower() == "pdf":
    #     file_path = build_pdf(parsed)
    #     return FileResponse(
    #         file_path,
    #         filename="BMW_Quotation.pdf",
    #         media_type="application/pdf"
    #     )

    raise HTTPException(
        status_code=400,
        detail="Unknown format (use 'excel')"
    )


# ======================================================
# ADDITIONS CHECKLIST OPTIONS
# ======================================================
@app.get("/additions-options")
def get_additions_options():
    """Gibt alle verfügbaren Additions-Optionen mit Preisen aus der JSON zurück"""
    additions = load_additions_options()
    return {"options": additions}


# ======================================================
# EXCEL UPLOAD
# ======================================================
@app.post("/upload-excel-options")
async def upload_excel_options(file: UploadFile = File(...)):
    """
    Importiert eine Excel-Datei mit Sheet 'Data' und konvertiert sie in das
    gleiche interne Format wie die manuelle Eingabe.
    """
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Nur .xlsx Dateien erlaubt")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = Path(tmp.name)

        try:
            options_meta = load_options()
            known_codes = list(options_meta.keys())
            data = parse_excel_option_data(tmp_path, known_codes=known_codes)
        finally:
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
