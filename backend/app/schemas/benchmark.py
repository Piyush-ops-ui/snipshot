"""
Schemas for automated benchmark evaluation and metrics tracking.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class EvaluationMetrics(BaseModel):
    clip_id: str
    tter_percent: float = Field(..., description="Technical Term Error Rate (%) - lower is better")
    hinglish_wer_percent: float = Field(..., description="Word Error Rate (%) across Hinglish segments")
    wt_mae_ms: float = Field(..., description="Word Timestamp Mean Absolute Error (ms)")
    ctbr_percent: float = Field(..., description="Complete-Thought Boundary Rate (%) - higher is better")
    aclr_percent: float = Field(..., description="Active Code Legibility Rate (%) - higher is better")
    processing_time_sec: float = Field(..., description="Total pipeline processing time")
    char_clipping_rate_percent: float = Field(default=0.0, description="Percentage of frames with clipped characters")


class BenchmarkRunResult(BaseModel):
    benchmark_version: str = "1.0.0"
    timestamp: str
    hardware_tier: str
    baseline_metrics: EvaluationMetrics
    sgpc_metrics: EvaluationMetrics
    relative_improvements: Dict[str, str] = Field(default_factory=dict)
    ablation_results: Dict[str, Any] = Field(default_factory=dict)
