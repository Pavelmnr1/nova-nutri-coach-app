from app.services import MealService


class DummyMeal:
    def __init__(self, suitability_status: str, estimated_calories: int | None):
        self.suitability_status = suitability_status
        self.estimated_calories = estimated_calories


def test_build_today_summary_for_empty_day():
    service = MealService(session=None)  # type: ignore[arg-type]
    assert service.build_today_summary([]) == "Today you have not logged any meals yet."


def test_build_today_summary_with_heavier_day():
    service = MealService(session=None)  # type: ignore[arg-type]
    meals = [DummyMeal("undesirable", 600), DummyMeal("suitable", 400)]
    summary = service.build_today_summary(meals)
    assert "Today you logged 2 meals." in summary
    assert "workable" in summary
    assert "1000" in summary
