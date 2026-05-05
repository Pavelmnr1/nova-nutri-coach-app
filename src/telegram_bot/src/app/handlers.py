from __future__ import annotations

from io import BytesIO
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.ai import GeminiClient, MealAnalysisResult
from app.db import SessionLocal
from app.models import UserProfile
from app.quiz import QUIZ_QUESTIONS, format_question
from app.services import (
    ConversationService,
    MealService,
    ProfileService,
    UserService,
    next_quiz_step,
)
from app.utils import bullet_lines, format_confidence_percent, match_option


router = Router()


def _start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Begin onboarding", callback_data="quiz:start")
    return builder.as_markup()


def _quiz_keyboard(index: int) -> InlineKeyboardMarkup | None:
    question = QUIZ_QUESTIONS[index]
    options = question.get("options")
    if not options or len(options) > 6:
        return None

    builder = InlineKeyboardBuilder()
    for option_index, option in enumerate(options):
        builder.button(
            text=option.title() if len(option) < 24 else option,
            callback_data=f"quiz:answer:{index}:{option_index}",
        )
    builder.adjust(1 if len(options) > 3 else 2)
    return builder.as_markup()


def _friendly_analysis_text(result: MealAnalysisResult) -> str:
    adjust_now = result.adjust_now[:2] if result.adjust_now else ["Keep the portion reasonable"]
    do_later = result.do_later[:2] if result.do_later else ["Keep the next meal balanced"]
    confidence = format_confidence_percent(result.confidence)
    status = (result.suitability_status or "conditionally suitable").title()
    explanation = result.explanation or "This is an approximate evaluation based on limited information."
    explanation = explanation.strip()
    if len(explanation) > 180:
        explanation = explanation[:177].rstrip() + "..."

    portion = f"{result.estimated_portion_g} g" if result.estimated_portion_g is not None else "-"
    calories = result.estimated_calories if result.estimated_calories is not None else "-"
    protein = f"{round(result.estimated_protein_g)} g" if result.estimated_protein_g is not None else "-"
    fat = f"{round(result.estimated_fat_g)} g" if result.estimated_fat_g is not None else "-"
    carbs = f"{round(result.estimated_carbs_g)} g" if result.estimated_carbs_g is not None else "-"

    return (
        f"🍽 Food: {result.recognized_food}\n"
        f"Confidence: {confidence or '-'}\n"
        f"Status: {status}\n\n"
        f"Why:\n{explanation}\n\n"
        f"Now:\n{bullet_lines(adjust_now)}\n\n"
        f"Later:\n{bullet_lines(do_later)}\n\n"
        f"Approx:\n"
        f"Calories: {calories}\n"
        f"Portion: {portion}\n"
        f"Protein: {protein}\n"
        f"Fat: {fat}\n"
        f"Carbs: {carbs}\n\n"
        "Saved to diary ✅"
    ).strip()


def _onboarding_done_message(summary: str) -> str:
    return (
        "✅ Got it! I’ll use your goal, eating habits, and restrictions when evaluating your meals.\n\n"
        f"{summary}\n\n"
        "Here’s how I can help:\n"
        "• send a meal photo 📸\n"
        "• describe your food in one short sentence\n"
        "• check your daily summary with /today\n"
        "• view recent meals with /diary\n\n"
        "You can send your first meal now."
    )


async def _send_quiz_question(message: Message, index: int) -> None:
    await message.answer(format_question(index), reply_markup=_quiz_keyboard(index))


def _profile_context(profile: UserProfile) -> str:
    restrictions = profile.dietary_restrictions or "none"
    summary = profile.ai_summary or ""
    return (
        f"Goal: {profile.goal}\n"
        f"Sex: {profile.sex}\n"
        f"Age group: {profile.age_group}\n"
        f"Activity: {profile.activity_level}\n"
        f"Eating pattern: {profile.eating_pattern}\n"
        f"Main difficulty: {profile.main_difficulty}\n"
        f"Restrictions: {restrictions}\n"
        f"AI summary: {summary}"
    )


async def _download_photo_bytes(message: Message) -> tuple[bytes, str, str]:
    bot = message.bot
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    buffer = BytesIO()
    await bot.download(file, destination=buffer)
    mime_type = "image/jpeg"
    file_path = file.file_path or ""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".png":
        mime_type = "image/png"
    elif suffix == ".webp":
        mime_type = "image/webp"
    print(
        "DEBUG: telegram photo downloaded",
        {
            "file_id": photo.file_id,
            "file_path": file_path,
            "mime_type": mime_type,
            "bytes": len(buffer.getvalue()),
        },
    )
    return buffer.getvalue(), mime_type, photo.file_id


