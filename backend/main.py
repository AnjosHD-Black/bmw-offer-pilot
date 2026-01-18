import os
import json
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vehicle_parser import normalize_vehicle_input
from excel_builder import build_excel
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
        "https://*.vercel.app",  # Alle Vercel-Deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
    path = os.path.join(BASE_DIR, "options_meta.json")
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
