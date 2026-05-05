export interface UserProfile {
  goal: string;
  sex: string;
  ageGroup: string;
  activity: string;
  eatingPattern: string;
  difficulty: string;
  restrictions: string;
}

export interface MealEntry {
  id: string;
  food_name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  coach_note: string;
  timestamp: string;
  description: string;
}

export function getUserProfile(): UserProfile | null {
  const data = localStorage.getItem("nutricoach_profile");
  return data ? JSON.parse(data) : null;
}

export function saveUserProfile(profile: UserProfile) {
  localStorage.setItem("nutricoach_profile", JSON.stringify(profile));
}

export function getUserName(): string {
  return localStorage.getItem("nutricoach_username") || "";
}

export function saveUserName(name: string) {
  localStorage.setItem("nutricoach_username", name);
}

export function getMeals(): MealEntry[] {
  const data = localStorage.getItem("nutricoach_meals");
  return data ? JSON.parse(data) : [];
}

export function addMeal(meal: MealEntry) {
  const meals = getMeals();
  meals.unshift(meal);
  localStorage.setItem("nutricoach_meals", JSON.stringify(meals));
}

export function getStreak(): number {
  const data = localStorage.getItem("nutricoach_streak");
  return data ? parseInt(data, 10) : 0;
}

export function updateStreak() {
  const lastLog = localStorage.getItem("nutricoach_last_log");
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  if (lastLog === today) return;

  if (lastLog === yesterday) {
    const streak = getStreak() + 1;
    localStorage.setItem("nutricoach_streak", streak.toString());
  } else if (lastLog !== today) {
    localStorage.setItem("nutricoach_streak", "1");
  }

  localStorage.setItem("nutricoach_last_log", today);
}

export function getTodayCalories(): number {
  const today = new Date().toDateString();
  return getMeals()
    .filter((m) => new Date(m.timestamp).toDateString() === today)
    .reduce((sum, m) => sum + m.calories, 0);
}

export function getWeeklyData(): { day: string; calories: number }[] {
  const meals = getMeals();
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const result: { day: string; calories: number }[] = [];

  for (let i = 6; i >= 0; i--) {
    const date = new Date(Date.now() - i * 86400000);
    const dayMeals = meals.filter(
      (m) => new Date(m.timestamp).toDateString() === date.toDateString()
    );
    result.push({
      day: days[date.getDay()],
      calories: dayMeals.reduce((sum, m) => sum + m.calories, 0),
    });
  }

  return result;
}

export function getCalorieBudget(profile: UserProfile): number {
  const base = profile.sex === "Female" ? 1600 : 2000;
  const activityMod =
    profile.activity === "High" ? 400 : profile.activity === "Medium" ? 200 : 0;
  const goalMod =
    profile.goal === "Lose weight"
      ? -400
      : profile.goal === "Gain weight"
        ? 300
        : 0;
  return base + activityMod + goalMod;
}
