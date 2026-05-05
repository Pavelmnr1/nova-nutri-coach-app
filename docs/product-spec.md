# Product Spec

## Product type
Telegram MVP bot for an AI nutrition assistant.

## Core value
The bot does not just count calories. It evaluates food in the context of the specific user.

## Tone
- friendly
- concise
- practical
- non-judgmental
- not medical

## User onboarding
The bot asks 10 onboarding questions and creates:
1. structured profile
2. AI summary profile

## Example profile fields
- goal
- dietary pattern
- allergies
- food restrictions
- disliked foods
- meal schedule
- snacking habits
- lifestyle notes
- self-reported issues
- motivation level

## Main input types
1. food photo
2. food text description

## Recognition logic
- detect food from image or text
- if confidence is low, ask 1–2 clarification questions
- then evaluate suitability for the user

## Output format
- recognized_food
- suitability_status
- short_explanation
- adjust_now
- do_later
- diary_confirmation

## Suitability statuses
- suitable
- conditionally_suitable
- undesirable
- not_suitable

## Diary entry structure
- timestamp
- input_type
- original_input
- recognized_food
- confidence
- clarification_answers
- suitability_status
- explanation
- adjust_now
- do_later

## Reminder support
The bot should allow storing reminder settings for future nudges.

## Important boundaries
- do not present the bot as a doctor
- do not make diagnostic claims
- keep the UX practical and supportive