import { createFileRoute } from "@tanstack/react-router";
import { MobileFrame } from "@/components/MobileFrame";
import { BottomNav } from "@/components/BottomNav";
import { getUserProfile, getMeals, getStreak, getWeeklyData, getCalorieBudget, getUserName } from "@/lib/storage";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, CartesianGrid } from "recharts";

export const Route = createFileRoute("/progress")({
  component: ProgressPage,
});

function ProgressPage() {
  const profile = getUserProfile();
  const meals = getMeals();
  const streak = getStreak();
  const weeklyData = getWeeklyData();
  const budget = profile ? getCalorieBudget(profile) : 2000;

  const weekMeals = meals.filter((m) => {
    const d = new Date(m.timestamp);
    const weekAgo = new Date(Date.now() - 7 * 86400000);
    return d >= weekAgo;
  });

  const daysLogged = new Set(weekMeals.map((m) => new Date(m.timestamp).toDateString())).size;
  const weeklyGoalProgress = Math.round((daysLogged / 7) * 100);

  return (
    <MobileFrame>
      <div className="min-h-screen bg-background pb-24">
        <div className="px-5 pt-6 pb-4">
          <h1 className="text-xl font-bold text-foreground">{getUserName() ? `${getUserName()}'s journey` : "Progress"}</h1>
          <p className="text-sm text-muted-foreground mt-1">Your nutrition journey</p>
        </div>

        {/* Streak */}
        <div className="mx-5 p-5 rounded-2xl bg-card border border-border shadow-sm text-center mb-4" style={{ animation: "fade-up 0.5s ease-out" }}>
          <span className="text-5xl block mb-2">🔥</span>
          <p className="font-extrabold text-streak" style={{ fontSize: "48px", lineHeight: 1 }}>{streak}</p>
          <p className="text-sm text-muted-foreground">Day streak</p>
        </div>

        {/* Weekly chart */}
        <div className="mx-5 p-4 rounded-2xl bg-card border border-border shadow-sm mb-4" style={{ animation: "fade-up 0.5s ease-out 0.1s both" }}>
          <h3 className="text-sm font-semibold text-foreground mb-3">Weekly Calories</h3>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} width={35} />
                <Bar dataKey="calories" fill="var(--primary)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weekly Calorie Balance */}
        {(() => {
          const weeklyTotal = weeklyData.reduce((s, d) => s + d.calories, 0);
          const weeklyBudget = budget * 7;
          const isOver = weeklyTotal > weeklyBudget;
          const diff = Math.abs(weeklyBudget - weeklyTotal);
          return (
            <div className="mx-5 p-5 rounded-2xl bg-card border border-border shadow-sm mb-4" style={{ animation: "fade-up 0.5s ease-out 0.2s both" }}>
              <p className="text-sm font-semibold text-muted-foreground mb-2">This week</p>
              <p className="text-3xl font-extrabold text-foreground tracking-tight">{weeklyTotal.toLocaleString()} <span className="text-base font-semibold text-muted-foreground">kcal</span></p>
              <p className="text-xs text-muted-foreground mb-3">of {weeklyBudget.toLocaleString()} kcal weekly budget</p>
              <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden mb-3">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${isOver ? 'bg-destructive' : 'bg-primary'}`}
                  style={{ width: `${Math.min((weeklyTotal / weeklyBudget) * 100, 100)}%` }}
                />
              </div>
              <p className={`text-xs font-medium ${isOver ? 'text-destructive' : 'text-primary'}`}>
                {isOver
                  ? `⚠️ ${diff.toLocaleString()} kcal over — lighter meals tomorrow will balance it`
                  : `You're on track 🎯 ${diff.toLocaleString()} kcal remaining this week`}
              </p>
            </div>
          );
        })()}

        {/* Insight cards */}
        <div className="px-5 pb-32 flex flex-col gap-3" style={{ animation: "fade-up 0.5s ease-out 0.3s both" }}>
          <InsightCard emoji="📋" text={`You logged ${weekMeals.length} meals this week`} />
          {profile?.eatingPattern && (
            <InsightCard
              emoji="💡"
              text={
                profile.eatingPattern === "Chaotic"
                  ? "You're building consistency — keep logging daily!"
                  : profile.eatingPattern === "Often overeat"
                    ? "Try mindful eating: pause between bites"
                    : `Pattern: ${profile.eatingPattern} — awareness is the first step!`
              }
            />
          )}
          {profile?.goal && (
            <InsightCard
              emoji="🎯"
              text={`Working toward: ${profile.goal}. Average ${Math.round(weeklyData.reduce((s, d) => s + d.calories, 0) / 7)} kcal/day vs ${budget} target.`}
            />
          )}
        </div>

        <BottomNav />
      </div>
    </MobileFrame>
  );
}

function InsightCard({ emoji, text }: { emoji: string; text: string }) {
  return (
    <div className="p-3 rounded-xl bg-card border border-border shadow-sm flex items-start gap-3">
      <span className="text-lg">{emoji}</span>
      <p className="text-sm text-card-foreground">{text}</p>
    </div>
  );
}