async def _download_photo_bytes_from_file_id(
    message: Message, file_id: str
) -> tuple[bytes, str, str]:
    bot = message.bot
    file = await bot.get_file(file_id)
    buffer = BytesIO()
    await bot.download(file, destination=buffer)
    mime_type = "image/jpeg"
    file_path = file.file_path or ""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".png":
        mime_type = "image/png"
    elif suffix == ".webp":
        mime_type = "image/webp"
    print(
        "DEBUG: telegram stored photo downloaded",
        {
            "file_id": file_id,
            "file_path": file_path,
            "mime_type": mime_type,
            "bytes": len(buffer.getvalue()),
        },
    )
    return buffer.getvalue(), mime_type, file_id


async def _process_quiz_answer(
    telegram_user_id: int,
    username: str | None,
    first_name: str | None,
    answer: str,
    ai_client: GeminiClient,
    target_message: Message,
) -> None:
    with SessionLocal() as session:
        user_service = UserService(session)
        conversation_service = ConversationService(session)
        profile_service = ProfileService(session)
        user = user_service.get_or_create_user(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
        )
        payload = conversation_service.get_payload(user.id)
        step = next_quiz_step(payload)
        answers = payload.get("answers", {})
        question = QUIZ_QUESTIONS[step]

        if question["options"]:
            matched_option = match_option(answer, question["options"])
            if matched_option:
                answer = matched_option
            else:
                await target_message.answer(
                    "Please choose one of the options below, or send the closest match and I’ll do my best to follow."
                )
                await _send_quiz_question(target_message, step)
                return

        answers[question["key"]] = answer
        step += 1

        if step >= len(QUIZ_QUESTIONS):
            summary = await ai_client.create_onboarding_summary(answers)
            profile = profile_service.save_onboarding_answers(user.id, answers, summary)
            conversation_service.clear_state(user.id)
            await target_message.answer(_onboarding_done_message(profile.ai_summary or summary))
            return

        conversation_service.set_state(user.id, "onboarding", {"step": step, "answers": answers})
        await _send_quiz_question(target_message, step)


async def _handle_quiz_answer(message: Message, ai_client: GeminiClient) -> None:
    await _process_quiz_answer(
        telegram_user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        answer=(message.text or "").strip(),
        ai_client=ai_client,
        target_message=message,
    )


async def _handle_clarification(message: Message, ai_client: GeminiClient) -> None:
    with SessionLocal() as session:
        user_service = UserService(session)
        conversation_service = ConversationService(session)
        meal_service = MealService(session)
        user = user_service.get_or_create_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        profile = user_service.get_profile(user.id)
        if profile is None:
            conversation_service.clear_state(user.id)
            await message.answer("Please complete onboarding first with /start.")
            return

        payload = conversation_service.get_payload(user.id)
        clarification_answer = (message.text or "").strip()

        if payload.get("input_type") == "text":
            analysis = await ai_client.analyze_text_meal(
                _profile_context(profile),
                payload["raw_input"],
                clarification_answer=clarification_answer,
                user_id=user.id,
            )
        else:
            image_bytes, mime_type, _ = await _download_photo_bytes_from_file_id(
                message, payload["telegram_file_id"]
            )
            analysis = await ai_client.analyze_image_meal(
                _profile_context(profile),
                image_bytes,
                mime_type,
                clarification_answer=clarification_answer,
            )

        if analysis.needs_clarification:
            await message.answer(
                analysis.clarification_question
                or "I still need one short clarification to evaluate this meal."
            )
            return

        meal_service.save_meal(
            user.id,
            payload["input_type"],
            payload.get("raw_input"),
            payload.get("telegram_file_id"),
            analysis,
        )
        conversation_service.clear_state(user.id)
        await message.answer(_friendly_analysis_text(analysis))


