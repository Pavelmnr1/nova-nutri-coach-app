import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { MobileFrame } from "@/components/MobileFrame";
import { BottomNav } from "@/components/BottomNav";
import {
  getUserProfile,
  getMeals,
  getStreak,
  getTodayCalories,
  getCalorieBudget,
  getUserName,
} from "@/lib/storage";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
});

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function getInsight(profile: ReturnType<typeof getUserProfile>) {
  if (!profile) return null;
  if (profile.goal === "Lose weight")
    return { emoji: "🔥", text: `Today's calorie budget: ${getCalorieBudget(profile)} kcal` };
  if (profile.difficulty === "Evening cravings")
    return { emoji: "🌙", text: "Tip: eat a protein snack at 5pm to avoid evening cravings tonight" };
  if (profile.eatingPattern === "Chaotic")
    return { emoji: "🔥", text: "Let's build your first logging streak!" };
  if (profile.goal === "Eat healthier")
    return { emoji: "🥗", text: "Focus on adding one extra serving of vegetables today" };
  return { emoji: "💪", text: `Your daily target: ${getCalorieBudget(profile)} kcal — let's hit it!` };
}

const placeholderMeals = [
  { food_name: "Oatmeal with berries", calories: 310, time: "8:30 AM", emoji: "🥣" },
  { food_name: "Chicken salad", calories: 420, time: "1:00 PM", emoji: "🥗" },
  { food_name: "Cornmeal porridge with cheese", calories: 380, time: "7:00 PM", emoji: "🧀" },
];

function DashboardPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(getUserProfile());
  const [meals] = useState(getMeals());
  const streak = getStreak();
  const todayCal = getTodayCalories();

  useEffect(() => {
    const p = getUserProfile();
    if (!p) {
      navigate({ to: "/" });
      return;
    }
    setProfile(p);
  }, [navigate]);

  if (!profile) return null;

  const insight = getInsight(profile);
  const budget = getCalorieBudget(profile);
  const recentMeals = meals.length > 0 ? meals.slice(0, 3) : null;

  return (
    <MobileFrame>
      <div className="min-h-screen bg-background pb-24">
        {/* Header */}
        <div className="px-5 pt-6 pb-4">
          <h1 className="text-2xl font-bold text-foreground">
            {getGreeting()}{getUserName() ? `, ${getUserName()}` : ""} 👋
          </h1>
          {streak > 0 && (
            <p className="text-sm text-streak font-semibold mt-1">
              🔥 {streak} day streak
            </p>
          )}
        </div>

        {/* Insight card */}
        {insight && (
          <div className="mx-5 p-4 rounded-2xl bg-primary/5 border border-primary/20 mb-4" style={{ animation: "fade-up 0.5s ease-out" }}>
            <p className="text-sm text-foreground">
              <span className="mr-2">{insight.emoji}</span>
              {insight.text}
            </p>
          </div>
        )}

        {/* Calorie progress */}
        <div className="mx-5 p-4 rounded-2xl bg-card shadow-sm border border-border mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">Today</span>
            <span className={`text-sm font-bold ${todayCal > budget ? 'text-destructive' : 'text-foreground'}`}>{todayCal} / {budget} kcal</span>
          </div>
          <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${todayCal > budget ? 'bg-destructive' : 'bg-primary'}`}
              style={{ width: `${Math.min((todayCal / budget) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Log meal CTA */}
        <div className="px-5 mb-5">
          <Link
            to="/log"
            className="flex items-center justify-center gap-2 w-full py-4 rounded-2xl bg-primary text-primary-foreground font-semibold text-base shadow-lg active:scale-[0.97] transition-transform"
            style={{ boxShadow: "0 4px 20px oklch(0.65 0.19 145 / 25%)" }}
          >
            📸 Log a meal
          </Link>
        </div>

        {/* Recent meals */}
        <div className="px-5">
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">Recent meals</h3>
          <div className="flex flex-col gap-3">
            {recentMeals
              ? recentMeals.map((meal) => (
                  <div key={meal.id} className="p-3 rounded-xl bg-card border border-border shadow-sm flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center text-lg">🍽️</div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-card-foreground">{meal.food_name}</p>
                      <p className="text-xs text-muted-foreground">{new Date(meal.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</p>
                    </div>
                    <span className="text-sm font-bold text-primary">{meal.calories} kcal</span>
                  </div>
                ))
              : placeholderMeals.map((meal) => (
                  <div key={meal.food_name} className="p-3 rounded-xl bg-card border border-border shadow-sm flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center text-lg">{meal.emoji}</div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-card-foreground">{meal.food_name}</p>
                      <p className="text-xs text-muted-foreground">{meal.time}</p>
                    </div>
                    <span className="text-sm font-bold text-primary">{meal.calories} kcal</span>
                  </div>
                ))}
          </div>
        </div>

        <BottomNav />
      </div>
    </MobileFrame>
  );
}
