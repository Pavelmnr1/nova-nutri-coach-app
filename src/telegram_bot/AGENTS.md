# AGENTS.md

## Project
Build an MVP Telegram bot for an AI nutrition assistant.

## Goal
Create a practical, modular MVP with clean architecture, easy local setup, and minimal manual fixes.

## Tech stack
- Python 3.11
- FastAPI
- Telegram Bot API
- SQLite by default for MVP
- SQLAlchemy
- Pydantic settings via environment variables
- OpenRouter for LLM provider
- OpenRouter multimodal when available for image understanding
- Hugging Face fallback for image analysis

## Product behavior
- Friendly, concise, non-judgmental tone
- Practical nutrition assistant, not just a calorie tracker
- Never pretend to be a doctor
- Use calories/macros internally, but not as the main UX
- If food recognition confidence is low, ask 1–2 clarification questions

## Commands
/start
/profile
/today
/diary
/reminders
/help

## Architecture requirements
Use provider abstraction so LLM and image analysis providers can be swapped via environment variables.

Expected modules:
- app/main.py
- app/config.py
- app/db/
- app/models/
- app/schemas/
- app/services/
- app/providers/llm/
- app/providers/vision/
- app/bot/
- app/api/
- tests/

## Defaults
- Use SQLite by default
- Include .env.example
- Include requirements.txt
- Include README with setup instructions
- Prefer simple local startup
- Prefer long polling for Telegram MVP unless another approach is clearly simpler

## Quality bar
- Code must run locally
- Avoid placeholders unless clearly marked
- Add basic tests for core business logic
- Add defensive error handling
- Keep code modular and readable
- Return structured responses for food analysis

## Output expectations
When coding, also:
1. explain final architecture briefly
2. list all created files
3. provide exact run commands
4. mention any limitations honestly
