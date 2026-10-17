"""
Unit tests for Smart 9:16 Reframer (Dead-Zone Camera, SplitStage, Code Cards).
"""

from backend.app.core.smart_reframer import SmartReframer
from backend.app.schemas.reel_ir import LayoutMode
from backend.app.schemas.tssg import ScreenToken


def test_split_stage_trigger_on_bimodal_activity():
    reframer = SmartReframer()
    
    # Left IDE tokens (x < 1000) and Right Terminal tokens (x > 950)
    tokens = [
        ScreenToken(
            id="st_left_1", text="const app = express();", norm_text="const app = express();",
            phonetic_code="KNS", bbox=(80, 100, 300, 30), normalized_bbox=(0.04, 0.09, 0.15, 0.02),
            timestamp=5.0, is_identifier=True,
        ),
        ScreenToken(
            id="st_left_2", text="app.listen(3000);", norm_text="app.listen(3000);",
            phonetic_code="PLS", bbox=(80, 140, 260, 30), normalized_bbox=(0.04, 0.13, 0.13, 0.02),
            timestamp=6.0, is_identifier=True,
        ),
        ScreenToken(
            id="st_left_3", text="@RestController", norm_text="@restcontroller",
            phonetic_code="RST", bbox=(80, 180, 200, 30), normalized_bbox=(0.04, 0.16, 0.10, 0.02),
            timestamp=7.0, is_identifier=True,
        ),
        ScreenToken(
            id="st_right_1", text="kubectl get pods", norm_text="kubectl get pods",
            phonetic_code="KBK", bbox=(1100, 500, 340, 30), normalized_bbox=(0.57, 0.46, 0.17, 0.02),
            timestamp=5.5, is_identifier=True,
        ),
        ScreenToken(
            id="st_right_2", text="pod/api-server-79 Running", norm_text="pod/api-server-79 running",
            phonetic_code="PDR", bbox=(1100, 540, 400, 30), normalized_bbox=(0.57, 0.50, 0.20, 0.02),
            timestamp=7.2, is_identifier=True,
        ),
    ]

    keyframes, code_cards, layout_mode = reframer.compute_viewports(0.0, 10.0, tokens)
    
    assert layout_mode == LayoutMode.SPLIT_STAGE
    assert len(keyframes) >= 1
    assert keyframes[0].mode == LayoutMode.SPLIT_STAGE
    assert keyframes[0].top_crop is not None
    assert keyframes[0].bottom_crop is not None


def test_single_focus_deadzone_hold():
    reframer = SmartReframer()
    
    # Clustered tokens on left IDE only
    tokens = [
        ScreenToken(
            id="st_1", text="def main():", norm_text="def main():",
            phonetic_code="DFM", bbox=(100, 100, 180, 30), normalized_bbox=(0.05, 0.09, 0.09, 0.02),
            timestamp=2.0, is_identifier=True,
        ),
        ScreenToken(
            id="st_2", text="    return 0", norm_text="return 0",
            phonetic_code="RTN", bbox=(120, 140, 160, 30), normalized_bbox=(0.06, 0.13, 0.08, 0.02),
            timestamp=4.0, is_identifier=True,
        ),
    ]

    keyframes, code_cards, layout_mode = reframer.compute_viewports(0.0, 10.0, tokens)
    assert layout_mode == LayoutMode.SINGLE_FOCUS
    assert keyframes[0].mode == LayoutMode.SINGLE_FOCUS
    assert keyframes[0].bottom_crop is None


def test_single_focus_deadzone_l1_smoothed_camera_motion():
    reframer = SmartReframer()
    
    # Tokens initially at left IDE (x centroid ~0.15)
    # Then tokens at t=5.0 shift significantly to the right (x centroid ~0.70)
    tokens = [
        ScreenToken(
            id="st_1", text="let a = 1;", norm_text="let a = 1;",
            phonetic_code="LT", bbox=(100, 100, 200, 30), normalized_bbox=(0.05, 0.09, 0.10, 0.02),
            timestamp=1.0, is_identifier=True,
        ),
        ScreenToken(
            id="st_2", text="let b = 2;", norm_text="let b = 2;",
            phonetic_code="LT", bbox=(100, 140, 200, 30), normalized_bbox=(0.05, 0.13, 0.10, 0.02),
            timestamp=2.0, is_identifier=True,
        ),
        ScreenToken(
            id="st_shift", text="console.log(veryLongResultIdentifier);", norm_text="console.log",
            phonetic_code="KNS", bbox=(1200, 200, 300, 30), normalized_bbox=(0.62, 0.18, 0.16, 0.02),
            timestamp=5.0, is_identifier=True,
        ),
    ]

    keyframes, code_cards, layout_mode = reframer.compute_viewports(0.0, 8.0, tokens)
    assert len(keyframes) == 2
    kf0, kf1 = keyframes[0], keyframes[1]
    assert kf0.timestamp == 0.0
    assert kf1.timestamp == 4.0
    # Camera moved to follow centroid with L1 smoothing
    assert kf1.top_crop[0] > kf0.top_crop[0]
    assert kf1.transition_duration == 0.6


def test_readable916_ast_spotlight_trigger_on_wide_code_lines():
    reframer = SmartReframer()
    
    # Single wide source line exceeding 850px width threshold
    wide_tokens = [
        ScreenToken(
            id="st_wide_1",
            text="const veryLongConfigurationObject = { endpoint: 'https://api.techsummit.com/v1/stream', retry: 5 };",
            norm_text="const verylongconfigurationobject",
            phonetic_code="KNS",
            bbox=(80, 200, 920, 32),  # width = 920px > 850px
            normalized_bbox=(0.04, 0.18, 0.48, 0.03),
            timestamp=3.0,
            is_identifier=True,
        ),
    ]

    keyframes, code_cards, layout_mode = reframer.compute_viewports(0.0, 10.0, wide_tokens)
    assert len(code_cards) >= 1
    assert code_cards[0].verified_by_ast is True
    assert "veryLongConfigurationObject" in code_cards[0].code
    assert layout_mode == LayoutMode.CODE_SPOTLIGHT
    assert keyframes[0].mode == LayoutMode.CODE_SPOTLIGHT


def test_dual_roi_splitstage_coordinates_and_dimensions():
    reframer = SmartReframer()
    assert reframer.SPLIT_TOP_DIMENSIONS == (1080, 1020)
    assert reframer.SPLIT_BOTTOM_DIMENSIONS == (1080, 680)
    assert reframer.WIDE_CODE_THRESHOLD_PX == 850

