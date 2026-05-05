SYSTEM_RULES = """You are a practical AI nutrition assistant.
Be concise, realistic, supportive, and non-judgmental.
Do not act like a doctor and do not make diagnostic or medical claims.
Estimate calories and macros only approximately.
If the meal is unclear, prefer a short clarification question instead of guessing.
Return valid JSON only."""


MEAL_JSON_EXAMPLE = """{
  "recognized_food": "pizza",
  "confidence": 0.82,
  "estimated_portion_g": 320,
  "estimated_calories": 650,
  "estimated_protein_g": 22,
  "estimated_fat_g": 28,
  "estimated_carbs_g": 70,
  "suitability_status": "undesirable",
  "explanation": "This meal is fairly heavy for the user's goal because it is calorie-dense and easy to overeat.",
  "adjust_now": [
    "Keep the portion moderate",
    "Skip sugary drinks"
  ],
  "do_later": [
    "Make the next meal lighter",
    "Prioritize protein and vegetables later"
  ],
  "needs_clarification": false,
  "clarification_question": null
}"""


def onboarding_summary_prompt(profile_data: dict[str, str]) -> str:
    return f"""Create a short nutrition profile summary in 2 sentences.
Focus on the user's goal, activity, eating pattern, main difficulty, and restrictions.
Keep it practical and non-medical.

Profile data:
{profile_data}
"""


def text_meal_prompt(profile_summary: str, meal_text: str) -> str:
    return f"""Evaluate this meal for the user.
You MUST return ONLY valid JSON. No explanations, no markdown, no extra text.
Do not wrap JSON in code fences.

User profile summary:
{profile_summary}

Meal description:
{meal_text}

Return exactly this JSON structure with the same field names:
{MEAL_JSON_EXAMPLE}

If confidence is below roughly 0.6, set nutrition and evaluation fields to null where needed,
set needs_clarification to true, and ask one short clarification question.
If the meal is clear enough, set needs_clarification to false and fill all major fields.
"""


def image_meal_prompt(profile_summary: str) -> str:
    return f"""Analyze this food image for the user.
You MUST return ONLY valid JSON. No explanations, no markdown, no extra text.
Do not wrap JSON in code fences.

User profile summary:
{profile_summary}

Return exactly this JSON structure with the same field names:
{MEAL_JSON_EXAMPLE}

Identify the likely dish, visible ingredients, and approximate portion.
If the image is ambiguous, ask one short clarification question instead of pretending certainty.
If the image is reasonably clear, set needs_clarification to false and fill the analysis fields.
"""