async def _analyze_text_message(message: Message, ai_client: GeminiClient) -> None:
    with SessionLocal() as session:
        user_service = UserService(session)
        conversation_service = ConversationService(session)
        meal_service = MealService(session)
        user = user_service.get_or_create_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        profile = user_service.get_profile(user.id)
        if profile is None or not profile.onboarding_complete:
            await message.answer("Please complete onboarding first with /start.")
            return

        meal_text = (message.text or "").strip()
        analysis = await ai_client.analyze_text_meal(
            _profile_context(profile),
            meal_text,
            user_id=user.id,
        )
        if analysis.needs_clarification:
            conversation_service.set_state(
                user.id,
                "clarification",
                {
                    "input_type": "text",
                    "raw_input": meal_text,
                },
            )
            await message.answer(
                analysis.clarification_question
                or "I need one quick clarification before I evaluate this meal."
            )
            return

        meal_service.save_meal(user.id, "text", message.text, None, analysis)
        conversation_service.clear_state(user.id)
        await message.answer(_friendly_analysis_text(analysis))


async def _analyze_photo_message(message: Message, ai_client: GeminiClient) -> None:
    progress_message = await message.answer("📸 Got it, analyzing your meal...")
    with SessionLocal() as session:
        user_service = UserService(session)
        conversation_service = ConversationService(session)
        meal_service = MealService(session)
        user = user_service.get_or_create_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        profile = user_service.get_profile(user.id)
        if profile is None or not profile.onboarding_complete:
            try:
                await progress_message.delete()
            except Exception:
                pass
            await message.answer("Please complete onboarding first with /start.")
            return

        image_bytes, mime_type, file_id = await _download_photo_bytes(message)
        analysis = await ai_client.analyze_image_meal(
            _profile_context(profile),
            image_bytes,
            mime_type,
        )
        if analysis.needs_clarification:
            conversation_service.set_state(
                user.id,
                "clarification",
                {
                    "input_type": "photo",
                    "telegram_file_id": file_id,
                },
            )
            await progress_message.edit_text(
                analysis.clarification_question
                or "I need one quick clarification before I evaluate this meal."
            )
            return

        meal_service.save_meal(user.id, "photo", None, file_id, analysis)
        conversation_service.clear_state(user.id)
        await progress_message.edit_text(_friendly_analysis_text(analysis))


async def _save_fallback_and_reply(
    message: Message,
    ai_client: GeminiClient,
    input_type: str,
    raw_input: str | None,
    telegram_file_id: str | None,
) -> None:
    with SessionLocal() as session:
        user_service = UserService(session)
        meal_service = MealService(session)
        user = user_service.get_or_create_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        profile = user_service.get_profile(user.id)
        if profile is None or not profile.onboarding_complete:
            await message.answer("Please complete onboarding first with /start.")
            return

        if input_type == "photo":
            analysis = ai_client._fallback_meal_result("", from_image=True)
        else:
            analysis = ai_client._fallback_meal_result(raw_input or "meal")

        meal_service.save_meal(user.id, input_type, raw_input, telegram_file_id, analysis)
        await message.answer(_friendly_analysis_text(analysis))


