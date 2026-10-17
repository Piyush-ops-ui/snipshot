import { ReelIR } from '../types/reel_ir';

export const SAMPLE_REEL: ReelIR = {
  schema_version: '1.0.0',
  reel_id: 'reel_py_async_001',
  mode: 'mode_a_extract',
  title: 'Python Async Context Managers & Resource Cleanup',
  source_media_path: '/samples/python_apnacollege.mp4',
  clip_start: 114.2,
  clip_end: 154.8,
  total_duration: 40.6,
  audio_path: '/audio/python_async_clean.wav',
  pedagogical_score: 9.6,
  error_resolved_at: 23.4,
  entry_closure_verified: true,
  exit_closure_verified: true,
  technical_term_count: 5,
  created_at: new Date().toISOString(),
  typing_hyperlapse_intervals: [[14.0, 18.5]],
  template_archetype: 'bug_hunter',
  brand_kit: {
    id: 'brand_perpetual_cyan',
    name: 'SnipShot Obsidian Cyan',
    primary_color: '#00F2FE',
    secondary_color: '#4FACFE',
    background_color: '#0B0F17',
    text_color: '#F8FAFC',
    font_family: 'JetBrains Mono',
    font_size_pt: 32,
    logo_position: 'top_right',
    show_provenance_badge: true,
    enable_intro_bumper: false,
    intro_bumper_duration: 1.5,
    enable_outro_bumper: true,
    outro_bumper_duration: 2.0,
    watermark_text: 'SnipShot Perpetual Studio',
  },
  redaction_boxes: [],
  viewports: [],
  code_cards: [],
  transcript: [],
  growth_pack: {
    hook_title: 'Prevent Database Connection Leaks with Async Context Managers ⚡',
    broad_hashtags: ['#coding', '#programming', '#softwareengineering', '#backend'],
    stack_hashtags: ['#python', '#fastapi', '#sqlalchemy', '#asyncio'],
    micro_api_hashtags: ['#contextmanager', '#asyncwith', '#connectionpool', '#dboptimization'],
    pinned_code_comment: `⚡ Always use an async context manager to ensure database connections are released immediately back to the pool:

\`\`\`python
async with get_db_session() as session:
    result = await session.execute(query)
    return result.scalars().all()
\`\`\`

Full production test suite and architectural cheat sheet linked in bio! 🚀`,
    qr_code_data: 'https://github.com/snipshot/clean-architecture-guide',
  },
};

