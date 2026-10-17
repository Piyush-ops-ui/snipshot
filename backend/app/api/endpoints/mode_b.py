"""
Mode B Endpoints:
AST-Verified Explainer Video Generation from ANY educational topic prompt.
Produces clean 1080x1920 .mp4 videos with synchronized narration and code slides in < 10 seconds.
"""

from typing import List, Optional
from pathlib import Path
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.schemas.brand import BrandKitConfig
from backend.app.core.fast_mode_b import FastModeBEngine
from backend.app.config import settings

router = APIRouter()
fast_b_engine = FastModeBEngine()


class ExplainerSceneItem(BaseModel):
    title: str
    narration_text: str
    code_snippet: str
    language: str


class GenerateExplainerRequest(BaseModel):
    prompt: str = Field(..., description="Educational topic prompt (e.g. 'JSON vs XML')")
    brand_kit: Optional[BrandKitConfig] = None
    brand_kit_id: Optional[str] = "tech_summit_trainers"


class GenerateExplainerResponse(BaseModel):
    video_url: str
    duration: float
    scenes: List[ExplainerSceneItem]
    hashtags: List[str]
    reel_id: Optional[str] = None
    elapsed_seconds: Optional[float] = None


from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import shutil
import uuid
from backend.app.api.endpoints.mode_a import parse_brand_kit_input

@router.post("/generate-explainer", response_model=GenerateExplainerResponse)
async def generate_explainer(request: GenerateExplainerRequest):
    """
    Compiles educational topic prompt into a real 1080x1920 .mp4 animated explainer video,
    saved in backend/outputs/explainer_<id>.mp4 in < 10 seconds.
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty.")

    # Resolve Brand Kit
    institute_name = "SNIPSHOT ACADEMY"
    brand_color = "#4F46E5"
    logo_base64 = None

    if request.brand_kit:
        institute_name = request.brand_kit.name or institute_name
        brand_color = request.brand_kit.primary_color or brand_color
        logo_base64 = getattr(request.brand_kit, "logo_base64", None) or getattr(request.brand_kit, "logo_path", None)

    try:
        import inspect
        kwargs = {
            "prompt": request.prompt,
            "institute_name": institute_name,
            "brand_color": brand_color,
        }
        sig = inspect.signature(fast_b_engine.generate_explainer)
        if "logo_base64" in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            kwargs["logo_base64"] = logo_base64
        result = fast_b_engine.generate_explainer(**kwargs)
        return GenerateExplainerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explainer video: {str(e)}")


@router.post("/generate-from-doc", response_model=GenerateExplainerResponse)
async def generate_from_doc(
    file: UploadFile = File(...),
    topic_focus: Optional[str] = Form(None),
    brand_kit: Optional[str] = Form(None),
):
    """
    POST /api/v1/mode-b/generate-from-doc:
    Upload ANY document (.pdf, .docx, .md, .py, .ts, .txt, etc.).
    Extracts key architectural concepts & code, and compiles a 1080x1920 .mp4 explainer video.
    """
    from backend.app.core.doc_ingest import DocumentIngestEngine
    doc_engine = DocumentIngestEngine()
    if not doc_engine.is_supported(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document format. Supported: {', '.join(sorted(doc_engine.SUPPORTED_EXTENSIONS))}"
        )

    ext = Path(file.filename or "doc.txt").suffix
    temp_id = uuid.uuid4().hex[:8]
    doc_save_path = settings.CACHE_DIR / f"upload_doc_{temp_id}{ext}"
    try:
        with open(doc_save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded document: {str(e)}")

    parsed_brand_kit = parse_brand_kit_input(brand_kit)

    try:
        import inspect
        kwargs = {
            "file_path": str(doc_save_path),
            "topic_focus": topic_focus,
            "institute_name": parsed_brand_kit.name,
            "brand_color": parsed_brand_kit.primary_color,
        }
        sig = inspect.signature(fast_b_engine.generate_explainer_from_document)
        if "logo_base64" in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            kwargs["logo_base64"] = getattr(parsed_brand_kit, "logo_base64", None)
        result = fast_b_engine.generate_explainer_from_document(**kwargs)
        return GenerateExplainerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate reel from document: {str(e)}")

