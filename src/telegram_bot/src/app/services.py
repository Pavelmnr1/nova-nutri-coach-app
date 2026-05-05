from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ConversationState, MealEntry, User, UserProfile
from app.quiz import QUIZ_QUESTIONS
from app.utils import dumps_json, extract_clean_summary_text, loads_json, normalize_whitespace


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_user(
        self, telegram_user_id: int, username: str | None, first_name: str | None
    ) -> User:
        user = self.session.scalar(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        if user is None:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
            )
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user

        user.username = username
        user.first_name = first_name
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_profile(self, user_id: int) -> UserProfile | None:
        return self.session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))


class ConversationService:
    def __init__(self, session: Session):
        self.session = session

    def get_state(self, user_id: int) -> ConversationState | None:
        return self.session.scalar(
            select(ConversationState).where(ConversationState.user_id == user_id)
        )

    def set_state(self, user_id: int, state_type: str, payload: dict[str, Any]) -> ConversationState:
        state = self.get_state(user_id)
        if state is None:
            state = ConversationState(user_id=user_id, state_type=state_type, state_payload="{}")
            self.session.add(state)

        state.state_type = state_type
        state.state_payload = dumps_json(payload)
        state.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(state)
        return state

    def clear_state(self, user_id: int) -> None:
        state = self.get_state(user_id)
        if state is not None:
            self.session.delete(state)
            self.session.commit()

    def get_payload(self, user_id: int) -> dict[str, Any]:
        state = self.get_state(user_id)
        return loads_json(state.state_payload) if state else {}


class ProfileService:
    def __init__(self, session: Session):
        self.session = session

    def save_onboarding_answers(self, user_id: int, answers: dict[str, str], ai_summary: str) -> UserProfile:
        profile = self.session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self.session.add(profile)

        profile.goal = answers["goal"]
        profile.age_group = answers["age_group"]
        profile.sex = answers["sex"]
        profile.activity_level = answers["activity_level"]
        profile.eating_pattern = answers["eating_pattern"]
        profile.main_difficulty = answers["main_difficulty"]
        restrictions = answers.get("dietary_restrictions", "").strip()
        profile.dietary_restrictions = None if restrictions.lower() == "none" else restrictions
        profile.ai_summary = self.clean_ai_summary(ai_summary, answers)
        profile.onboarding_complete = True
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def clean_ai_summary(self, ai_summary: str | None, answers: dict[str, str]) -> str:
        cleaned = extract_clean_summary_text(ai_summary)
        if cleaned:
            return cleaned
        return self.build_manual_summary(answers)

    def build_manual_summary(self, answers: dict[str, str]) -> str:
        restrictions = answers.get("dietary_restrictions", "none").strip() or "none"
        restrictions = "none" if restrictions.lower() == "none" else restrictions
        return normalize_whitespace(
            f"Your current focus is {answers.get('goal', 'eating better')}, with a "
            f"{answers.get('activity_level', 'moderate')} activity level and a "
            f"{answers.get('eating_pattern', 'mixed')} eating pattern. "
            f"I’ll keep your main challenge of {answers.get('main_difficulty', 'making food decisions')} "
            f"and your notes about {restrictions} in mind when I evaluate meals."
        )

    def reset_profile(self, user_id: int) -> None:
        profile = self.session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        if profile is not None:
            self.session.delete(profile)
            self.session.commit()

    def build_profile_text(self, profile: UserProfile) -> str:
        restrictions = profile.dietary_restrictions or "none"
        return (
            f"Goal: {profile.goal}\n"
            f"Activity: {profile.activity_level}\n"
            f"Eating pattern: {profile.eating_pattern}\n"
            f"Main difficulty: {profile.main_difficulty}\n"
            f"Restrictions: {restrictions}"
        )

    def onboarding_answers_complete(self, answers: dict[str, str]) -> bool:
        return all(question["key"] in answers for question in QUIZ_QUESTIONS)


class MealService:
    def __init__(self, session: Session):
        self.session = session

    def save_meal(
        self,
        user_id: int,
        input_type: str,
        raw_input: str | None,
        telegram_file_id: str | None,
        analysis: Any,
    ) -> MealEntry:
        meal = MealEntry(
            user_id=user_id,
            input_type=input_type,
            raw_input=raw_input,
            telegram_file_id=telegram_file_id,
            recognized_food=analysis.recognized_food,
            estimated_calories=analysis.estimated_calories,
            estimated_protein_g=analysis.estimated_protein_g,
            estimated_fat_g=analysis.estimated_fat_g,
            estimated_carbs_g=analysis.estimated_carbs_g,
            suitability_status=analysis.suitability_status,
            explanation=analysis.explanation,
            adjust_now="\n".join(analysis.adjust_now),
            do_later="\n".join(analysis.do_later),
            confidence=analysis.confidence,
        )
        self.session.add(meal)
        self.session.commit()
        self.session.refresh(meal)
        return meal

    def get_todays_meals(self, user_id: int) -> list[MealEntry]:
        today = datetime.utcnow().date()
        stmt = select(MealEntry).where(
            MealEntry.user_id == user_id,
            func.date(MealEntry.created_at) == today.isoformat(),
        ).order_by(MealEntry.created_at.desc())
        return list(self.session.scalars(stmt))

    def get_recent_meals(self, user_id: int, limit: int = 5) -> list[MealEntry]:
        stmt = (
            select(MealEntry)
            .where(MealEntry.user_id == user_id)
            .order_by(MealEntry.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def delete_user_meals(self, user_id: int) -> int:
        meals = list(self.session.scalars(select(MealEntry).where(MealEntry.user_id == user_id)))
        count = len(meals)
        for meal in meals:
            self.session.delete(meal)
        self.session.commit()
        return count

    def build_today_summary(self, meals: list[MealEntry]) -> str:
        if not meals:
            return "📊 No meals logged today yet.\n\nSend a meal photo 📸 or a short food description to get started."

        total_calories = sum(meal.estimated_calories or 0 for meal in meals)
        total_protein = sum(meal.estimated_protein_g or 0 for meal in meals)
        total_fat = sum(meal.estimated_fat_g or 0 for meal in meals)
        total_carbs = sum(meal.estimated_carbs_g or 0 for meal in meals)
        statuses = [meal.suitability_status for meal in meals]
        if any(status == "not suitable" for status in statuses):
            balance = "There was at least one meal that was tough for your goal, so the next one should be lighter and simpler."
        elif any(status == "undesirable" for status in statuses):
            balance = "Your day is still manageable, but there is already some heavier food in the mix."
        else:
            balance = "Your day looks fairly balanced so far."

        if total_carbs > total_protein * 2 and total_carbs > 120:
            balance = "Your day is generally okay, but carbs are running a bit high. The next meal should be lighter and more protein-focused."
        elif total_protein >= 90:
            balance = "Your protein intake looks solid so far. Keep the rest of the day simple and balanced."

        return (
            f"📊 Today you logged {len(meals)} meals\n\n"
            f"Approx totals:\n"
            f"Calories: {total_calories if total_calories else '-'}\n"
            f"Protein: {round(total_protein)} g\n"
            f"Fat: {round(total_fat)} g\n"
            f"Carbs: {round(total_carbs)} g\n\n"
            f"Summary:\n{balance}"
        )


def next_quiz_step(payload: dict[str, Any]) -> int:
    return int(payload.get("step", 0))
