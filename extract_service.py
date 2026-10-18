import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


EMAIL = "24f2006214@ds.study.iitm.ac.in"
app = FastAPI()


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1)


class InvoiceFields(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


def first_match(patterns: list[str], text: str, flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return None


@app.post("/extract", response_model=InvoiceFields)
async def extract(payload: ExtractRequest):
    text = payload.text.strip()
    vendor = first_match(
        [
            r"(?:vendor|supplier|merchant|billed\s+by|from)\s*[:#-]?\s*([^\n\r]+)",
        ],
        text,
    )
    amount_text = first_match(
        [
            r"(?:total\s+(?:due|amount)|amount\s+due|balance\s+due|grand\s+total)\s*[:#-]?\s*[^\d-]*([\d,]+(?:\.\d{1,2})?)",
        ],
        text,
    )
    currency = first_match([r"\b(USD|EUR|GBP)\b"], text)
    date = first_match(
        [
            r"(?:due\s+date|payment\s+due|date\s+due)\s*[:#-]?\s*(\d{4}-\d{2}-\d{2})",
            r"\b(2026-\d{2}-\d{2})\b",
        ],
        text,
    )

    if not all((vendor, amount_text, currency, date)):
        raise HTTPException(status_code=422, detail="Could not extract required invoice fields")

    return InvoiceFields(
        vendor=vendor,
        amount=float(amount_text.replace(",", "")),
        currency=currency.upper(),
        date=date,
    )

