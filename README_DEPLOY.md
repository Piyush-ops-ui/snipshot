# 🚀 Deploying SnipShot to Hugging Face Spaces (100% Free Docker Tier)

This guide walks you through deploying **SnipShot (Reel Studio)** to [Hugging Face Spaces](https://huggingface.co/spaces) using Docker. SnipShot runs completely on Hugging Face's **free 2 vCPU / 16GB RAM tier** with zero external API dependencies, zero cloud billing, and pre-bundled demo lectures for instant 1-click evaluation.

---

## 📋 Features in This Deployment

- **Single-Origin Production Serving**: FastAPI serves both the high-performance backend API routes (`/api/...`, `/outputs/...`, `/provenance/...`) and the compiled Vite React frontend SPA directly on port `7860`.
- **Zero Cold-Start Lag**: `faster-whisper` base & small models are pre-cached inside the container during build time so the app launches instantly.
- **Pre-Bundled Demo Clips**: 4 real lecture videos are pre-packaged in `/app/data/demo_clips/`, allowing judges and users to test the complete Screen-Grounded Pedagogical Compilation pipeline with **1 click** without uploading large files.
- **Full Hardware Portability**: Auto-detects available CPU/RAM resources and uses native FFmpeg + RapidOCR + faster-whisper int8 quantization.

---

## 🛠️ Step-by-Step Hugging Face Space Deployment

### Step 1: Create a New Space
1. Log in to [Hugging Face](https://huggingface.co).
2. In the top-right profile menu, click **New Space** (or visit [huggingface.co/new-space](https://huggingface.co/new-space)).
3. Fill in the Space settings:
   - **Space name**: `snipshot` (or your preferred name)
   - **License**: `mit` or `apache-2.0`
   - **Space SDK**: Select **Docker** 🐳
   - **Docker template**: Select **Blank**
   - **Space Hardware**: Choose **CPU basic • 2 vCPU • 16 GB • Free**
   - **Visibility**: Public (recommended for hackathon submission)

---

### Step 2: Set Up Hugging Face Access Token
If you haven't already set up a Hugging Face User Access Token on your machine:
1. Go to [Hugging Face Settings > Access Tokens](https://huggingface.co/settings/tokens).
2. Create a new token with **Write** permissions.
3. Save the token for git authentication.

---

### Step 3: Push Your Repository to Hugging Face Space

From your local SnipShot project directory, add the Hugging Face Space as a git remote and push:

```bash
# 1. Add your Hugging Face Space remote
git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/<YOUR_SPACE_NAME>

# 2. Ensure all changes and demo clips are committed
git add .
git commit -m "feat: bundle full-stack app, Dockerfile, and demo clips for Hugging Face Spaces"

# 3. Push to Hugging Face Space main branch
git push space main
```

*(When prompted for credentials: use your Hugging Face username and the User Access Token as your password).*

---

### Step 4: Automatic Build & Launch
1. Open your Space page on Hugging Face:
   `https://huggingface.co/spaces/<YOUR_HF_USERNAME>/<YOUR_SPACE_NAME>`
2. Watch the **Building** tab. Hugging Face Spaces will:
   - Build Stage 1 (Node.js builds Vite React frontend)
   - Build Stage 2 (Python installs FFmpeg, faster-whisper, RapidOCR, pre-caches models)
   - Launch FastAPI on port `7860`
3. Once the build completes, the status will show **Running**, and your interactive SnipShot Studio interface will appear live in the browser!

---

## ⚡ 1-Click Evaluation for Judges

When viewing the live Space:
1. Navigate to the **Mode A: Lecture Decompiler** tab.
2. Under the upload area, click any of the pre-loaded sample lecture buttons:
   - 🚗 **Java OOP: Objects & Classes** (`java_oop_car.mp4` • 9m 50s)
   - 🐍 **Python Programming Fundamentals** (`python_fundamentals.mp4` • 4m 00s)
   - 🐙 **Git & GitHub Desktop** (`github_desktop.mp4` • 11m 12s)
   - 🕹️ **Java Swing GUI Game** (`java_whacamole.mp4` • 32m 22s)
3. The engine will autonomously:
   - Scan for the highest-signal code-dense window
   - Run faster-whisper ASR with word-level timestamps
   - Run RapidOCR on lecture frames and confirm pixel-grounded code terms
   - Generate provenance snapshot crops
   - Render a vertical 1080x1920 MP4 reel with dynamic captions and code card in < 15 seconds!

---

## 💻 Optional: Testing the Docker Image Locally

You can test the exact container image on your local machine before pushing:

```bash
# 1. Build the Docker container image
docker build -t snipshot:latest .

# 2. Run container mapped to port 7860
docker run -p 7860:7860 snipshot:latest

# 3. Open in your web browser
# http://localhost:7860
```

---

## 🔍 Verification & Health Check

The container includes a built-in healthcheck endpoint:
```bash
curl http://localhost:7860/health
```
Response:
```json
{
  "status": "healthy",
  "app": "SnipShot (Reel Studio)",
  "version": "1.0.0",
  "hardware_profile": {
    "tier": "tier2_cpu_16gb",
    "cloud_cost_inr": 0.0,
    "privacy_status": "100% On-Device"
  }
}
```
