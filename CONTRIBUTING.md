# Contributing to MacOS AI Agent

First off, thank you for considering contributing to **MacOS AI Agent**! It is contributions from developers like you that make open-source projects thrive.

---

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [License](#license)

---

## 📜 Code of Conduct
We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone. Please treat all contributors and maintainers with respect, courtesy, and constructive communication.

---

## 💡 How Can I Contribute?

### Reporting Bugs
Before creating bug reports, please check existing issues to ensure the problem has not already been reported. When creating an issue, please include:
- A clear, descriptive title.
- Steps to reproduce the behavior.
- Expected behavior vs. actual behavior.
- macOS version and Python version.
- Terminal logs or stack traces (redact any sensitive API keys).

### Suggesting Features
Feature requests are always welcome! When opening a feature request, please specify:
- The context and use case for the feature.
- Proposed command syntax or agent interaction style.
- Any macOS native dependencies or permissions required.

### Pull Requests
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/macos-ai-agent.git
   cd macos-ai-agent
   ```
3. Create a feature branch with a descriptive name:
   ```bash
   git checkout -b feat/add-new-automation
   ```
4. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add Apple Calendar event creation tool`
   - `fix: handle edge case in volume pattern matching`
   - `docs: update troubleshooting guide for permissions`
5. Push to your branch and submit a Pull Request to `main`.

---

## 🛠️ Development Setup

1. **Prerequisites:** macOS 12+ (Monterey or later), Python 3.10+.
2. **Setup virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY in .env
   ```
4. **Run syntax verification:**
   ```bash
   python3 -m py_compile tools.py desktop_tools.py main.py
   ```

---

## 📐 Coding Standards

- **Python Style:** Follow PEP 8 guidelines. Use type annotations (`str`, `list[str]`, `dict`) wherever applicable.
- **Safety First:** Never include hardcoded credentials, personal emails, or raw tokens in source code or examples.
- **Subprocess Discipline:** When executing AppleScript or bash commands, always handle exceptions gracefully with timeout limits and clear error messages.
- **Rich Terminal UI:** Maintain visual consistency using `rich` markup and theme colors.

---

## 📄 License

By contributing to **MacOS AI Agent**, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