def register_handlers(ai_client: GeminiClient) -> Router:
    @router.message(Command("start"))
    async def start_command(message: Message) -> None:
        with SessionLocal() as session:
            user_service = UserService(session)
            conversation_service = ConversationService(session)
            user = user_service.get_or_create_user(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )
            profile = user_service.get_profile(user.id)
            if profile and profile.onboarding_complete:
                conversation_service.clear_state(user.id)
                await message.answer(
                    "You’re all set. Send a meal photo 📸 or a short meal description and I’ll evaluate it."
                )
                return

            conversation_service.set_state(user.id, "onboarding_intro", {"step": 0, "answers": {}})
            await message.answer(
                "👋 I can help you make quick, practical food decisions and keep a simple diary.\n\n"
                "Tap below to start a short 7-question setup.",
                reply_markup=_start_keyboard(),
            )

    @router.message(Command("reset"))
    async def reset_command(message: Message) -> None:
        with SessionLocal() as session:
            user_service = UserService(session)
            conversation_service = ConversationService(session)
            profile_service = ProfileService(session)
            user = user_service.get_or_create_user(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )
            conversation_service.clear_state(user.id)
            profile_service.reset_profile(user.id)
        await message.answer("✅ Your setup has been cleared. Run /start when you want to begin again.")

    @router.callback_query(F.data == "quiz:start")
    async def start_quiz_callback(callback: CallbackQuery) -> None:
        if callback.message is None:
            await callback.answer()
            return
        with SessionLocal() as session:
            user_service = UserService(session)
            conversation_service = ConversationService(session)
            user = user_service.get_or_create_user(
                telegram_user_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
            )
            conversation_service.set_state(user.id, "onboarding", {"step": 0, "answers": {}})
        await callback.answer()
        await _send_quiz_question(callback.message, 0)

    @router.callback_query(F.data.startswith("quiz:answer:"))
    async def quiz_answer_callback(callback: CallbackQuery) -> None:
        if callback.message is None:
            await callback.answer()
            return
        parts = callback.data.split(":")
        if len(parts) != 4:
            await callback.answer()
            return
        question_index = int(parts[2])
        option_index = int(parts[3])
        options = QUIZ_QUESTIONS[question_index].get("options") or []
        if option_index >= len(options):
            await callback.answer()
            return
        await callback.answer()
        await _process_quiz_answer(
            telegram_user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            answer=options[option_index],
            ai_client=ai_client,
            target_message=callback.message,
        )

    @router.message(Command("profile"))
    async def profile_command(message: Message) -> None:
        with SessionLocal() as session:
            user_service = UserService(session)
            profile_service = ProfileService(session)
            user = user_service.get_or_create_user(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )
            profile = user_service.get_profile(user.id)
            if profile is None or not profile.onboarding_complete:
                await message.answer("You do not have a completed profile yet. Use /start first.")
                return

            await message.answer(profile_service.build_profile_text(profile))

    @router.message(Command("today"))
    async def today_command(message: Message) -> None:
        with SessionLocal() as session:
            user_service = UserService(session)
            meal_service = MealService(session)
            user = user_service.get_or_create_user(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )
            meals = meal_service.get_todays_meals(user.id)
            await message.answer(meal_service.build_today_summary(meals))

    @router.message(Command("diary"))
    async def diary_command(message: Message) -> None:
        with SessionLocal() as session:
            user_service = UserService(session)
            meal_service = MealService(session)
            user = user_service.get_or_create_user(
                telegram_user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )
            meals = meal_service.get_recent_meals(user.id)
            if not meals:
                await message.answer("Your diary is empty so far. Send a meal to get started.")
                return

            lines = ["Recent meals:"]
            for meal in meals:
                timestamp = meal.created_at.strftime("%Y-%m-%d %H:%M")
                lines.append(f"- {timestamp} | {meal.recognized_food} | {meal.suitability_status}")
            await message.answer("\n".join(lines))

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "Send a meal photo 📸 or a short food description like 'rice with chicken'.\n"
            "Use /today for your daily summary, /diary for recent meals, /profile for your profile, and /reset to start over."
        )

    @router.message(F.photo)
    async def photo_message(message: Message) -> None:
        try:
            await _route_message(message, ai_client)
        except Exception:
            await _save_fallback_and_reply(message, ai_client, "photo", None, None)

    @router.message(F.text)
    async def text_message(message: Message) -> None:
        try:
            await _route_message(message, ai_client)
        except Exception:
            await _save_fallback_and_reply(message, ai_client, "text", message.text, None)

    return router


async def _route_message(message: Message, ai_client: GeminiClient) -> None:
    with SessionLocal() as session:
        user_service = UserService(session)
        conversation_service = ConversationService(session)
        user = user_service.get_or_create_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        state = conversation_service.get_state(user.id)

    if state and state.state_type == "onboarding_intro":
        text = (message.text or "").strip().lower()
        if text not in {"yes", "start", "ok", "okay"}:
            await message.answer(
                "Tap the button below to begin onboarding, or reply with yes.",
                reply_markup=_start_keyboard(),
            )
            return
        with SessionLocal() as session:
            conversation_service = ConversationService(session)
            conversation_service.set_state(user.id, "onboarding", {"step": 0, "answers": {}})
        await _send_quiz_question(message, 0)
        return

    if state and state.state_type == "onboarding":
        await _handle_quiz_answer(message, ai_client)
        return

    if state and state.state_type == "clarification":
        if not message.text:
            await message.answer("Please answer the clarification question with text.")
            return
        await _handle_clarification(message, ai_client)
        return

    if message.photo:
        await _analyze_photo_message(message, ai_client)
        return

    if message.text:
        if message.text.startswith("/"):
            return
        await _analyze_text_message(message, ai_client)
        return

    await message.answer("Please send either text or a food photo.")
