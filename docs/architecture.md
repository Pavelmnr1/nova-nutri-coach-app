# Architecture

## Overview

The repository contains two separate project parts:

1. `src/telegram_bot` contains the main working AI nutrition assistant implemented as a Telegram bot.
2. `src/web_prototype` contains a Lovable-created web interface prototype for a possible future web version.

They are stored in one submission repository for presentation purposes, but this package does not claim that both parts share one production backend or one fully integrated deployment pipeline.

## Telegram Bot

Path: [src/telegram_bot/src/app](src/telegram_bot/src/app)

Main responsibilities:

- onboarding flow and user profile capture
- message handling for text and food photos
- request preparation for external AI analysis
- result formatting and practical feedback
- local persistence for diary/profile data

Important files:

- `main.py`: startup entry point
- `handlers.py`: Telegram command and message handling
- `quiz.py`: onboarding questions and flow
- `ai.py`: calls to the external AI API
- `prompts.py`: prompt templates used by the bot
- `db.py`, `models.py`, `services.py`: storage and application services

## Web Interface Prototype

Path: [src/web_prototype](src/web_prototype)

This part is a UI prototype created with Lovable and related frontend tooling. It demonstrates a possible future web experience and should not be presented as the main working deployment of the project.

Observed prototype elements:

- route-based frontend structure
- UI screens for onboarding, logging, progress, and coaching
- Supabase-related integration files
- Lovable-related build configuration

## AI Usage

The submission uses external AI APIs transparently. The repository does not contain evidence of training a proprietary large model inside this codebase.

## Testing

Existing automated tests are located in [tests](tests) and cover a limited part of the Telegram bot service layer.
