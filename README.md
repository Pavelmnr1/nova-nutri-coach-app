# Nutri Coach Nova

This repository is prepared as an ONIA submission package.

The main working version is the Telegram bot in [src/telegram_bot](/C:/Users/Welcome/Documents/nutri-coach-nova-main/src/telegram_bot). It helps a user complete onboarding, send food text or photos, and receive practical nutrition-oriented feedback.

The web part in [src/web_prototype](/C:/Users/Welcome/Documents/nutri-coach-nova-main/src/web_prototype) is a web interface prototype created with Lovable. It should be treated as a UI prototype and future web version concept, not as proof of a fully integrated production system.

The project uses external AI APIs transparently. This repository does not claim that the team trained its own large model.

## Repository Structure

```text
src/
  telegram_bot/
  web_prototype/
docs/
  architecture.md
  ethics_and_limitations.md
  product-spec.md
data/
  README.md
models/
  README.md
notebooks/
  README.md
tests/
README.md
.gitignore
.env.example
```

## Main Components

- `src/telegram_bot`: main Telegram bot code and its Python dependencies list.
- `src/web_prototype`: Lovable-based web interface prototype and frontend configuration.
- `docs/architecture.md`: honest system overview for submission.
- `docs/ethics_and_limitations.md`: safety, scope, and non-medical limitations.
- `tests/`: existing automated tests from the Telegram bot project.

## Running The Telegram Bot

1. Create a Python virtual environment.
2. Install dependencies from `src/telegram_bot/requirements.txt`.
3. Copy values from `.env.example` into a local `.env` file that is not committed.
4. Set `PYTHONPATH=src/telegram_bot/src`.
5. Start the bot with `python -m app.main`.

## Running The Web Prototype

1. Install frontend dependencies inside `src/web_prototype`.
2. Provide local environment variables if needed.
3. Run the existing frontend dev command from that folder.

## Honesty Notes For ONIA

- Telegram bot = main working AI version.
- Web app = additional web interface prototype.
- External AI API usage is explicit.
- No medical accuracy or doctor replacement claim is made.
- No claim is made that the web prototype is fully integrated with the Telegram bot unless such integration is demonstrated separately.
