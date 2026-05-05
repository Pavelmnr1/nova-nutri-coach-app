import { createFileRoute } from "@tanstack/react-router";
import { MobileFrame } from "@/components/MobileFrame";
import { BottomNav } from "@/components/BottomNav";
import { getUserProfile, addMeal, updateStreak } from "@/lib/storage";
import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { motion, AnimatePresence } from "framer-motion";

export const Route = createFileRoute("/log")({
  component: LogPage,
});

interface MealResult {
  food_name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  coach_note: string;
}

function LogPage() {
  const [mode, setMode] = useState<"choose" | "text" | "photo">("choose");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MealResult | null>(null);
  const [error, setError] = useState("");
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  const analyzeMeal = async (text: string, imageBase64?: string) => {
    setLoading(true);
    setError("");
    try {
      const profile = getUserProfile();
      const { data, error: fnError } = await supabase.functions.invoke("analyze-meal", {
        body: { description: text, profile, imageBase64 },
      });

      if (fnError) throw fnError;
      const mealData = data as MealResult;
      setResult(mealData);

      addMeal({
        id: crypto.randomUUID(),
        ...mealData,
        timestamp: new Date().toISOString(),
        description: text,
      });
      updateStreak();
    } catch (e) {
      console.error(e);
      setError("Nova is thinking... try again in a moment");
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setPhotoPreview(ev.target?.result as string);
        setMode("photo");
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <MobileFrame>
      <div className="min-h-screen bg-background pb-24">
        <div className="px-5 pt-6 pb-4">
          <h1 className="text-xl font-bold text-foreground">Log a meal</h1>
          <p className="text-sm text-muted-foreground mt-1">Tell Nova what you ate</p>
        </div>

        <AnimatePresence mode="wait">
          {!result && !loading && mode === "choose" && (
            <motion.div
              key="choose"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="px-5 flex flex-col gap-4"
            >
              <label className="cursor-pointer">
                <input type="file" accept="image/*" className="hidden" onChange={handlePhotoChange} />
                <div className="p-6 rounded-2xl bg-card border-2 border-border hover:border-primary/30 transition-all text-center active:scale-[0.97]">
                  <span className="text-4xl block mb-2">📸</span>
                  <p className="font-semibold text-card-foreground">Take/upload photo</p>
                  <p className="text-xs text-muted-foreground mt-1">Snap your meal for analysis</p>
                </div>
              </label>
              <button
                onClick={() => setMode("text")}
                className="p-6 rounded-2xl bg-card border-2 border-border hover:border-primary/30 transition-all text-center active:scale-[0.97]"
              >
                <span className="text-4xl block mb-2">✍️</span>
                <p className="font-semibold text-card-foreground">Describe your meal</p>
                <p className="text-xs text-muted-foreground mt-1">Type what you ate</p>
              </button>
            </motion.div>
          )}

          {!result && !loading && mode === "text" && (
            <motion.div
              key="text"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="px-5"
            >
              <button
                onClick={() => setMode("choose")}
                className="text-sm text-muted-foreground mb-3 flex items-center gap-1"
              >
                ← Back
              </button>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="E.g. Soup with sour cream and bread, or chicken salad with rice..."
                className="w-full h-36 p-4 rounded-2xl border-2 border-border bg-card text-card-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:border-primary transition-colors"
              />
              <button
                onClick={() => analyzeMeal(description)}
                disabled={!description.trim()}
                className="w-full mt-4 py-4 rounded-full bg-primary text-primary-foreground font-semibold disabled:opacity-40 active:scale-[0.97] transition-all"
              >
                Analyze meal 🔍
              </button>
            </motion.div>
          )}

          {!result && !loading && mode === "photo" && (
            <motion.div
              key="photo"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="px-5"
            >
              <button
                onClick={() => {
                  setMode("choose");
                  setPhotoPreview(null);
                }}
                className="text-sm text-muted-foreground mb-3 flex items-center gap-1"
              >
                ← Back
              </button>
              {photoPreview && (
                <img src={photoPreview} alt="Meal preview" className="w-full h-48 object-cover rounded-2xl mb-4" />
              )}
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what's in the photo..."
                className="w-full h-24 p-4 rounded-2xl border-2 border-border bg-card text-card-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:border-primary transition-colors"
              />
              <button
                onClick={() => {
                  // Strip the data URL prefix to get pure base64
                  const base64 = photoPreview ? photoPreview.split(",")[1] : undefined;
                  const mimeMatch = photoPreview?.match(/data:([^;]+);/);
                  const mime = mimeMatch ? mimeMatch[1] : "image/jpeg";
                  analyzeMeal(
                    description || "Analyze this food photo",
                    base64 ? `data:${mime};base64,${base64}` : undefined,
                  );
                }}
                className="w-full mt-4 py-4 rounded-full bg-primary text-primary-foreground font-semibold active:scale-[0.97] transition-all"
              >
                Analyze meal 🔍
              </button>
            </motion.div>
          )}

          {loading && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="px-5 py-16 text-center"
            >
              <div
                className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4"
                style={{ animation: "pulse-green 1.5s infinite" }}
              >
                <span className="text-2xl">🌿</span>
              </div>
              <p className="text-muted-foreground text-sm">Nova is analyzing your meal...</p>
            </motion.div>
          )}

          {error && (
            <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="px-5 py-8 text-center">
              <p className="text-destructive text-sm mb-4">{error}</p>
              <button
                onClick={() => {
                  setError("");
                  setMode("choose");
                }}
                className="text-primary text-sm font-medium"
              >
                Try again
              </button>
            </motion.div>
          )}

          {result && (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="px-5"
            >
              <MealResultCard
                result={result}
                onReset={() => {
                  setResult(null);
                  setDescription("");
                  setMode("choose");
                  setPhotoPreview(null);
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <BottomNav />
      </div>
    </MobileFrame>
  );
}

function MealResultCard({ result, onReset }: { result: MealResult; onReset: () => void }) {
  const [showDetails, setShowDetails] = useState(false);

  const verdict =
    result.calories < 500
      ? {
          emoji: "✅",
          text: "Great choice!",
          bg: "bg-emerald-50",
          border: "border-emerald-200",
          textColor: "text-emerald-700",
        }
      : result.calories <= 700
        ? {
            emoji: "⚠️",
            text: "Decent, eat mindfully",
            bg: "bg-amber-50",
            border: "border-amber-200",
            textColor: "text-amber-700",
          }
        : {
            emoji: "🔴",
            text: "Heavy meal — balance it",
            bg: "bg-red-50",
            border: "border-red-200",
            textColor: "text-red-700",
          };

  // Generate specific food suggestions based on the meal
  const eatNowOptions: Record<string, string[]> = {
    lowProtein: [
      "Add grilled chicken breast 🍗",
      "Add a boiled egg 🥚",
      "Add Greek yogurt 🥛",
      "Add cottage cheese 🧀",
    ],
    highFat: [
      "Add cucumber salad 🥗",
      "Add steamed broccoli 🥦",
      "Add fresh tomato slices 🍅",
      "Add pickled cabbage 🥬",
    ],
    highCarb: [
      "Add leafy green salad 🥬",
      "Add grilled zucchini 🥒",
      "Add sautéed mushrooms 🍄",
      "Add bell pepper strips 🫑",
    ],
    balanced: [
      "Add a side of fresh veggies 🥕",
      "Add a small fruit bowl 🍎",
      "Add a handful of nuts 🥜",
      "Add a light herb salad 🌿",
    ],
  };
  const eatNextOptions: Record<string, string[]> = {
    heavy: [
      "Light vegetable soup 🍲",
      "Green salad with lemon 🥗",
      "Steamed fish with herbs 🐟",
      "Clear broth with greens 🍵",
    ],
    medium: [
      "Grilled salmon with veggies 🐟",
      "Turkey wrap with salad 🌯",
      "Baked chicken with greens 🍗",
      "Lentil soup with bread 🍲",
    ],
    lowProtein: [
      "Grilled steak with salad 🥩",
      "Baked fish with rice 🐟",
      "Chicken stir-fry 🍳",
      "Bean and veggie bowl 🫘",
    ],
    light: [
      "Balanced dinner with protein 🍽️",
      "Pasta with lean meat sauce 🍝",
      "Rice bowl with chicken 🍚",
      "Stuffed peppers with meat 🫑",
    ],
  };

  const pickRandom = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)];

  const eatNowCategory =
    result.protein_g < 15
      ? "lowProtein"
      : result.fat_g > 25
        ? "highFat"
        : result.carbs_g > 60
          ? "highCarb"
          : "balanced";
  const eatNow = pickRandom(eatNowOptions[eatNowCategory]);

  const eatNextCategory =
    result.calories > 700 ? "heavy" : result.calories > 500 ? "medium" : result.protein_g < 15 ? "lowProtein" : "light";
  const eatNext = pickRandom(eatNextOptions[eatNextCategory]);

  return (
    <>
      <div className="rounded-3xl bg-card border border-border shadow-sm overflow-hidden">
        {/* Food name */}
        <div className="px-6 pt-7 pb-2">
          <h2 className="text-2xl font-extrabold text-foreground tracking-tight">{result.food_name}</h2>
        </div>

        {/* Verdict banner */}
        <div className={`mx-5 mt-2 px-5 py-3 rounded-2xl ${verdict.bg} ${verdict.border} border`}>
          <p className={`text-base font-bold ${verdict.textColor}`}>
            {verdict.emoji} {verdict.text}
          </p>
        </div>

        {/* Calories */}
        <div className="px-6 py-5">
          <p className="text-4xl font-extrabold text-foreground tracking-tight">
            {result.calories} <span className="text-lg font-semibold text-muted-foreground">kcal</span>
          </p>
        </div>

        {/* Action cards */}
        <div className="px-5 pb-5 grid grid-cols-2 gap-3">
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100">
            <p className="text-xs font-semibold text-emerald-600 mb-1">Eat now 🍽️</p>
            <p className="text-sm font-bold text-emerald-800">{eatNow}</p>
          </div>
          <div className="p-4 rounded-2xl bg-blue-50 border border-blue-100">
            <p className="text-xs font-semibold text-blue-600 mb-1">Eat next 🕐</p>
            <p className="text-sm font-bold text-blue-800">{eatNext}</p>
          </div>
        </div>

        {/* Details toggle */}
        <div className="px-6 pb-5">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {showDetails ? "Hide nutrition details ‹" : "See nutrition details ›"}
          </button>
          {showDetails && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-3 flex gap-6 text-sm"
            >
              <div>
                <p className="text-muted-foreground text-xs">Protein</p>
                <p className="font-bold text-foreground">{result.protein_g}g</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Carbs</p>
                <p className="font-bold text-foreground">{result.carbs_g}g</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Fat</p>
                <p className="font-bold text-foreground">{result.fat_g}g</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      <button
        onClick={onReset}
        className="w-full mt-4 py-3 rounded-full border-2 border-primary text-primary font-semibold active:scale-[0.97] transition-all"
      >
        Log another meal
      </button>
    </>
  );
}
