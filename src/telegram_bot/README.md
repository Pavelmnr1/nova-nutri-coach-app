# AI Nutrition Assistant MVP

This repository contains a simple Telegram MVP bot that helps users make practical food decisions fast.

The bot:
- runs a short onboarding quiz
- stores a lightweight nutrition profile
- accepts meal text or food photos
- evaluates how the meal fits the user's goal
- gives practical advice instead of a raw calorie dump
- saves meals into a simple diary

## Project Structure

```text
src/app/
  __init__.py
  ai.py
  config.py
  db.py
  handlers.py
  main.py
  models.py
  prompts.py
  quiz.py
  services.py
  utils.py

tests/
  test_services.py
```

## What The Bot Does

Commands:
- `/start`
- `/profile`
- `/today`
- `/diary`
- `/help`

Main flow:
1. User runs `/start`
2. Bot completes a 7-question onboarding quiz
3. User sends meal text or a food photo
4. Bot analyzes the meal with the Gemini API
5. Bot replies with recognized food, suitability, explanation, and practical next steps
6. Meal is saved in SQLite

## Environment Variables

Create `.env` from `.env.example` and fill in:

- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_VISION_MODEL`
- `DATABASE_URL`
- `APP_HOST`
- `APP_PORT`
- `LOG_LEVEL`

## Local Setup

1. Create a virtual environment:

```powershell
python -m venv .venv
```

2. Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Copy the env file:

```powershell
Copy-Item .env.example .env
```

5. Fill in your Telegram bot token and Gemini API key in `.env`.

6. Run the Telegram bot:

```powershell
$env:PYTHONPATH="src"
python -m app.main
```

7. Optional health endpoint:

```powershell
$env:PYTHONPATH="src"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Running Tests

```powershell
$env:PYTHONPATH="src"
pytest
```

## Simple Architecture

- `main.py`: bot startup and optional FastAPI health app
- `config.py`: environment settings
- `handlers.py`: Telegram commands and message routing
- `quiz.py`: onboarding questions
- `ai.py`: Gemini API requests and structured response parsing
- `prompts.py`: reusable prompts
- `db.py`: SQLite engine and session setup
- `models.py`: SQLAlchemy models
- `services.py`: profile, conversation state, meal, and diary logic
- `utils.py`: small helpers

## Limitations

- Image analysis depends on the chosen Gemini model supporting image input.
- The bot retries invalid JSON once, then falls back to a friendly error message.
- Meal estimates are approximate and should not be treated as medical advice.
- `/today` uses UTC date boundaries for simplicity in this MVP.
- The daily summary uses lightweight heuristics instead of deep analytics.
