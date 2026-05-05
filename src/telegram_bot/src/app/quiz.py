QUIZ_QUESTIONS = [
    {
        "key": "goal",
        "question": "What is your main goal?",
        "options": [
            "lose weight",
            "maintain weight",
            "eat healthier",
            "gain weight",
            "reduce unhealthy cravings",
        ],
    },
    {
        "key": "sex",
        "question": "What is your sex?",
        "options": ["male", "female", "prefer not to say"],
    },
    {
        "key": "age_group",
        "question": "What is your age group?",
        "options": ["under 18", "18-24", "25-34", "35-44", "45+"],
    },
    {
        "key": "activity_level",
        "question": "How active are you?",
        "options": ["low", "medium", "high"],
    },
    {
        "key": "eating_pattern",
        "question": "How would you describe your eating pattern?",
        "options": [
            "chaotic",
            "often overeat",
            "often undereat",
            "crave sweets/fast food",
            "relatively stable",
        ],
    },
    {
        "key": "main_difficulty",
        "question": "What is your biggest difficulty right now?",
        "options": [
            "I do not know what to eat",
            "calorie tracking is too annoying",
            "hard to stop eating",
            "no time to think about food",
            "evening cravings",
            "I cannot tell if food is good for me",
        ],
    },
    {
        "key": "dietary_restrictions",
        "question": (
            "Any restrictions or important notes? Reply with things like allergies, "
            "vegetarian, lactose-free, religious restrictions, medical notes, or 'none'."
        ),
        "options": None,
    },
]


def format_question(index: int) -> str:
    question = QUIZ_QUESTIONS[index]
    lines = [f"Question {index + 1}/{len(QUIZ_QUESTIONS)}", question["question"]]
    if question["options"]:
        lines.append("Options:")
        lines.extend(f"- {option}" for option in question["options"])
    return "\n".join(lines)
