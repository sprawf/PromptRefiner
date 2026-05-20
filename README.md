# ⚡ PromptRefiner

> Refine any text with AI — anywhere on Windows — in one hotkey.

Select text in **any app** → press **Alt + Shift + W** → the text is instantly replaced with an AI-polished version. Runs silently in the system tray. No subscriptions, no accounts, bring your own free API keys.

---

## Download

**[⬇ Download for Windows (v1.0.0)](https://github.com/sprawf/PromptRefiner/releases/latest)**

Unzip → run `PromptRefiner.exe`. Windows 10 / 11, no install required.

> First launch downloads the local AI model (~1 GB). Or add a free cloud key for instant sub-second responses.

---

## Free cloud API keys (optional — faster)

| Provider | Avg speed | Free tier | Get key |
|---|---|---|---|
| **Cerebras** | ~0.3 s | ✅ Yes | [cloud.cerebras.ai](https://cloud.cerebras.ai) → API Keys |
| **Groq** | ~1–3 s | ✅ Yes | [console.groq.com](https://console.groq.com) → API Keys |

Paste in: **System Tray icon → Settings → Providers**

---

## Features

- 🔥 **Global hotkey** — works in Word, browser, email, Notepad, Slack, anywhere
- 🤖 **Three AI backends** — Local (offline, private), Groq (70B), Cerebras (fastest)
- 📚 **Prompt library** — switch between prompt styles with one click (Alt + Shift + E)
- ✏️ **Custom prompts** — create, edit, colour-code your own refinement styles
- ⌨️ **Configurable hotkeys** — change shortcuts to anything you like
- 🔒 **Private** — local model never sends data anywhere; cloud keys stay on your machine
- 🔁 **Auto-fallback** — cloud providers automatically fall back to local on failure

---

## How it works

```
1. Select any text in any app
2. Press Alt + Shift + W
3. ⚡ pill appears while AI runs
4. Text is replaced in-place with the refined version
```

---

## Prompt Library

Press **Alt + Shift + E** (or tray → Prompt Library) to switch prompt styles:

| Action | How |
|---|---|
| Activate a prompt | Single click |
| Edit a prompt | Double click |
| Delete | ✕ button |
| Add new | ＋ Add button |

Included prompts: **Refine Prompt**, **System Prompt**, **Formalize**, **Simplify**, **Technical Depth**, **Expand**

---

## Hotkeys

| Action | Default |
|---|---|
| Refine selected text | `Alt + Shift + W` |
| Open Prompt Library | `Alt + Shift + E` |

Change in **Settings → General → Hotkeys → Record**

---

## Run from source

**Requirements:** Python 3.10+, Windows 10/11

```bash
git clone https://github.com/sprawf/PromptRefiner
cd PromptRefiner

# One-click setup (handles venv + GPU detection)
install.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# GPU-accelerated local AI (pick one):
# NVIDIA:
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
# AMD (Vulkan):
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/vulkan
# CPU fallback:
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

python main.py
```

---

## Build the exe yourself

```bash
pip install pyinstaller
pyinstaller PromptRefiner.spec
# Output: dist/PromptRefiner/PromptRefiner.exe
```

---

## Tech stack

| Layer | Technology |
|---|---|
| UI | CustomTkinter (dark, GPU-composited) |
| Local AI | llama-cpp-python + Qwen 2.5 1.5B GGUF (CUDA / Vulkan / CPU) |
| Cloud AI | Groq API, Cerebras API |
| Hotkeys | `keyboard` library (Windows low-level hook) |
| System tray | `pystray` |
| Packaging | PyInstaller (--onedir, UPX disabled) |

---

## Data & Privacy

- **Local mode**: text never leaves your machine
- **Cloud mode**: text is sent to Groq / Cerebras (both have privacy policies)
- Config + API keys stored in `%APPDATA%\PromptRefiner\config.json` — never in source
- Logs in `%APPDATA%\PromptRefiner\app.log` (auto-rotated, max 4 MB)
- No analytics, no telemetry, no accounts

---

## License

MIT — do whatever you want with it.
