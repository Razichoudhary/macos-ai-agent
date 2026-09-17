# 🤖 MacOS AI Agent

> **An Autonomous Desktop Assistant & Real-Time Knowledge Retrieval Engine for macOS.**  
> Powered by **LangChain**, **Google Gemini 3.5 Flash**, **Pydantic**, and native **macOS Automation**.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/Orchestration-LangChain-1C3C3C.svg)](https://www.langchain.com/)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini%203.5%20Flash%20Lite-4285F4.svg)](https://aistudio.google.com/)
[![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)
[![Web UI](https://img.shields.io/badge/Web%20Dashboard-http%3A%2F%2Flocalhost%3A8000-00f0ff.svg)](#-web-dashboard--frontend-ui)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 Overview

**MacOS AI Agent** is a production-engineered AI assistant designed to bridge high-speed language model reasoning with real-world operating system execution. 

<p align="center">
  <img src="screenshots/screenshot_1_terminal_cli.png" alt="MacOS AI Agent Terminal Interface" width="850">
</p>

Unlike traditional chatbots that can only converse, **MacOS AI Agent** is an **Action Agent**: it reasons about user intent, decides the optimal course of action, queries live external tools (Wikipedia, DuckDuckGo web search), and directly automates macOS native applications, media players, system settings, desktop files, and emails.

---

## 🚀 Key Features

### 🎙️ 1. Hands-Free Continuous Voice Control
Speak commands completely hands-free via microphone without pressing any keys. Powered by `SpeechRecognition` and PortAudio/`pyaudio`, the engine continuously listens, waits for an exact **2-second speech pause** (`pause_threshold = 2.0`), transcribes via Google Web Speech, and executes commands instantly. Launch directly with `python main.py --voice` or type `voice` in the terminal.

### 🎵 2. Smart Music & YouTube Playback (Top Result + Random Fallback)
* **Specific Song/Artist:** Command *"play music Shape of You"* or *"play sunflower"* — automatically searches YouTube, extracts the **#1 top result**, and opens it directly in your browser.
* **Random Fallback:** Say *"play music"*, *"play any music"*, or *"play a song"* without naming a title — the agent automatically selects a hit from a curated global playlist and plays the top result immediately.
* **Instant Routing:** Bypasses LLM latency completely with sub-second direct playback.

### ⚡ 3. Sub-50ms Instant Direct Routing
Deterministic system actions (smooth volume up/down, battery status, screenshots, dark mode, screen lock, clipboard management, text-to-speech) bypass LLM API latency completely via a localized intent pattern router, executing natively in **under 50 milliseconds**.

### 🧠 4. Multi-Turn Conversational Memory
Maintains rolling context across multiple user requests. You can research a topic, ask follow-up questions, and command the agent: *"Now save that summary into a note file on my Desktop"*, or *"Email that research to my colleague"*.

### 🔍 5. Live Web Research & Structured Synthesis
Gathers up-to-date facts, current news, and scientific articles using DuckDuckGo search and Wikipedia. All research findings are strictly validated against a **Pydantic schema** (`ResearchResponse`) with resilient multi-tier JSON regex fallbacks to eliminate parsing failures.

### ✉️ 6. Automated Email Dispatch
* **Direct SMTP Transmission:** If configured with a Google App Password, transmits emails silently in the background in **0.2 seconds** via encrypted SSL (`smtp.gmail.com:465`).
* **Web Compose Auto-Send:** Opens the official Gmail Web Compose interface and automatically triggers DOM click / shortcuts to send without manual intervention.

### 🖥️ 7. Native macOS Desktop Control
* Open & close any desktop app (`open_app`, `close_app`).
* Distinguishes native apps from web services (e.g., native **Mail.app** vs. web **Gmail**, native **Notes.app** vs. **Google Keep**).
* Read and write files directly on the macOS Desktop.
* Native Apple Reminders integration (`create_reminder`).
* Media control for Apple Music and Spotify (play, pause, next, previous, now playing).


---

## 🏗️ System Architecture

```
                                  User Command / Query
                                           │
                                           ▼
                           ┌───────────────────────────────┐
                           │   Sub-50ms Direct Router      │
                           │   (Regex & Intent Classifier) │
                           └───────────────┬───────────────┘
                                           │
                  ┌────────────────────────┴────────────────────────┐
                  │ Match                                           │ No Match (Reasoning Required)
                  ▼                                                 ▼
     ┌────────────────────────┐                    ┌─────────────────────────────────┐
     │ Instant Native Tool    │                    │ Google Gemini 3.5 Flash Agent   │
     │ - Audio / Volume       │                    │ (LangChain Tool-Calling Engine) │
     │ - Dark Mode / Battery  │                    └────────────────┬────────────────┘
     │ - Lock / Screenshot    │                                     │
     └────────────┬───────────┘                                     ▼
                  │                                ┌─────────────────────────────────┐
                  │                                │ Autonomous Tool Selection       │
                  │                                │ ├── DuckDuckGo Web Search       │
                  │                                │ ├── Wikipedia API               │
                  │                                │ ├── YouTube Video Finder        │
                  │                                │ ├── Desktop App & File I/O      │
                  │                                │ └── Gmail Automated Dispatch    │
                  │                                └────────────────┬────────────────┘
                  │                                                 │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                           ┌───────────────────────────────┐
                           │   Pydantic Schema Validation  │
                           │   & Multi-Stage JSON Parser   │
                           └───────────────┬───────────────┘
                                           │
                                           ▼
                           ┌───────────────────────────────┐
                           │ Rich Styled Terminal UI       │
                           │ + Auto-Log to research_output │
                           └───────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core application logic |
| **LLM Engine** | Google Gemini 3.5 Flash Lite | High-speed, high-rate-limit autonomous reasoning |
| **Agent Framework** | LangChain Core / Classic | Tool-calling agent orchestration & scratchpad |
| **Data Validation** | Pydantic v2 | Strict schema enforcement and type validation |
| **Terminal UI** | Rich | Vibrant aesthetic formatting, panels, tables & spinners |
| **OS Automation** | macOS `subprocess` & AppleScript | Native hardware, application, and window control |
| **Information APIs** | DuckDuckGo Search, Wikipedia API | Real-time web retrieval |

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Razichoudhary/macos-ai-agent.git
cd macos-ai-agent
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your **Google Gemini API Key**:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

*(Optional: To enable 100% automated background email sending, add your Gmail address and a 16-character [Google App Password](https://myaccount.google.com/apppasswords)):*
```env
SENDER_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password
```

---

## 🌐 Web Dashboard & Frontend UI

The agent includes a production-grade **Cyber-Glassmorphism Web Dashboard** built with FastAPI and modern Vanilla CSS/JS. It features real-time macOS system telemetry, an interactive HUD, a smart music player dock, live tool execution logs, and browser-based hands-free voice controls.

### 🚀 Launching the Web Frontend:
```bash
# Option A: One-click launcher:
./start_web.sh

# Option B: Run directly with Python:
python server.py
```

### 🔗 Frontend Web Link:
Open your web browser at:  
👉 **[http://localhost:8000](http://localhost:8000)** *(or `http://127.0.0.1:8000`)*

---

## 🚦 Usage & Command Line Modes

You can also run the agent directly inside your terminal:

```bash
# 1. Text interactive mode:
python main.py

# 2. Hands-free continuous voice mode (no keypresses needed):
python main.py --voice
```
*(Inside text mode, you can also type `voice` anytime to switch into hands-free voice mode).*

### Example Commands:

#### 🎙️ Voice Commands (Hands-Free):
* *"open youtube"*
* *"play music"* *(plays a random top hit)*
* *"play music shape of you"* *(plays top YouTube search result)*
* *"volume up"* / *"volume down"*
* *"battery"* / *"take screenshot"* / *"dark mode"*
* *"send email to john@example.com with subject Hi saying Let's meet at 5"*


#### 🔍 Live Research:
* `What is quantum computing in simple terms?`
* `Who won the latest Nobel Prize in Physics?`
* `What is photosynthesis?`

#### 🎬 YouTube Playback:
* `open youtube apna college channel and in that the video python full course for beginner`
* `play lofi hip hop radio on youtube`

#### 🖥️ Desktop & App Control:
* `open calculator` / `close calculator`
* `open safari` / `close safari`
* `open gmail` *(opens Gmail web in browser)* vs `open mail` *(opens native Apple Mail)*
* `open youtube`

#### 📝 Notes & Files:
* `create a note on my Desktop called project_ideas.txt with the text AI Agent is running`
* `read file project_ideas.txt`

#### ⚡ Sub-50ms Quick Controls:
* `battery` *(shows percentage, charging state, and cycle count)*
* `screenshot` *(captures screen to Desktop)*
* `dark mode` *(toggles macOS dark/light appearance)*
* `volume 50%` / `mute` / `unmute`
* `specs` *(displays chip, memory, and disk space)*
* `say Welcome to MacOS AI Agent`

#### ✉️ Email Sending:
* `send an email to friend@example.com with subject Meeting Today saying Hey, let's catch up at 5 PM!`

---

## 🔒 Security & Privacy

* **Zero Hardcoded Secrets:** All credentials (`GEMINI_API_KEY`, email passwords) are stored exclusively in `.env`.
* **Git Safe:** The repository contains a strict `.gitignore` configured to ensure that `.env`, virtual environments, cache files, and private logs can never be accidentally committed to GitHub.
* **Non-Destructive:** File operations are restricted to non-destructive creation and reading; no arbitrary recursive deletion tools are provided.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.

---

## 👨‍💻 Author

Built with ❤️ by **Razi Chaudhary**
* 🐙 **GitHub:** [@Razichoudhary](https://github.com/Razichoudhary)
* 💼 **LinkedIn:** [Razi Chaudhary](https://www.linkedin.com/in/razi-chaudhary-ba946b324/)

Contributions, feature suggestions, and pull requests are welcome!

---

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**. Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development guidelines.

