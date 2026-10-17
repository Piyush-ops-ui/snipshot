import os
import shutil
from pathlib import Path
from huggingface_hub import HfApi

BASE_DIR = Path(__file__).resolve().parent.parent

# Read HF token from environment or local .env
TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("HF_TOKEN="):
                TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

REPO_ID = os.environ.get("HF_SPACE_ID", "Ninad0109/snipshot")
DIST_DIR = BASE_DIR / "frontend" / "dist"
DEPLOY_DIR = BASE_DIR / "dist_space"

print(f"📦 Preparing deployment package in {DEPLOY_DIR}...")
if DEPLOY_DIR.exists():
    shutil.rmtree(DEPLOY_DIR)
DEPLOY_DIR.mkdir(parents=True)

# 1. Copy compiled frontend (index.html, assets, outputs, samples, provenance)
for item in DIST_DIR.iterdir():
    target = DEPLOY_DIR / item.name
    if item.is_dir():
        print(f"  Copying directory: {item.name}")
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        print(f"  Copying file: {item.name}")
        shutil.copy2(item, target)

# 2. Add .gitattributes with Git LFS tracking for video files
gitattributes_content = """*.7z filter=lfs diff=lfs merge=lfs -text
*.arrow filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.bz2 filter=lfs diff=lfs merge=lfs -text
*.ckpt filter=lfs diff=lfs merge=lfs -text
*.gz filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.webm filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text
*.tar.* filter=lfs diff=lfs merge=lfs -text
*.tar filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
"""
(DEPLOY_DIR / ".gitattributes").write_text(gitattributes_content, encoding="utf-8")

# 3. Add README.md with Hugging Face Space metadata
readme_content = """---
title: Snipshot - Autonomous 9:16 Video Studio
emoji: 🎬
colorFrom: indigo
colorTo: purple
sdk: static
pinned: false
---

# 🎬 SnipShot Perpetual Studio

**Screen-Grounded Pedagogical Compilation (SGPC 2.0)**  
Autonomous Multimodal Video Studio for Transforming 16:9 Coding Lectures into High-Retention 9:16 Vertical Reels.

- **Live URL:** [https://ninad0109-snipshot.static.hf.space](https://ninad0109-snipshot.static.hf.space)
- **Space Hub:** [https://huggingface.co/spaces/Ninad0109/snipshot](https://huggingface.co/spaces/Ninad0109/snipshot)
- **GitHub Repository:** [https://github.com/Piyush-ops-ui/snipshot](https://github.com/Piyush-ops-ui/snipshot)

---

## 🌟 Key Features

1. **ScreenLex-ASR Grounding:** Real on-screen OCR text extracted via RapidOCR dynamically biases Whisper transcription, phonetically repairing programming jargon with verifiable video frame snapshot proofs.
2. **Delta 64×36 Slide-Skip Gate:** Perceptual frame-diff gate skips OCR on static slide plateaus ($< 2.0\\%$ diff), saving 40%–75% compute while scoping vocabulary to $\\pm 15$s.
3. **4-Signal Multimodal Candidate Scorer:** Evaluates candidate 30–55s windows using Vocal Energy + Visual Typing Diff + Grounded Tech Density + Sentence Closure with Deictic Penalty.
4. **Smart 1.35x Active-Window Zoom:** Centers on active editor/terminal typing with zero black pillar/letterbox bars.
5. **Mode B AI Explainer Compiler:** Compiles topics into 4 pedagogical beats with mathematical accuracy (NumPy Gradient Descent, Neural Nets, React Hooks, Docker vs VM) and synthesized voiceover.
6. **₹0.00 Cloud Tax:** Runs 100% on-device (Intel Core Ultra 5 125H + Intel Arc QSV) with zero SaaS subscriptions.
"""
(DEPLOY_DIR / "README.md").write_text(readme_content, encoding="utf-8")

# 4. Measure deployment size
total_size_mb = sum(f.stat().st_size for f in DEPLOY_DIR.rglob("*") if f.is_file()) / (1024 * 1024)
print(f"📊 Total deployment package size: {total_size_mb:.2f} MB")

# 5. Upload to Hugging Face Space
print(f"🚀 Uploading to Hugging Face Space: {REPO_ID}...")
api = HfApi(token=TOKEN)
commit_info = api.upload_folder(
    folder_path=str(DEPLOY_DIR),
    repo_id=REPO_ID,
    repo_type="space",
    commit_message="Deploy SnipShot Studio with sample lectures and reels",
)
print(f"✅ Deployment successful! Commit: {commit_info}")
print(f"🌐 Live Space URL: https://ninad0109-snipshot.static.hf.space")
print(f"🌐 Space Dashboard: https://huggingface.co/spaces/{REPO_ID}")