export const SAMPLE_LECTURE_PREVIEWS: Record<string, any> = {
  "apnacollege_python": {
    "clip_id": "reel_apnacollege",
    "title": "ApnaCollege Python (FirstProgram.py)",
    "video_url": "/outputs/reel_apnacollege.mp4",
    "source_video_path": "/samples/python_apnacollege.mp4",
    "source_video_url": "/samples/python_apnacollege.mp4",
    "start_sec": 12.0,
    "end_sec": 46.5,
    "duration": 34.5,
    "transcript": "Now let us write our first program. We take user input for old age, convert it into an integer, add two to it, and print the new age.",
    "code_snippet": "old_age = input(\"enter your old age : \")\nnew_age = int(old_age) + 2\nprint(new_age)",
    "hashtags": [
      "#python",
      "#pythontutorial",
      "#typecasting",
      "#programming",
      "#coding"
    ],
    "vocal_energy_score": 91.5,
    "screen_activity_score": 94.0,
    "bug2fix_detected": false,
    "key_teaching_moment": true,
    "typing_hyperlapse_sec": 2.8,
    "repaired_terms": [
      {
        "id": "crop_1",
        "raw_asr": "olt aj",
        "repaired_term": "old_age",
        "confidence": 0.98,
        "thumbnail": "/provenance/crop_2b6116.png",
        "timestamp": 14.2
      },
      {
        "id": "crop_2",
        "raw_asr": "int olt aj",
        "repaired_term": "int(old_age)",
        "confidence": 0.97,
        "thumbnail": "/provenance/crop_26d110.png",
        "timestamp": 22.8
      },
      {
        "id": "crop_3",
        "raw_asr": "print niw aj",
        "repaired_term": "print(new_age)",
        "confidence": 0.99,
        "thumbnail": "/provenance/crop_58bdaf.png",
        "timestamp": 31.4
      },
      {
        "id": "crop_4",
        "raw_asr": "first progrm",
        "repaired_term": "FirstProgram.py",
        "confidence": 0.95,
        "thumbnail": "/provenance/crop_15058d.png",
        "timestamp": 8.0
      }
    ],
    "growth_pack": {
      "hook_title": "Master Python Variables & Type Casting in 35s! \ud83d\ude80",
      "broad_hashtags": [
        "#coding",
        "#programming",
        "#python3"
      ],
      "stack_hashtags": [
        "#python",
        "#pythontutorial",
        "#learnpython"
      ],
      "micro_api_hashtags": [
        "#input",
        "#int",
        "#typecasting"
      ],
      "pinned_code_comment": "\u26a1 Verified Python Snippet from ApnaCollege:\n\n```python\nold_age = input(\"enter your old age : \")\nnew_age = int(old_age) + 2\nprint(new_age)\n```\n\nScan QR code or visit https://snipshot.studio to download.",
      "qr_code_data": "https://snipshot.studio/c/apnacollege_python"
    },
    "ocr_telemetry": {
      "compute_saved_pct": 41.7,
      "unique_screen_states_ocrd": 14,
      "total_frames_scanned": 24,
      "static_frames_skipped": 10,
      "total_score": 94.2,
      "vocal_score": 91.5,
      "visual_diff_score": 94.0,
      "tech_ocr_score": 96.0,
      "closure_score": 98.0,
      "vocab_fixes_count": 4,
      "render_time_seconds": 3.2,
      "resolution": "1080x1920 (9:16)",
      "duration_seconds": 34.5,
      "audio_spec": "16kHz Mono H.264/AAC"
    },
    "candidate_highlights": [
      {
        "rank": 1,
        "start_sec": 12.0,
        "end_sec": 46.5,
        "total_score": 94.2,
        "vocal_score": 91.5,
        "visual_diff_score": 94.0,
        "tech_density_score": 96.0,
        "closure_score": 98.0,
        "why_selected": "Optimal balance of instructor voice clarity, active code typing, and complete sentence closure."
      },
      {
        "rank": 2,
        "start_sec": 65.0,
        "end_sec": 98.0,
        "total_score": 84.6,
        "vocal_score": 82.0,
        "visual_diff_score": 79.0,
        "tech_density_score": 88.0,
        "closure_score": 91.0,
        "why_selected": "Good technical density but contains partial slide transition."
      },
      {
        "rank": 3,
        "start_sec": 110.0,
        "end_sec": 142.0,
        "total_score": 78.1,
        "vocal_score": 76.0,
        "visual_diff_score": 71.0,
        "tech_density_score": 83.0,
        "closure_score": 85.0,
        "why_selected": "Lower visual typing activity plateau."
      }
    ]
  },
  "java_whacamole": {
    "clip_id": "reel_whacamole",
    "title": "Java Swing GUI (WhacAMole.java)",
    "video_url": "/outputs/reel_whacamole.mp4",
    "source_video_path": "/samples/java_whacamole.mp4",
    "source_video_url": "/samples/java_whacamole.mp4",
    "start_sec": 25.0,
    "end_sec": 58.0,
    "duration": 33.0,
    "transcript": "Now we iterate through nine tiles using a for loop. Each JButton is created, stored in the array, added to the board panel, and wired to the action listener.",
    "code_snippet": "for (int i = 0; i < 9; i++) {\n    JButton tile = new JButton();\n    board[i] = tile;\n    boardPanel.add(tile);\n    tile.setFocusable(false);\n    tile.addActionListener(this);\n}",
    "hashtags": [
      "#java",
      "#javaswing",
      "#whacamole",
      "#gui",
      "#programming"
    ],
    "vocal_energy_score": 89.2,
    "screen_activity_score": 96.5,
    "bug2fix_detected": true,
    "key_teaching_moment": true,
    "typing_hyperlapse_sec": 3.4,
    "repaired_terms": [
      {
        "id": "crop_w1",
        "raw_asr": "bord penal",
        "repaired_term": "boardPanel.add(tile)",
        "confidence": 0.98,
        "thumbnail": "/provenance/crop_fa334a.png",
        "timestamp": 28.0
      },
      {
        "id": "crop_w2",
        "raw_asr": "je batan",
        "repaired_term": "JButton tile",
        "confidence": 0.96,
        "thumbnail": "/provenance/crop_3ebc2d.png",
        "timestamp": 34.5
      },
      {
        "id": "crop_w3",
        "raw_asr": "akshan lisnar",
        "repaired_term": "ActionListener",
        "confidence": 0.99,
        "thumbnail": "/provenance/crop_941e4b.png",
        "timestamp": 45.1
      }
    ],
    "growth_pack": {
      "hook_title": "Build a Java Swing Game in 33 Seconds! \ud83c\udfae",
      "broad_hashtags": [
        "#java",
        "#programming",
        "#gamedev"
      ],
      "stack_hashtags": [
        "#javaswing",
        "#gui",
        "#desktopapps"
      ],
      "micro_api_hashtags": [
        "#jbutton",
        "#actionlistener",
        "#layoutmanager"
      ],
      "pinned_code_comment": "\u26a1 Verified Java Swing Grid Loop:\n\n```java\nfor (int i = 0; i < 9; i++) {\n    JButton tile = new JButton();\n    board[i] = tile;\n    boardPanel.add(tile);\n    tile.setFocusable(false);\n    tile.addActionListener(this);\n}\n```\n\nScan QR code or visit https://snipshot.studio to download.",
      "qr_code_data": "https://snipshot.studio/c/java_whacamole"
    },
    "ocr_telemetry": {
      "compute_saved_pct": 46.7,
      "unique_screen_states_ocrd": 16,
      "total_frames_scanned": 30,
      "static_frames_skipped": 14,
      "total_score": 96.8,
      "vocal_score": 89.2,
      "visual_diff_score": 96.5,
      "tech_ocr_score": 98.0,
      "closure_score": 97.0,
      "vocab_fixes_count": 3,
      "render_time_seconds": 3.6,
      "resolution": "1080x1920 (9:16)",
      "duration_seconds": 33.0,
      "audio_spec": "16kHz Mono H.264/AAC"
    },
    "candidate_highlights": [
      {
        "rank": 1,
        "start_sec": 25.0,
        "end_sec": 58.0,
        "total_score": 96.8,
        "vocal_score": 89.2,
        "visual_diff_score": 96.5,
        "tech_density_score": 98.0,
        "closure_score": 97.0,
        "why_selected": "Real-time UI component instantiation with high typing activity."
      },
      {
        "rank": 2,
        "start_sec": 80.0,
        "end_sec": 114.0,
        "total_score": 88.3,
        "vocal_score": 85.0,
        "visual_diff_score": 84.0,
        "tech_density_score": 91.0,
        "closure_score": 93.0,
        "why_selected": "Good event handler explanation."
      },
      {
        "rank": 3,
        "start_sec": 140.0,
        "end_sec": 172.0,
        "total_score": 81.0,
        "vocal_score": 79.0,
        "visual_diff_score": 75.0,
        "tech_density_score": 86.0,
        "closure_score": 88.0,
        "why_selected": "Minor deictic reference in opening."
      }
    ]
  },
  "java_oop_car": {
    "clip_id": "reel_javaoop",
    "title": "Java OOP (Main.java & Car.java)",
    "video_url": "/outputs/reel_javaoop.mp4",
    "source_video_path": "/samples/java_oop_car.mp4",
    "source_video_url": "/samples/java_oop_car.mp4",
    "start_sec": 24.0,
    "end_sec": 53.0,
    "duration": 29.0,
    "transcript": "An object is an entity that holds data as attributes and can perform actions through methods. Here in our main class, we instantiate our Car object.",
    "code_snippet": "public class Main {\n    public static void main(String[] args) {\n        Car myCar = new Car(\"Tesla\", 2024);\n        myCar.startEngine();\n    }\n}",
    "hashtags": [
      "#java",
      "#javaoop",
      "#objectoriented",
      "#coding",
      "#softwareengineering"
    ],
    "vocal_energy_score": 87.4,
    "screen_activity_score": 88.0,
    "bug2fix_detected": false,
    "key_teaching_moment": true,
    "typing_hyperlapse_sec": 1.9,
    "repaired_terms": [
      {
        "id": "crop_c1",
        "raw_asr": "methods",
        "repaired_term": "(methods)",
        "confidence": 0.94,
        "thumbnail": "/provenance/crop_cf1c4f.png",
        "timestamp": 28.0
      },
      {
        "id": "crop_c2",
        "raw_asr": "kar",
        "repaired_term": "Car.java",
        "confidence": 0.96,
        "thumbnail": "/provenance/crop_def4ee.png",
        "timestamp": 34.0
      },
      {
        "id": "crop_c3",
        "raw_asr": "my project",
        "repaired_term": "MyFirstProject",
        "confidence": 0.97,
        "thumbnail": "/provenance/crop_1faf29.png",
        "timestamp": 42.0
      }
    ],
    "growth_pack": {
      "hook_title": "Master Java OOP Architecture in 29 Seconds! \u2615",
      "broad_hashtags": [
        "#java",
        "#programming",
        "#computerscience"
      ],
      "stack_hashtags": [
        "#oop",
        "#classes",
        "#softwaredevelopment"
      ],
      "micro_api_hashtags": [
        "#constructor",
        "#instantiation",
        "#methods"
      ],
      "pinned_code_comment": "\u26a1 Verified Java OOP Object Scaffold:\n\n```java\npublic class Main {\n    public static void main(String[] args) {\n        Car myCar = new Car(\"Tesla\", 2024);\n        myCar.startEngine();\n    }\n}\n```\n\nScan QR code or visit https://snipshot.studio to download.",
      "qr_code_data": "https://snipshot.studio/c/java_oop_car"
    },
    "ocr_telemetry": {
      "compute_saved_pct": 75.0,
      "unique_screen_states_ocrd": 1,
      "total_frames_scanned": 4,
      "static_frames_skipped": 3,
      "total_score": 91.4,
      "vocal_score": 87.4,
      "visual_diff_score": 88.0,
      "tech_ocr_score": 95.0,
      "closure_score": 95.0,
      "vocab_fixes_count": 3,
      "render_time_seconds": 2.7,
      "resolution": "1080x1920 (9:16)",
      "duration_seconds": 29.0,
      "audio_spec": "16kHz Mono H.264/AAC"
    },
    "candidate_highlights": [
      {
        "rank": 1,
        "start_sec": 24.0,
        "end_sec": 53.0,
        "total_score": 91.4,
        "vocal_score": 87.4,
        "visual_diff_score": 88.0,
        "tech_density_score": 95.0,
        "closure_score": 95.0,
        "why_selected": "75% static frames skipped via Delta Gate with concise object explanation."
      },
      {
        "rank": 2,
        "start_sec": 75.0,
        "end_sec": 106.0,
        "total_score": 83.2,
        "vocal_score": 81.0,
        "visual_diff_score": 80.0,
        "tech_density_score": 87.0,
        "closure_score": 89.0,
        "why_selected": "Method definition segment."
      },
      {
        "rank": 3,
        "start_sec": 120.0,
        "end_sec": 150.0,
        "total_score": 77.5,
        "vocal_score": 75.0,
        "visual_diff_score": 72.0,
        "tech_density_score": 81.0,
        "closure_score": 84.0,
        "why_selected": "Introductory slide plateau."
      }
    ]
  },
  "github_desktop": {
    "clip_id": "reel_github",
    "title": "GitHub Desktop & Terminal",
    "video_url": "/outputs/reel_github.mp4",
    "source_video_path": "/samples/github_desktop.mp4",
    "source_video_url": "/samples/github_desktop.mp4",
    "start_sec": 31.0,
    "end_sec": 60.0,
    "duration": 29.0,
    "transcript": "First download GitHub Desktop, create your repository, open it inside VS Code with code dot, and push your initial commit to origin.",
    "code_snippet": "# Workflow: GitHub Desktop & Terminal\n1. Create & Clone 'sample-repo'\n2. Open in VS Code:\n   $ cd sample-repo\n   $ code .\n3. Create Web Entrypoint:\n   $ touch index.html",
    "hashtags": [
      "#git",
      "#githubdesktop",
      "#terminal",
      "#versioncontrol",
      "#developer"
    ],
    "vocal_energy_score": 86.8,
    "screen_activity_score": 91.2,
    "bug2fix_detected": false,
    "key_teaching_moment": true,
    "typing_hyperlapse_sec": 3.1,
    "repaired_terms": [
      {
        "id": "crop_g1",
        "raw_asr": "gethaph",
        "repaired_term": "GitHub Desktop",
        "confidence": 0.98,
        "thumbnail": "/provenance/crop_8a91c5.png",
        "timestamp": 33.0
      },
      {
        "id": "crop_g2",
        "raw_asr": "samapl ripo",
        "repaired_term": "sample-repo",
        "confidence": 0.96,
        "thumbnail": "/provenance/crop_3c4861.png",
        "timestamp": 41.5
      },
      {
        "id": "crop_g3",
        "raw_asr": "viyas kod",
        "repaired_term": "VS Code",
        "confidence": 0.99,
        "thumbnail": "/provenance/crop_c648bf.png",
        "timestamp": 52.0
      }
    ],
    "growth_pack": {
      "hook_title": "Setup Git & VS Code in 29 Seconds! \ud83d\udc19",
      "broad_hashtags": [
        "#git",
        "#github",
        "#coding"
      ],
      "stack_hashtags": [
        "#versioncontrol",
        "#vscode",
        "#terminal"
      ],
      "micro_api_hashtags": [
        "#gitinit",
        "#gitpush",
        "#githubdesktop"
      ],
      "pinned_code_comment": "\u26a1 Verified Git Workflow Steps:\n\n```bash\n# 1. Create & Clone repo\n$ git clone https://github.com/user/sample-repo.git\n\n# 2. Open in VS Code\n$ cd sample-repo && code .\n\n# 3. Create entrypoint\n$ touch index.html\n```\n\nScan QR code or visit https://snipshot.studio to download.",
      "qr_code_data": "https://snipshot.studio/c/github_desktop"
    },
    "ocr_telemetry": {
      "compute_saved_pct": 33.3,
      "unique_screen_states_ocrd": 4,
      "total_frames_scanned": 6,
      "static_frames_skipped": 2,
      "total_score": 93.1,
      "vocal_score": 86.8,
      "visual_diff_score": 91.2,
      "tech_ocr_score": 96.0,
      "closure_score": 95.0,
      "vocab_fixes_count": 3,
      "render_time_seconds": 3.1,
      "resolution": "1080x1920 (9:16)",
      "duration_seconds": 29.0,
      "audio_spec": "16kHz Mono H.264/AAC"
    },
    "candidate_highlights": [
      {
        "rank": 1,
        "start_sec": 31.0,
        "end_sec": 60.0,
        "total_score": 93.1,
        "vocal_score": 86.8,
        "visual_diff_score": 91.2,
        "tech_density_score": 96.0,
        "closure_score": 95.0,
        "why_selected": "Fastest setup sequence from GUI install to VS Code CLI."
      },
      {
        "rank": 2,
        "start_sec": 85.0,
        "end_sec": 118.0,
        "total_score": 85.4,
        "vocal_score": 82.0,
        "visual_diff_score": 83.0,
        "tech_density_score": 89.0,
        "closure_score": 90.0,
        "why_selected": "Branch creation segment."
      },
      {
        "rank": 3,
        "start_sec": 140.0,
        "end_sec": 169.0,
        "total_score": 79.2,
        "vocal_score": 77.0,
        "visual_diff_score": 74.0,
        "tech_density_score": 82.0,
        "closure_score": 86.0,
        "why_selected": "Commit history view."
      }
    ]
  }
};

