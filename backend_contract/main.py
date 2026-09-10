from typing import List

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from contract_builder_g05 import build_contract_g05
from contract_builder_g73 import build_contract_g73


app = FastAPI(title="BMW Contract API")

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


class ContractRequest(BaseModel):
    contract_series: str
    seller_code: str
    buyer_first_name: str
    buyer_surname: str
    buyer_street: str
    buyer_city: str
    buyer_postal_code: str
    buyer_country: str
    buyer_vat: str
    buyer_tax_no: str
    buyer_phone: str
    buyer_email: str
    buyer_represented_by: str
    quantity: str
    price: str
    vin: str
    order_number: str
    special_equipment: List[str]


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "BMW Contract API",
        "endpoints": ["/generate-contract", "/docs"],
    }


@app.post("/generate-contract")
def generate_contract(req: ContractRequest):
    payload = req.model_dump()
    series = (req.contract_series or "").upper()

    if series == "G05":
        file_path = build_contract_g05(payload)
        filename = "BMW_Vertrag_G05.docx"
    elif series == "G73":
        file_path = build_contract_g73(payload)
        filename = "BMW_Vertrag_G73.docx"
    else:
        raise HTTPException(status_code=400, detail="Unknown contract_series (use 'G05' or 'G73')")

    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
