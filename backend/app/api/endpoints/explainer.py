"""
Explainer Endpoints (Mode B: AST-Verified Pedagogical Compiler).
Compiles topic prompts into verified code explainer Reels.
"""

from fastapi import APIRouter, HTTPException
import json

from backend.app.schemas.reel_ir import ReelIR
from backend.app.schemas.api_requests import GenerateExplainerRequest
from backend.app.schemas.brand import BrandKitConfig
from backend.app.core.mode_b_compiler import ModeBCompiler
from backend.app.config import settings

router = APIRouter()


@router.post("/generate", response_model=ReelIR)
async def generate_explainer(request: GenerateExplainerRequest):
    """
    Compiles educational topic prompt into an AST-validated Reel-IR document.
    """
    # Load brand kit if specified
    brand_kit = BrandKitConfig(id=request.brand_kit_id)
    brand_kits_path = settings.DATA_DIR / "default_brand_kits.json"
    if brand_kits_path.exists():
        try:
            with open(brand_kits_path, "r", encoding="utf-8") as f:
                kits = json.load(f)
                for k in kits:
                    if k.get("id") == request.brand_kit_id:
                        brand_kit = BrandKitConfig(**k)
                        break
        except Exception:
            pass

    compiler = ModeBCompiler(brand_kit=brand_kit)
    try:
        reel_ir = compiler.compile_prompt(
            prompt=request.prompt,
            target_duration=request.target_duration,
            brand_kit=brand_kit,
        )
        return reel_ir
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explainer: {str(e)}")