export const SAMPLE_EXPLAINER_PREVIEWS: Record<string, any> = {
  "gradient_descent": {
    "video_url": "/outputs/explainer_gradient_descent.mp4",
    "duration": 42.0,
    "scenes": [
      {
        "title": "Hook: Optimization Objective",
        "narration_text": "Gradient descent is the optimization engine powering linear regression and deep learning.",
        "code_snippet": "# Minimize Mean Squared Error (MSE)\nloss = (1 / (2 * N)) * np.sum((y_pred - y) ** 2)",
        "language": "python"
      },
      {
        "title": "Core Concept: Forward Prediction",
        "narration_text": "We compute the dot product between our input feature matrix X and model weights w, then add the bias b.",
        "code_snippet": "y_pred = np.dot(X, w) + b",
        "language": "python"
      },
      {
        "title": "Mutation: Analytical Gradient",
        "narration_text": "Next we compute the partial derivative dw across all training samples N.",
        "code_snippet": "error = y_pred - y\ndw = (1 / N) * np.dot(X.T, error)\ndb = (1 / N) * np.sum(error)",
        "language": "python"
      },
      {
        "title": "Verification: Parameter Step",
        "narration_text": "Finally, we update weights in the opposite direction of the gradient scaled by our learning rate.",
        "code_snippet": "w -= learning_rate * dw\nb -= learning_rate * db\nprint(f\"Updated loss: {loss:.4f}\")",
        "language": "python"
      }
    ],
    "hashtags": [
      "#machinelearning",
      "#gradientdescent",
      "#linearregression",
      "#datascience",
      "#numpy",
      "#math"
    ]
  },
  "react_hooks": {
    "video_url": "/outputs/explainer_react_hooks.mp4",
    "duration": 40.0,
    "scenes": [
      {
        "title": "Hook: State vs Lifecycle",
        "narration_text": "React useState manages local component state, while useEffect coordinates side effects.",
        "code_snippet": "const [count, setCount] = useState(0);",
        "language": "javascript"
      },
      {
        "title": "Core Concept: State Trigger",
        "narration_text": "Calling setCount schedules a re-render with the latest state value.",
        "code_snippet": "const increment = () => setCount(prev => prev + 1);",
        "language": "javascript"
      },
      {
        "title": "Mutation: Effect Synchronization",
        "narration_text": "useEffect runs after painting to synchronize with external APIs or subscriptions.",
        "code_snippet": "useEffect(() => {\n  document.title = `Count: ${count}`;\n}, [count]);",
        "language": "javascript"
      },
      {
        "title": "Verification: Cleanup Guard",
        "narration_text": "Always return a cleanup callback to avoid memory leaks when components unmount.",
        "code_snippet": "useEffect(() => {\n  const id = setInterval(tick, 1000);\n  return () => clearInterval(id);\n}, []);",
        "language": "javascript"
      }
    ],
    "hashtags": [
      "#reactjs",
      "#javascript",
      "#webdev",
      "#frontend",
      "#hooks"
    ]
  },
  "docker_vm": {
    "video_url": "/outputs/explainer_docker_vm.mp4",
    "duration": 38.0,
    "scenes": [
      {
        "title": "Hook: Container vs Hypervisor",
        "narration_text": "Virtual machines virtualize hardware, whereas Docker containers share the host Linux kernel.",
        "code_snippet": "# Dockerfile: Lightweight container\nFROM node:20-alpine",
        "language": "dockerfile"
      },
      {
        "title": "Core Concept: Isolation via Namespaces",
        "narration_text": "Containers isolate processes using Linux cgroups and namespaces with zero hypervisor overhead.",
        "code_snippet": "WORKDIR /app\nCOPY package*.json ./\nRUN npm ci --only=production",
        "language": "dockerfile"
      },
      {
        "title": "Mutation: Multi-Stage Efficiency",
        "narration_text": "Multi-stage builds eliminate compiler toolchains from production images.",
        "code_snippet": "COPY --from=builder /app/dist ./dist\nEXPOSE 3000\nCMD [\"node\", \"dist/index.js\"]",
        "language": "dockerfile"
      },
      {
        "title": "Verification: Instant Startup",
        "narration_text": "Containers launch in milliseconds with orders of magnitude lower memory footprint.",
        "code_snippet": "$ docker build -t my-app .\n$ docker run -p 3000:3000 my-app",
        "language": "bash"
      }
    ],
    "hashtags": [
      "#docker",
      "#devops",
      "#containers",
      "#cloud",
      "#infrastructure"
    ]
  },
  "json_xml": {
    "video_url": "/outputs/explainer_json_xml.mp4",
    "duration": 36.0,
    "scenes": [
      {
        "title": "Hook: Modern Payload Formats",
        "narration_text": "JSON provides clean key-value syntax, while XML supports schema validation and namespaces.",
        "code_snippet": "{\n  \"status\": 200,\n  \"user\": \"alex_dev\",\n  \"active\": true\n}",
        "language": "json"
      },
      {
        "title": "Core Concept: XML Schema Rigor",
        "narration_text": "XML enforces structural contracts with XSD schemas and custom tag hierarchies.",
        "code_snippet": "<user id=\"101\">\n  <name>Alex</name>\n  <role>Engineer</role>\n</user>",
        "language": "xml"
      },
      {
        "title": "Mutation: Network Efficiency",
        "narration_text": "JSON has 40% lower serialization overhead and maps natively to JavaScript objects.",
        "code_snippet": "const user = JSON.parse(responsePayload);\nconsole.log(user.name);",
        "language": "javascript"
      },
      {
        "title": "Verification: Fast Parsing",
        "narration_text": "Modern V8 engines parse JSON at gigabytes per second directly in native C++.",
        "code_snippet": "const payload = JSON.stringify({ ok: true });",
        "language": "javascript"
      }
    ],
    "hashtags": [
      "#json",
      "#xml",
      "#webapis",
      "#backend",
      "#architecture"
    ]
  }
};
