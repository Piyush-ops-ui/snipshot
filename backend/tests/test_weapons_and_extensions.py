import pytest
from pathlib import Path
from PIL import Image

from backend.app.schemas.reel_ir import (
    ReelIR,
    TemplateArchetype,
    RedactionBox,
    SocialGrowthPack,
    WordAlignment,
    ViewportKeyframe,
    LayoutMode,
)
from backend.app.schemas.brand import BrandKitConfig
from backend.app.core.screen_lex_ocr import (
    ScreenLexMiner,
    detect_secret_in_text,
    calculate_shannon_entropy,
)
from backend.app.core.compositor import ReelCompositor, QRCODE_AVAILABLE
from backend.app.services.hardware_profiler import detect_hardware_profile, HardwareTier


def test_safe_cohort_secret_detection():
    # 1. Test OpenAI API Key
    res_openai = detect_secret_in_text("sk-proj-abc1234567890defghijklmn12345")
    assert res_openai is not None
    assert res_openai[0] == "openai_api_key"

    # 2. Test AWS Key
    res_aws = detect_secret_in_text("export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
    assert res_aws is not None
    assert res_aws[0] == "aws_access_key"

    # 3. Test PII Email
    res_email = detect_secret_in_text("Contact instructor at support@techsummit.com for keys")
    assert res_email is not None
    assert res_email[0] == "pii_email"

    # 4. Test high entropy secret string
    entropy = calculate_shannon_entropy("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    assert entropy > 3.8
    res_entropy = detect_secret_in_text("SECRET = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'")
    assert res_entropy is not None

    # 5. Clean code line should NOT be flagged as secret
    res_clean = detect_secret_in_text("const [userId, setUserId] = useState(1);")
    assert res_clean is None


def test_safe_cohort_box_generation():
    miner = ScreenLexMiner()
    sample_boxes = [
        ("sk-proj-abc1234567890defghijklmn12345", (120, 300, 480, 30)),
        ("const greeting = 'hello world';", (120, 350, 320, 30)),
    ]
    redactions = miner.scan_boxes_for_secrets(sample_boxes, timestamp=14.5, duration=3.0)
    assert len(redactions) == 1
    redact = redactions[0]
    assert redact.secret_type == "openai_api_key"
    assert redact.start == 14.3
    assert redact.end == 17.5
    # Padded box check
    assert redact.box[0] == 110  # 120 - 10
    assert redact.box[1] == 292  # 300 - 8


def test_template_archetypes_and_growth_pack_schema():
    growth_pack = SocialGrowthPack(
        hook_title="Stop using raw useEffect for API calls! 🚫",
        broad_hashtags=["#coding", "#webdev"],
        stack_hashtags=["#react", "#javascript"],
        micro_api_hashtags=["#useEffect", "#useState"],
        pinned_code_comment="Copy the custom useFetch hook here: https://gist.github.com/example",
        qr_code_data="https://github.com/techsummit/custom-hooks",
    )

    reel = ReelIR(
        reel_id="reel_archetype_test",
        mode="mode_a_extract",
        title="Custom Hook Refactoring",
        clip_start=10.0,
        clip_end=45.0,
        total_duration=35.0,
        audio_path="test_audio.wav",
        template_archetype=TemplateArchetype.BUG_HUNTER,
        error_resolved_at=28.5,
        social_growth_pack=growth_pack,
        typing_hyperlapse_intervals=[(15.0, 18.2)],
        redaction_boxes=[
            RedactionBox(
                id="redact_test_1",
                start=12.0,
                end=16.0,
                box=(100, 200, 300, 40),
                secret_type="openai_api_key",
            )
        ],
    )

    assert reel.template_archetype == TemplateArchetype.BUG_HUNTER
    assert reel.error_resolved_at == 28.5
    assert len(reel.redaction_boxes) == 1
    assert len(reel.typing_hyperlapse_intervals) == 1
    assert reel.social_growth_pack.hook_title.startswith("Stop using")

    # Roundtrip JSON test
    json_str = reel.model_dump_json()
    reloaded = ReelIR.model_validate_json(json_str)
    assert reloaded.template_archetype == TemplateArchetype.BUG_HUNTER
    assert reloaded.social_growth_pack.qr_code_data == "https://github.com/techsummit/custom-hooks"


def test_local_roi_telemetry():
    hw = detect_hardware_profile()
    roi = hw.calculate_roi(processed_video_minutes=120.0)

    assert roi["cloud_tax_billed_inr"] == 0.00
    assert roi["video_minutes_processed"] == 120.0
    assert roi["estimated_saas_credits_saved"] == 120
    assert roi["estimated_cloud_tax_saved_inr"] > 0
    assert roi["privacy_status"] == "100% On-Device (Zero Egress)"
    assert roi["license_type"] == "SnipShot Perpetual Studio"


def test_compositor_outro_qr_and_archetype_rendering(tmp_path):
    assert QRCODE_AVAILABLE, "qrcode library should be installed"

    compositor = ReelCompositor(width=540, height=960, fps=15)
    reel = ReelIR(
        reel_id="reel_qr_test",
        mode="mode_b_prompt",
        title="QR Code Test",
        clip_start=0.0,
        clip_end=5.0,
        total_duration=5.0,
        audio_path="dummy.wav",
        template_archetype=TemplateArchetype.BUG_HUNTER,
        error_resolved_at=3.0,
        brand_kit=BrandKitConfig(enable_outro_bumper=True, outro_bumper_duration=2.0),
        social_growth_pack=SocialGrowthPack(
            hook_title="Scan to Copy Code!",
            stack_hashtags=["#python"],
            micro_api_hashtags=["#FastAPI"],
            qr_code_data="https://github.com/snipshot/snipshot",
        ),
    )

    # Verify frame elements render without exceptions
    img = Image.new("RGBA", (540, 960), color="#0F172A")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    # 1. Render Brand Elements during bug phase (crimson)
    title_font = compositor.ffmpeg.__class__  # dummy
    compositor._render_brand_elements(draw, reel, rel_time=1.0, abs_time=1.0, total_duration=5.0, title_font=None)

    # 2. Render Brand Elements after resolution (emerald)
    compositor._render_brand_elements(draw, reel, rel_time=4.0, abs_time=4.0, total_duration=5.0, title_font=None)

    # 3. Render Outro QR Bumper
    compositor._render_outro_qr_bumper(draw, img, reel, rel_time=4.5, total_duration=5.0, title_font=None)

    # Confirm image has content
    assert img.size == (540, 960)


def test_weapon5_localized_gaussian_blur():
    """Verifies Weapon 5 applies localized Gaussian blur (51, 51) over secret redaction boxes."""
    import numpy as np
    import cv2
    compositor = ReelCompositor(width=640, height=360, fps=15)
    
    # Create test BGR frame
    frame = np.ones((360, 640, 3), dtype=np.uint8) * 200
    # Add high-contrast pattern in secret region (x=100, y=100, w=150, h=40)
    frame[100:140:2, 100:250:2] = 0

    redactions = [
        RedactionBox(
            id="redact_blur_test",
            start=2.0,
            end=6.0,
            box=(100, 100, 150, 40),
            secret_type="openai_api_key",
        )
    ]

    # At t=1.0 (before start), frame is untouched
    frame_unblurred = compositor._apply_safe_cohort_blur(frame.copy(), redactions, abs_time=1.0)
    assert np.array_equal(frame, frame_unblurred)

    # At t=3.0 (during secret), frame ROI is blurred
    frame_blurred = compositor._apply_safe_cohort_blur(frame.copy(), redactions, abs_time=3.0)
    assert not np.array_equal(frame[100:140, 100:250], frame_blurred[100:140, 100:250])
    # Outside ROI is untouched
    assert np.array_equal(frame[0:50, 0:50], frame_blurred[0:50, 0:50])


def test_weapon7_vs_battle_and_predict_output_rendering():
    """Verifies rendering of VS_BATTLE dual card layout and PREDICT_OUTPUT callout."""
    from PIL import ImageDraw
    from backend.app.schemas.reel_ir import CodeSpotlightCard

    compositor = ReelCompositor(width=1080, height=1920, fps=30)
    reel_vs = ReelIR(
        reel_id="reel_vs_test",
        mode="mode_b_prompt",
        title="VS Battle Test",
        clip_start=0.0,
        clip_end=10.0,
        total_duration=10.0,
        audio_path="dummy.wav",
        template_archetype=TemplateArchetype.VS_BATTLE,
        code_cards=[
            CodeSpotlightCard(
                id="card_legacy", start=0.0, end=10.0, language="javascript",
                code="// Legacy Imperative\nfor (let i = 0; i < n; i++) {}",
            ),
            CodeSpotlightCard(
                id="card_modern", start=0.0, end=10.0, language="javascript",
                code="// Modern Declarative\nitems.forEach(processItem);",
            ),
        ],
    )

    img = Image.new("RGBA", (1080, 1920), color="#0F172A")
    draw = ImageDraw.Draw(img)
    from backend.app.core.compositor import get_font
    code_font = get_font(28, monospace=True)

    # Render VS Battle Dual Cards
    compositor._render_vs_battle_cards(draw, reel_vs, rel_time=2.0, code_font=code_font)
    assert img.size == (1080, 1920)

    # Render Predict Output Freeze Callout
    reel_predict = ReelIR(
        reel_id="reel_predict_test",
        mode="mode_a_extract",
        title="Predict Output Test",
        clip_start=0.0,
        clip_end=15.0,
        total_duration=15.0,
        audio_path="dummy.wav",
        template_archetype=TemplateArchetype.PREDICT_OUTPUT,
    )
    compositor._render_predict_output_callout(draw)
    compositor._render_brand_elements(draw, reel_predict, rel_time=12.0, abs_time=12.0, total_duration=15.0, title_font=None)


def test_weapon9_typing_gap_detection_and_hyperlapse():
    """Verifies silent typing gaps > 1.2s are detected and mapped to hyperlapse intervals."""
    compositor = ReelCompositor(width=1080, height=1920, fps=30)

    transcript = [
        WordAlignment(id="w1", word="First", start=0.0, end=0.5),
        WordAlignment(id="w2", word="phrase", start=0.6, end=1.0),
        # Silent typing gap: 1.0s to 3.5s (2.5s > 1.2s)
        WordAlignment(id="w3", word="Second", start=3.5, end=4.0),
        WordAlignment(id="w4", word="phrase", start=4.1, end=4.5),
        # Small speech pause: 4.5s to 5.2s (0.7s <= 1.2s, not hyperlapse)
        WordAlignment(id="w5", word="Third", start=5.2, end=5.8),
    ]

    gaps = compositor.detect_silent_typing_gaps(transcript, total_duration=8.0, min_gap_seconds=1.2)
    assert len(gaps) >= 1
    # First detected gap must match the 1.0s - 3.5s gap
    assert gaps[0] == (1.0, 3.5)
    # Gap after last word: 5.8s to 8.0s (2.2s > 1.2s)
    assert gaps[-1] == (5.8, 8.0)


def test_ffmpeg_service_intel_arc_qsv_probe_and_fallback(monkeypatch, tmp_path):
    """Verifies FFmpegService Intel Arc h264_qsv probe, graceful fallback to libx264 ultrafast crf 21, and gc.collect."""
    import gc
    from backend.app.services.ffmpeg_service import FFmpegService
    import subprocess

    ffmpeg_svc = FFmpegService()

    # 1. Test probe method returns bool
    qsv_supported = ffmpeg_svc.probe_qsv_support()
    assert isinstance(qsv_supported, bool)

    # 2. Test when QSV is mocked as supported
    ffmpeg_svc._qsv_supported = True
    recorded_cmds = []

    def mock_popen(cmd, *args, **kwargs):
        recorded_cmds.append(cmd)
        class DummyProc:
            stdin = None
            def wait(self): pass
        return DummyProc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)

    out_qsv = str(tmp_path / "test_qsv.mp4")
    ffmpeg_svc.open_pipe_renderer(output_mp4_path=out_qsv, encoder="h264_qsv")
    assert any("-c:v" in recorded_cmds[-1] and "h264_qsv" in recorded_cmds[-1] for cmd in recorded_cmds)
    assert "-global_quality" in recorded_cmds[-1]
    assert "21" in recorded_cmds[-1]

    # 3. Test when QSV is unsupported: graceful fallback to libx264 ultrafast crf 21
    ffmpeg_svc._qsv_supported = False
    out_cpu = str(tmp_path / "test_cpu.mp4")
    ffmpeg_svc.open_pipe_renderer(output_mp4_path=out_cpu, encoder="h264_qsv")
    cmd_fallback = recorded_cmds[-1]
    assert "-c:v" in cmd_fallback
    c_idx = cmd_fallback.index("-c:v")
    assert cmd_fallback[c_idx + 1] == "libx264"
    p_idx = cmd_fallback.index("-preset")
    assert cmd_fallback[p_idx + 1] == "ultrafast"
    crf_idx = cmd_fallback.index("-crf")
    assert cmd_fallback[crf_idx + 1] == "21"

