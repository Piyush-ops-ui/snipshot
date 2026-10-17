"""
Central API Router aggregation.
"""

from fastapi import APIRouter

from backend.app.api.endpoints import lecture, explainer, timeline, render, brands, benchmark, mode_a, mode_b, telemetry

api_router = APIRouter()

api_router.include_router(lecture.router, prefix="/lecture", tags=["Mode A: Lecture Decompiler"])
api_router.include_router(explainer.router, prefix="/explainer", tags=["Mode B: Prompt Compiler"])
api_router.include_router(mode_a.router, prefix="/mode-a", tags=["Mode A: Lecture Decompiler"])
api_router.include_router(mode_b.router, prefix="/mode-b", tags=["Mode B: Prompt Explainer"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry & Bandit"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["Timeline & Provenance"])
api_router.include_router(render.router, prefix="/render", tags=["Render & Delivery"])
api_router.include_router(brands.router, prefix="/brands", tags=["Brand Kits"])
api_router.include_router(benchmark.router, prefix="/benchmark", tags=["Benchmark & Metrics"])
