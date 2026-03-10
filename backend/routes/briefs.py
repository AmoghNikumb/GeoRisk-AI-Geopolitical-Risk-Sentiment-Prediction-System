"""routes/briefs.py — POST /api/briefs/generate"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter()


class BriefRequest(BaseModel):
    country_a: str
    country_b: str
    force: bool = False


@router.post("/briefs/generate")
def generate_brief(req: BriefRequest):
    try:
        from llm.brief_generator import BriefGenerator
        brief = BriefGenerator().generate(
            req.country_a.upper(), req.country_b.upper(),
            trigger="on_demand", force=req.force
        )
        if not brief:
            raise HTTPException(status_code=500, detail="Brief generation failed")
        return {
            "headline": brief.headline,
            "risk_level": brief.risk_level,
            "summary": brief.summary,
            "key_drivers": brief.key_drivers,
            "market_implications": brief.market_implications,
            "outlook_72hr": brief.outlook_72hr,
            "confidence": brief.confidence,
            "generated_at": brief.generated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

