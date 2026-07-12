# 🐳 Docker Inspector Agent

A local, privacy-friendly AI agent that lets you inspect your running Docker containers using plain English — powered by **[LangChain](https://www.langchain.com/)**, **[Ollama](https://ollama.com/)**, and the **Qwen2.5** model. Everything runs on your own machine; no API keys, no cloud calls, no data leaving your laptop.

```
You: how many containers are running right now?
Agent: You currently have 3 running containers: nginx, redis, and postgres-db.
```

---

## ✨ Features

- 🗣️ **Natural language interface** — ask about your containers instead of memorizing `docker` flags
- 📋 **List running or all containers** — including image, status, and exposed ports
- 📜 **Fetch container logs** — grab the last N lines from any container by name or ID
- 📊 **Live resource stats** — CPU % and memory usage for a running container
- 🔒 **Runs 100% locally** — uses Ollama for inference, no data sent to third-party APIs
- 🛠️ **Safe by design** — talks to Docker via the official `docker` Python SDK, not raw shell commands

---

## 🧱 Tech Stack

| Component | Purpose |
|---|---|
| [Ollama](https://ollama.com/) | Runs the Qwen2.5 model locally |
| [LangChain](https://www.langchain.com/) (`create_agent`) | Agent orchestration & tool-calling loop |
| [Docker SDK for Python](https://docker-py.readthedocs.io/) | Talks to the Docker Engine |

---

## 📋 Prerequisites

- Python 3.10+
- [Docker](https://docs.docker.com/get-docker/) installed and running
- [Ollama](https://ollama.com/download) installed

---

## 🚀 Setup

**1. Clone the repo**
```bash
git clone https://github.com/<your-username>/docker-inspector-agent.git
cd docker-inspector-agent
```

**2. Create a virtual environment and install dependencies**
```bash
python3 -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Pull a tool-calling-capable Qwen model**
```bash
ollama pull qwen2.5
```
> 💡 On an older or CPU-only machine, try a smaller/faster variant first to confirm everything works:
> ```bash
> ollama pull qwen2.5:1.5b
> ```

**4. Make sure Docker is accessible to your user**

On Linux, if you hit permission errors:
```bash
sudo usermod -aG docker $USER
# then log out and back in
```

---

## ▶️ Usage

```bash
python3 docker_agent.py
```

By default it uses the `qwen2.5` model. To use a different model:
```bash
python3 docker_agent.py qwen2.5:1.5b
```
or set it via an environment variable:
```bash
OLLAMA_MODEL=qwen2.5:1.5b python3 docker_agent.py
```

### Example prompts

```
You: what containers are running?
You: show me the last 20 log lines for nginx
You: how much CPU and memory is redis using?
You: are there any stopped containers?
```

While the agent is working, it prints each tool call it makes (e.g. `-> calling tool: list_running_containers({})`) so you can see what it's doing under the hood instead of staring at a blank screen.

---

## 📁 Project Structure

```
.
├── docker_agent.py      # Main agent + tool definitions
├── requirements.txt     # Python dependencies
├── .gitignore
└── README.md
```

---

## 🔧 How It Works

The agent is built with LangChain's `create_agent`, which wraps a local Ollama model in a tool-calling loop (via LangGraph under the hood). When you ask a question, the model decides whether it needs to call a tool — for example `list_running_containers` — inspects the result, and then responds in natural language.

```
User prompt
   │
   ▼
Qwen2.5 (via Ollama) ── decides which tool(s) to call
   │
   ▼
Docker SDK ── queries the local Docker Engine
   │
   ▼
Tool result fed back to the model
   │
   ▼
Final natural-language answer
```

---

## 🩹 Troubleshooting

| Problem | Fix |
|---|---|
| `ImportError: cannot import name 'create_tool_calling_agent'` | You're on LangChain 1.x, which uses the new `create_agent` API — make sure you're using the latest version of `docker_agent.py` in this repo. |
| `ollama._types.ResponseError: model 'qwen2.5' not found` | Run `ollama pull qwen2.5` (or whichever model you're passing in). |
| Agent seems to hang / no response | Large models are slow on CPU-only machines. Test with `ollama run qwen2.5 "hello"` directly, check `ollama ps`, or try a smaller model like `qwen2.5:1.5b`. |
| `Could not connect to Docker daemon` | Make sure Docker is running (`sudo systemctl start docker` on Linux) and your user has permission to access it. |

---

## 🗺️ Roadmap / Ideas

- [ ] Add a tool to start/stop/restart containers (with confirmation prompts)
- [ ] Add a `docker inspect`-style tool for full container config
- [ ] Support streaming token-by-token output in the CLI
- [ ] Optional web UI (Streamlit/Gradio) instead of terminal REPL

Contributions and suggestions welcome — feel free to open an issue or PR.

---

