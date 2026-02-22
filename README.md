# Basic Agentic AI Hardware (LED Controller)

A LangChain-based CLI agent that controls Raspberry Pi LEDs (`1` to `4`) using tool calls, keeps LED state in memory, and persists state to `output.json` for a live HTML dashboard.

## Features

- AI agent with tools:
  - `turn_on_led(led_number)`
  - `turn_off_led(led_number)`
  - `get_led_status()`
- In-memory LED state with thread lock for consistency
- Atomic JSON persistence to `output.json`
- Lightweight dashboard in `led_dashboard.html` that polls LED state

## Project Files

- `led_agent.py` — main AI agent and LED tools
- `led_dashboard.html` — LED status UI (inline CSS + JS)
- `serve_dashboard.py` — simple local HTTP server for dashboard (avoids `file://` CORS)
- `output.json` — persisted LED state

## Prerequisites

- Python 3.10+
- OpenAI API key

## Setup

1. Create/activate virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install langchain langchain-core langchain-openai python-dotenv
```

3. Create `.env` in project root:

```env
OPENAI_API_KEY=your_key_here
```

## Run Agent

```bash
python led_agent.py
```

Try prompts like:

- `Turn on led 1`
- `Turn off led 3`
- `What is led status?`

## Run Dashboard

Use HTTP mode (not `file://`):

```bash
python serve_dashboard.py
```

Then open:

- `http://127.0.0.1:8000/led_dashboard.html`

## Notes

- GPIO calls are currently left in code as commented placeholders.
- LED state memory is injected into each agent turn as context.
- `output.json` is updated atomically to reduce read/write conflicts with dashboard polling.
