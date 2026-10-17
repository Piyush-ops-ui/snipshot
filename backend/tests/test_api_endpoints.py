"""
Integration tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "hardware_profile" in data
    assert data["hardware_profile"]["cpu_cores"] >= 1


def test_brands_endpoint():
    response = client.get("/api/brands/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == "tech_summit_trainers"
    assert data[0]["primary_color"] == "#00F2FE"


def test_benchmark_endpoint():
    response = client.get("/api/benchmark/latest")
    assert response.status_code == 200
    data = response.json()
    assert "baseline_metrics" in data
    assert "sgpc_metrics" in data
    assert data["sgpc_metrics"]["tter_percent"] < data["baseline_metrics"]["tter_percent"]
    assert data["sgpc_metrics"]["aclr_percent"] > data["baseline_metrics"]["aclr_percent"]


def test_explainer_generation_endpoint():
    payload = {
        "prompt": "JSON vs XML",
        "target_duration": 40.0,
        "brand_kit_id": "tech_summit_trainers"
    }
    response = client.post("/api/explainer/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "mode_b_prompt"
    assert "code_cards" in data
    assert len(data["code_cards"]) >= 1
    assert len(data["transcript"]) > 0


def test_mode_b_generate_explainer_empty_prompt():
    """Validates that empty prompt returns 400."""
    response = client.post("/api/v1/mode-b/generate-explainer", json={"prompt": ""})
    assert response.status_code == 400


def test_mode_b_generate_explainer_endpoint(monkeypatch, tmp_path):
    """Tests POST /api/v1/mode-b/generate-explainer response structure."""
    dummy_mp4 = tmp_path / "explainer_dummy.mp4"
    dummy_mp4.write_bytes(b"dummy_video_bytes")

    from backend.app.core.fast_mode_b import FastModeBEngine

    def mock_generate(self, prompt, institute_name="SNIPSHOT ACADEMY", brand_color="#4F46E5"):
        return {
            "video_url": "/outputs/explainer_dummy.mp4",
            "duration": 42.5,
            "scenes": [
                {
                    "title": "Scene 1: Hook",
                    "narration_text": "Sample hook text.",
                    "code_snippet": "const x = 1;",
                    "language": "javascript"
                },
                {
                    "title": "Scene 2: Core",
                    "narration_text": "Sample core text.",
                    "code_snippet": "const y = 2;",
                    "language": "javascript"
                },
                {
                    "title": "Scene 3: Contrast",
                    "narration_text": "Sample contrast text.",
                    "code_snippet": "const z = 3;",
                    "language": "javascript"
                },
                {
                    "title": "Scene 4: Verification",
                    "narration_text": "Sample verification text.",
                    "code_snippet": "expect(x).toBe(1);",
                    "language": "javascript"
                }
            ],
            "hashtags": ["#coding", "#webdev"],
            "reel_id": "dummy"
        }

    monkeypatch.setattr(FastModeBEngine, "generate_explainer", mock_generate)

    response = client.post("/api/v1/mode-b/generate-explainer", json={"prompt": "JSON vs XML"})
    assert response.status_code == 200
    data = response.json()
    assert data["video_url"] == "/outputs/explainer_dummy.mp4"
    assert data["duration"] == 42.5
    assert len(data["scenes"]) == 4
    assert len(data["hashtags"]) >= 2


def test_static_outputs_mount(tmp_path):
    """Verifies that static mount /outputs serves files from backend/outputs."""
    from backend.app.main import ROOT_DIR
    outputs_dir = ROOT_DIR / "backend" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    test_file = outputs_dir / "mount_test.txt"
    test_file.write_text("static_mount_verified")

    response = client.get("/outputs/mount_test.txt")
    assert response.status_code == 200
    assert response.text == "static_mount_verified"
    if test_file.exists():
        test_file.unlink()


def test_mode_b_generate_from_doc_endpoint(monkeypatch, tmp_path):
    """Tests POST /api/v1/mode-b/generate-from-doc response structure with document upload."""
    from backend.app.core.fast_mode_b import FastModeBEngine

    def mock_generate_from_doc(self, file_path, topic_focus=None, institute_name="SNIPSHOT ACADEMY", brand_color="#4F46E5"):
        return {
            "video_url": "/outputs/explainer_doc_test.mp4",
            "duration": 38.0,
            "scenes": [
                {"title": "Scene 1: Hook", "narration_text": "Doc hook", "code_snippet": "x = 1", "language": "python"},
                {"title": "Scene 2: Core", "narration_text": "Doc core", "code_snippet": "y = 2", "language": "python"},
                {"title": "Scene 3: Contrast", "narration_text": "Doc contrast", "code_snippet": "z = 3", "language": "python"},
                {"title": "Scene 4: Verification", "narration_text": "Doc verify", "code_snippet": "assert x == 1", "language": "python"},
            ],
            "hashtags": ["#python", "#docs"],
            "reel_id": "doc_test"
        }

    monkeypatch.setattr(FastModeBEngine, "generate_explainer_from_document", mock_generate_from_doc)

    doc_content = b"# Architecture\n\n```python\ndef hello():\n    return 'snipshot'\n```\n"
    files = {"file": ("architecture.md", doc_content, "text/markdown")}
    data = {"topic_focus": "Architecture"}

    response = client.post("/api/v1/mode-b/generate-from-doc", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["video_url"] == "/outputs/explainer_doc_test.mp4"
    assert len(res_data["scenes"]) == 4
    assert res_data["duration"] == 38.0

