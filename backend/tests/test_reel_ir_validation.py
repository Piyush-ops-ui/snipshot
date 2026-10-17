"""
Unit tests for Reel-IR schema validation and serialization.
"""

from backend.app.schemas.reel_ir import ReelIR, WordAlignment, ViewportKeyframe, LayoutMode, CodeSpotlightCard
from backend.app.schemas.brand import BrandKitConfig


def test_reel_ir_instantiation(sample_reel_ir):
    assert sample_reel_ir.reel_id == "test_reel_001"
    assert sample_reel_ir.mode == "mode_a_extract"
    assert sample_reel_ir.total_duration == 35.0
    assert len(sample_reel_ir.transcript) == 2
    assert sample_reel_ir.transcript[1].is_technical is True


def test_reel_ir_json_roundtrip(sample_reel_ir):
    json_data = sample_reel_ir.model_dump_json()
    reloaded = ReelIR.model_validate_json(json_data)
    assert reloaded.reel_id == sample_reel_ir.reel_id
    assert reloaded.viewports[0].mode == LayoutMode.SINGLE_FOCUS
    assert reloaded.brand_kit.primary_color == "#00F2FE"


def test_split_stage_keyframe_validation():
    kf = ViewportKeyframe(
        timestamp=0.0,
        mode=LayoutMode.SPLIT_STAGE,
        top_crop=(0.0, 0.0, 0.6, 1.0),
        bottom_crop=(0.5, 0.0, 0.5, 1.0),
        transition_duration=0.5,
    )
    assert kf.mode == LayoutMode.SPLIT_STAGE
    assert kf.bottom_crop is not None
    assert kf.bottom_crop[0] == 0.5


def test_code_card_validation():
    card = CodeSpotlightCard(
        id="card_1",
        start=0.0,
        end=10.0,
        language="python",
        code="def hello():\n    return 'world'",
        active_line_indices=[0],
        verified_by_ast=True,
    )
    assert card.language == "python"
    assert card.verified_by_ast is True
    assert len(card.code.split("\n")) == 2
