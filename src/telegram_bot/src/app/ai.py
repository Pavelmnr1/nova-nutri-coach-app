from __future__ import annotations

import base64
import json
import re
import time
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field

from app.config import Settings
from app.prompts import (
    SYSTEM_RULES,
    image_meal_prompt,
    onboarding_summary_prompt,
    text_meal_prompt,
)


class MealAnalysisResult(BaseModel):
    recognized_food: str
    confidence: float | None = None
    estimated_portion_g: int | None = None
    estimated_calories: int | None = None
    estimated_protein_g: float | None = None
    estimated_fat_g: float | None = None
    estimated_carbs_g: float | None = None
    suitability_status: str | None = None
    explanation: str | None = None
    adjust_now: list[str] = Field(default_factory=list)
    do_later: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None


KEYWORD_ESTIMATES = {
    "pizza": ("pizza", 650, 22.0, 28.0, 70.0, "undesirable"),
    "cola": ("cola", 140, 0.0, 0.0, 35.0, "undesirable"),
    "rice with chicken": ("rice with chicken", 520, 32.0, 12.0, 58.0, "conditionally suitable"),
    "chicken with rice": ("rice with chicken", 520, 32.0, 12.0, 58.0, "conditionally suitable"),
    "chicken": ("chicken meal", 420, 32.0, 14.0, 24.0, "suitable"),
    "rice": ("rice meal", 320, 6.0, 3.0, 62.0, "conditionally suitable"),
    "burger": ("burger", 700, 28.0, 38.0, 50.0, "undesirable"),
    "croissant": ("coffee and croissant", 420, 7.0, 21.0, 45.0, "undesirable"),
    "pasta": ("pasta", 540, 18.0, 16.0, 76.0, "conditionally suitable"),
    "soup": ("soup and bread", 300, 12.0, 9.0, 38.0, "conditionally suitable"),
    "bread": ("bread meal", 220, 6.0, 3.0, 42.0, "conditionally suitable"),
}


TEXT_ANALYSIS_CACHE_TTL_SECONDS = 180


class GeminiRateLimitError(Exception):
    pass


class GeminiRequestError(Exception):
    pass


class GeminiClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self._text_cache: dict[tuple[int, str], tuple[float, MealAnalysisResult]] = {}

    async def _post(
        self,
        model: str,
        parts: list[dict[str, Any]],
        json_mode: bool = True,
        request_kind: str = "text",
    ) -> str:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is missing.")

        headers = {
            "x-goog-api-key": self.settings.gemini_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_RULES}]},
            "contents": [{"role": "user", "parts": parts}],
        }
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}

        print(
            "DEBUG: sending Gemini request",
            {
                "kind": request_kind,
                "model": model,
                "json_mode": json_mode,
                "parts_count": len(parts),
            },
        )
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{self.base_url}/{quote(model, safe='')}:generateContent",
                headers=headers,
                json=payload,
            )
            if response.status_code == 429:
                print("DEBUG: Gemini rate limit hit", {"kind": request_kind, "model": model})
                raise GeminiRateLimitError("Gemini quota limit reached.")
            if response.status_code >= 400:
                print(
                    "DEBUG: Gemini request failed",
                    {"kind": request_kind, "model": model, "status_code": response.status_code},
                )
                raise GeminiRequestError(f"Gemini request failed with status {response.status_code}")
            response.raise_for_status()
            data = response.json()
        raw = self._extract_text(data)
        print("RAW GEMINI RESPONSE:", raw)
        return raw

    def _extract_text(self, data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini returned no candidates.")

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if not text_parts:
            raise ValueError("Gemini returned no text content.")
        return "".join(text_parts)

    async def _parse_json(self, raw_text: str) -> dict[str, Any]:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            extracted = self._extract_json_substring(raw_text)
            if extracted:
                return json.loads(extracted)
            raise ValueError("Model returned invalid JSON.")

    def _extract_json_substring(self, raw_text: str) -> str | None:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return raw_text[start : end + 1]

    def _normalize_result(self, data: dict[str, Any]) -> MealAnalysisResult:
        adjust_now = data.get("adjust_now") or ["Keep the portion reasonable"]
        do_later = data.get("do_later") or ["Keep the next meal balanced"]
        if isinstance(adjust_now, str):
            adjust_now = [adjust_now]
        if isinstance(do_later, str):
            do_later = [do_later]

        normalized = {
            "recognized_food": data.get("recognized_food") or "meal",
            "confidence": data.get("confidence", 0.7),
            "estimated_portion_g": data.get("estimated_portion_g"),
            "estimated_calories": data.get("estimated_calories"),
            "estimated_protein_g": data.get("estimated_protein_g"),
            "estimated_fat_g": data.get("estimated_fat_g"),
            "estimated_carbs_g": data.get("estimated_carbs_g"),
            "suitability_status": data.get("suitability_status") or "conditionally suitable",
            "explanation": data.get("explanation")
            or "This looks workable, but the estimate is approximate.",
            "adjust_now": adjust_now,
            "do_later": do_later,
            "needs_clarification": bool(data.get("needs_clarification", False)),
            "clarification_question": data.get("clarification_question"),
        }
        if normalized["needs_clarification"] and not normalized["clarification_question"]:
            normalized["clarification_question"] = "Was this one portion or more?"
        return MealAnalysisResult.model_validate(normalized)

    def _extract_food_label_from_text(self, raw_text: str | None, default: str) -> str:
        text = (raw_text or "").lower()
        for keyword, estimate in KEYWORD_ESTIMATES.items():
            if keyword in text:
                return estimate[0]

        match = re.search(
            r"(?:looks like|appears to be|seems to be|dish is|food is)\s+([a-zA-Z ,\-]{3,80})",
            raw_text or "",
            re.IGNORECASE,
        )
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" .,:;")

        return default

    def _extract_partial_result_from_raw(
        self,
        raw_text: str | None,
        *,
        from_image: bool,
        fallback_hint: str,
    ) -> MealAnalysisResult | None:
        if not raw_text:
            return None

        explanation = re.sub(r"\s+", " ", raw_text).strip()
        if not explanation:
            return None

        recognized_food = self._extract_food_label_from_text(
            raw_text,
            "unrecognized meal from image" if from_image else fallback_hint,
        )
        print(
            "DEBUG: partial Gemini output preserved",
            {"from_image": from_image, "recognized_food": recognized_food},
        )
        return MealAnalysisResult(
            recognized_food=recognized_food,
            confidence=0.35 if from_image else 0.55,
            estimated_portion_g=None,
            estimated_calories=None,
            estimated_protein_g=None,
            estimated_fat_g=None,
            estimated_carbs_g=None,
            suitability_status="conditionally suitable",
            explanation=explanation[:280],
            adjust_now=["Use this as a rough read only"],
            do_later=["Send a short text description for a more reliable estimate"],
            needs_clarification=False,
            clarification_question=None,
        )

    def _fallback_summary(self, answers: dict[str, str]) -> str:
        restrictions = answers.get("dietary_restrictions", "none")
        return (
            f"The user wants to {answers.get('goal', 'eat better')} and has a "
            f"{answers.get('activity_level', 'moderate')} activity level. "
            f"Their main challenge is {answers.get('main_difficulty', 'making food decisions')}, "
            f"with restrictions or notes: {restrictions}."
        )

    def _fallback_meal_result(
        self,
        meal_hint: str,
        from_image: bool = False,
        raw_text: str | None = None,
    ) -> MealAnalysisResult:
        if from_image:
            print("DEBUG: image fallback triggered")
            return MealAnalysisResult(
                recognized_food="unrecognized meal from image",
                confidence=0.2,
                estimated_portion_g=None,
                estimated_calories=None,
                estimated_protein_g=None,
                estimated_fat_g=None,
                estimated_carbs_g=None,
                suitability_status="conditionally suitable",
                explanation="I could not identify this image reliably enough to estimate the meal with confidence. A short text description would help a lot.",
                adjust_now=["Send one short description if you want a better estimate"],
                do_later=["Use the result carefully because recognition was uncertain"],
                needs_clarification=False,
                clarification_question=None,
            )

        lower_text = (meal_hint or "").lower()
        food_name = "meal"
        calories = 450
        protein = 18.0
        fat = 14.0
        carbs = 48.0
        status = "conditionally suitable"

        for keyword, estimate in KEYWORD_ESTIMATES.items():
            if keyword in lower_text:
                food_name, calories, protein, fat, carbs, status = estimate
                break
        else:
            compact = re.sub(r"\s+", " ", meal_hint).strip()
            if compact:
                food_name = compact[:80]

        explanation = (
            "This is a practical estimate based on the available input, so treat it as approximate."
        )
        if status == "suitable":
            explanation = "This looks fairly aligned with the goal if the portion is reasonable."
        elif status == "undesirable":
            explanation = "This looks heavier for the goal, but it can still be managed with a few adjustments."

        adjust_now = ["Keep the portion moderate", "Skip extra sugary drinks or sauces"]
        do_later = ["Make the next meal lighter", "Prioritize protein and vegetables later"]
        if "cola" in lower_text:
            adjust_now = ["Keep the portion moderate", "Replace cola with water if possible"]
        if "rice" in lower_text and "chicken" in lower_text:
            adjust_now = ["Keep the rice portion sensible", "Add vegetables if available"]
            do_later = ["Keep the next meal simple and balanced", "Do not overcompensate later"]

        return MealAnalysisResult(
            recognized_food=food_name,
            confidence=0.65 if not from_image else 0.55,
            estimated_portion_g=350,
            estimated_calories=calories,
            estimated_protein_g=protein,
            estimated_fat_g=fat,
            estimated_carbs_g=carbs,
            suitability_status=status,
            explanation=explanation,
            adjust_now=adjust_now,
            do_later=do_later,
            needs_clarification=False,
            clarification_question=None,
        )

    async def create_onboarding_summary(self, answers: dict[str, str]) -> str:
        try:
            raw = await self._post(
                model=self.settings.gemini_model,
                parts=[{"text": onboarding_summary_prompt(answers)}],
                json_mode=False,
                request_kind="onboarding_summary",
            )
            return raw.strip() or self._fallback_summary(answers)
        except (GeminiRateLimitError, GeminiRequestError, Exception):
            return self._fallback_summary(answers)

    def _get_cached_text_result(
        self,
        user_id: int | None,
        meal_text: str,
        clarification_answer: str | None,
    ) -> MealAnalysisResult | None:
        if user_id is None or clarification_answer:
            return None
        key = (user_id, meal_text.strip().lower())
        cached = self._text_cache.get(key)
        if not cached:
            return None
        created_at, result = cached
        if time.time() - created_at > TEXT_ANALYSIS_CACHE_TTL_SECONDS:
            self._text_cache.pop(key, None)
            return None
        print("DEBUG: text analysis cache hit", {"user_id": user_id, "meal_text": meal_text})
        return result

    def _store_cached_text_result(self, user_id: int | None, meal_text: str, result: MealAnalysisResult) -> None:
        if user_id is None:
            return
        key = (user_id, meal_text.strip().lower())
        self._text_cache[key] = (time.time(), result)

    def _local_text_meal_result(self, meal_text: str) -> MealAnalysisResult | None:
        lower_text = meal_text.lower()
        for keyword, estimate in KEYWORD_ESTIMATES.items():
            if keyword in lower_text:
                food_name, calories, protein, fat, carbs, status = estimate
                adjust_now = ["Keep the portion moderate", "Skip extra sugary drinks or sauces"]
                do_later = ["Make the next meal lighter", "Prioritize protein and vegetables later"]
                if "rice" in lower_text and "chicken" in lower_text:
                    adjust_now = ["Keep the rice portion sensible", "Add vegetables if available"]
                    do_later = ["Keep the next meal simple and balanced", "Do not overcompensate later"]
                if "cola" in lower_text:
                    adjust_now = ["Replace cola with water if possible", "Keep the rest of the meal moderate"]
                print("DEBUG: local heuristic text analysis used", {"meal_text": meal_text, "keyword": keyword})
                return MealAnalysisResult(
                    recognized_food=food_name,
                    confidence=0.78,
                    estimated_portion_g=350,
                    estimated_calories=calories,
                    estimated_protein_g=protein,
                    estimated_fat_g=fat,
                    estimated_carbs_g=carbs,
                    suitability_status=status,
                    explanation="This is a quick local estimate for a common meal pattern, so treat it as approximate.",
                    adjust_now=adjust_now,
                    do_later=do_later,
                    needs_clarification=False,
                    clarification_question=None,
                )
        return None

    async def analyze_text_meal(
        self,
        profile_summary: str,
        meal_text: str,
        clarification_answer: str | None = None,
        user_id: int | None = None,
    ) -> MealAnalysisResult:
        cached = self._get_cached_text_result(user_id, meal_text, clarification_answer)
        if cached is not None:
            return cached

        if clarification_answer is None:
            heuristic = self._local_text_meal_result(meal_text)
            if heuristic is not None:
                self._store_cached_text_result(user_id, meal_text, heuristic)
                return heuristic

        prompt = text_meal_prompt(profile_summary, meal_text)
        if clarification_answer:
            prompt += f"\nClarification from the user:\n{clarification_answer}\n"
        result = await self._request_meal_analysis(
            model=self.settings.gemini_model,
            parts=[{"text": prompt}],
            fallback_hint=f"{meal_text}. {clarification_answer or ''}".strip(),
            request_kind="text",
        )
        if clarification_answer is None:
            self._store_cached_text_result(user_id, meal_text, result)
        return result

    async def analyze_image_meal(
        self,
        profile_summary: str,
        image_bytes: bytes,
        mime_type: str,
        clarification_answer: str | None = None,
    ) -> MealAnalysisResult:
        text_part = image_meal_prompt(profile_summary)
        if clarification_answer:
            text_part += f"\nClarification from the user:\n{clarification_answer}\n"
        selected_model = self.settings.gemini_vision_model or self.settings.gemini_model
        print(
            "DEBUG: image analysis config",
            {
                "vision_model": selected_model,
                "mime_type": mime_type,
                "image_bytes": len(image_bytes),
            },
        )
        try:
            image_b64 = base64.b64encode(image_bytes).decode("ascii")
            parts = [
                {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                {"text": text_part},
            ]
            return await self._request_meal_analysis(
                model=selected_model,
                parts=parts,
                fallback_hint=clarification_answer or "",
                from_image=True,
                request_kind="image",
            )
        except Exception:
            return self._fallback_meal_result(
                clarification_answer or "",
                from_image=True,
            )

    async def _request_meal_analysis(
        self,
        model: str,
        parts: list[dict[str, Any]],
        fallback_hint: str,
        from_image: bool = False,
        request_kind: str = "text",
    ) -> MealAnalysisResult:
        last_raw: str | None = None
        try:
            raw = await self._post(
                model=model,
                parts=parts,
                json_mode=True,
                request_kind=request_kind,
            )
            last_raw = raw
            data = await self._parse_json(raw)
            print("DEBUG: Gemini response parsed successfully", {"kind": request_kind})
            return self._normalize_result(data)
        except GeminiRateLimitError:
            print("DEBUG: Gemini retry skipped due to rate limit", {"kind": request_kind})
            partial = self._extract_partial_result_from_raw(
                last_raw,
                from_image=from_image,
                fallback_hint=fallback_hint or "meal",
            )
            if partial is not None:
                return partial
            return self._fallback_meal_result(
                fallback_hint,
                from_image=from_image,
                raw_text=fallback_hint,
            )
        except GeminiRequestError:
            print("DEBUG: Gemini retry skipped due to request error", {"kind": request_kind})
            partial = self._extract_partial_result_from_raw(
                last_raw,
                from_image=from_image,
                fallback_hint=fallback_hint or "meal",
            )
            if partial is not None:
                return partial
            return self._fallback_meal_result(
                fallback_hint,
                from_image=from_image,
                raw_text=fallback_hint,
            )
        except Exception:
            print("DEBUG: primary Gemini parse/request failed", {"kind": request_kind})
            retry_parts = list(parts)
            retry_parts.append(
                {
                    "text": (
                        "Return valid JSON only. Do not include markdown, comments, or code fences. "
                        "Use the exact schema requested."
                    )
                }
            )
            try:
                raw = await self._post(
                    model=model,
                    parts=retry_parts,
                    json_mode=True,
                    request_kind=f"{request_kind}_retry",
                )
                last_raw = raw
                data = await self._parse_json(raw)
                print("DEBUG: Gemini response parsed successfully on retry", {"kind": request_kind})
                return self._normalize_result(data)
            except GeminiRateLimitError:
                print("DEBUG: retry aborted due to rate limit", {"kind": request_kind})
                partial = self._extract_partial_result_from_raw(
                    last_raw,
                    from_image=from_image,
                    fallback_hint=fallback_hint or "meal",
                )
                if partial is not None:
                    return partial
                return self._fallback_meal_result(
                    fallback_hint,
                    from_image=from_image,
                    raw_text=fallback_hint,
                )
            except GeminiRequestError:
                print("DEBUG: retry aborted due to request error", {"kind": request_kind})
                partial = self._extract_partial_result_from_raw(
                    last_raw,
                    from_image=from_image,
                    fallback_hint=fallback_hint or "meal",
                )
                if partial is not None:
                    return partial
                return self._fallback_meal_result(
                    fallback_hint,
                    from_image=from_image,
                    raw_text=fallback_hint,
                )
            except Exception:
                print("DEBUG: retry Gemini parse/request failed", {"kind": request_kind})
                partial = self._extract_partial_result_from_raw(
                    last_raw,
                    from_image=from_image,
                    fallback_hint=fallback_hint or "meal",
                )
                if partial is not None:
                    return partial
                return self._fallback_meal_result(
                    fallback_hint,
                    from_image=from_image,
                    raw_text=fallback_hint,
                )
