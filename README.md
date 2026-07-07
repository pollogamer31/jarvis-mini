# 🤖 Jarvis Mini

A lightweight, fast, and fully customizable personal terminal assistant written in Python.

No cloud, no subscriptions: Jarvis Mini runs entirely on your local machine and even integrates an offline AI chatbot via **Ollama**.

> ⚠️ **macOS only.** Jarvis Mini uses a few macOS-specific system commands (`afplay`, `pmset`, `screencapture`) for sound alerts, battery status, and screenshots, plus a `.command` launcher file. It won't run properly on Windows or Linux without modifications.

## ✨ Features

- ⏱️ **Timer** — set quick timers straight from the command line
- 🍅 **Pomodoro** — study/work sessions with configurable cycles
- ✅ **To-do list** — manage your tasks without leaving the terminal
- 🎵 **Music recommendations** — suggestions based on mood or genre
- 🌍 **Translation** — translate text on the fly
- 🧠 **Local AI chat** — talk to an AI model locally via Ollama, no internet connection or paid API required

## 🚀 Installation

```bash
git clone https://github.com/pollogamer31/jarvis-mini.git
cd jarvis-mini
pip3 install rich deep-translator langdetect
```

For local AI chat, install [Ollama](https://ollama.com) and pull a model:

```bash
ollama pull llama3
```

## 🖥️ Usage

```bash
python jarvis.py
```

From there, you can use the available commands (timer, todo, pomodoro, chat, etc.) directly from the terminal menu.

## 🛠️ Built with

- Python 3
- Ollama (local AI)
- [`rich`](https://github.com/Textualize/rich) — terminal UI and formatting
- [`deep-translator`](https://github.com/nidhaloff/deep-translator) — translation
- [`langdetect`](https://github.com/Mimino666/langdetect) — automatic language detection

## 📌 Why Jarvis Mini?

Many "smart" assistants require accounts, subscriptions, or send your data to external servers. Jarvis Mini was built to be the opposite: a simple, fast tool that runs entirely on your own computer.

## 🤝 Contributing

Ideas, bug reports, or improvements are welcome! Feel free to open an issue or a pull request.

## 📄 License

MIT License — free to use, modify, and share.

---
*
Built by pollogamer31 as a Python and terminal automation experiment.
