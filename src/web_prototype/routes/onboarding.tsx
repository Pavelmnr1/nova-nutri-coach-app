import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { MobileFrame } from "@/components/MobileFrame";
import { saveUserProfile, saveUserName } from "@/lib/storage";
import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

export const Route = createFileRoute("/onboarding")({
  component: OnboardingPage,
});

interface StepConfig {
  question: string;
  type: "cards" | "textarea";
  options?: { icon: string; label: string; description?: string }[];
  chips?: string[];
  placeholder?: string;
}

const steps: StepConfig[] = [
  {
    question: "What is your main goal?",
    type: "cards",
    options: [
      { icon: "🎯", label: "Lose weight" },
      { icon: "⚖️", label: "Maintain weight" },
      { icon: "🥗", label: "Eat healthier" },
      { icon: "💪", label: "Gain weight" },
      { icon: "🚫", label: "Reduce unhealthy cravings" },
    ],
  },
  {
    question: "What is your sex?",
    type: "cards",
    options: [
      { icon: "👨", label: "Male" },
      { icon: "👩", label: "Female" },
      { icon: "🤝", label: "Prefer not to say" },
    ],
  },
  {
    question: "What is your age group?",
    type: "cards",
    options: [
      { icon: "🧒", label: "Under 18" },
      { icon: "🧑", label: "18–24" },
      { icon: "💼", label: "25–34" },
      { icon: "🏡", label: "35–44" },
      { icon: "🌟", label: "45+" },
    ],
  },
  {
    question: "How active are you?",
    type: "cards",
    options: [
      { icon: "🐢", label: "Low", description: "Mostly sitting, little exercise" },
      { icon: "🚶", label: "Medium", description: "Some walks, occasional sport" },
      { icon: "🏃", label: "High", description: "Regular workouts, active lifestyle" },
    ],
  },
  {
    question: "How would you describe your eating pattern?",
    type: "cards",
    options: [
      { icon: "🌀", label: "Chaotic", description: "I eat randomly" },
      { icon: "🍽️", label: "Often overeat", description: "Hard to stop" },
      { icon: "🐦", label: "Often undereat", description: "Forget to eat" },
      { icon: "🍫", label: "Crave sweets/fast food", description: "Constantly" },
      { icon: "✅", label: "Relatively stable", description: "Could just be better" },
    ],
  },
  {
    question: "What is your biggest difficulty right now?",
    type: "cards",
    options: [
      { icon: "🤷", label: "I don't know what to eat" },
      { icon: "📊", label: "Calorie tracking is too annoying" },
      { icon: "😤", label: "Hard to stop eating" },
      { icon: "⏰", label: "No time to think about food" },
      { icon: "🌙", label: "Evening cravings" },
      { icon: "🔍", label: "Can't tell if food is good" },
    ],
  },
  {
    question: "Any restrictions or important notes?",
    type: "textarea",
    placeholder:
      "E.g. vegetarian, lactose intolerant, allergies, religious restrictions, or type 'none'",
    chips: ["Vegetarian", "Vegan", "Lactose-free", "Gluten-free", "Halal", "No restrictions"],
  },
];

const keys = ["goal", "sex", "ageGroup", "activity", "eatingPattern", "difficulty", "restrictions"] as const;

function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0); // 0 = name step, 1-7 = question steps
  const [userName, setUserName] = useState("");
  const [answers, setAnswers] = useState<string[]>(Array(7).fill(""));
  const [direction, setDirection] = useState(1);
  const [loading, setLoading] = useState(false);

  const handleSelect = useCallback(
    (value: string) => {
      const questionIndex = step - 1;
      const next = [...answers];
      next[questionIndex] = value;
      setAnswers(next);

      if (step < 7) {
        setDirection(1);
        setTimeout(() => setStep(step + 1), 150);
      }
    },
    [answers, step]
  );

  const handleBack = () => {
    if (step > 0) {
      setDirection(-1);
      setStep(step - 1);
    }
  };

  const handleNameContinue = () => {
    if (userName.trim()) {
      saveUserName(userName.trim());
      setDirection(1);
      setStep(1);
    }
  };

  const handleFinish = () => {
    const profile = Object.fromEntries(keys.map((k, i) => [k, answers[i]]));
    saveUserProfile(profile as any);
    setLoading(true);
    setTimeout(() => navigate({ to: "/dashboard" }), 2000);
  };

  if (loading) {
    return (
      <MobileFrame>
        <div className="min-h-screen flex flex-col items-center justify-center px-8 bg-background">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            <span className="text-3xl" style={{ animation: "pulse-green 1.5s infinite" }}>🌿</span>
          </div>
          <h2 className="text-xl font-bold text-foreground mb-3">Building your profile...</h2>
          <div className="w-48 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full"
              style={{ animation: "progress-fill 1.5s ease-out forwards" }}
            />
          </div>
          <p className="text-muted-foreground text-sm mt-6">Nova is ready to meet you 👋</p>
        </div>
      </MobileFrame>
    );
  }

  const totalSteps = 8; // 1 name + 7 questions
  const current = step > 0 ? steps[step - 1] : null;
  const questionIndex = step - 1;

  return (
    <MobileFrame>
      <div className="min-h-screen flex flex-col bg-background">
        {/* Header */}
        <div className="px-4 pt-4 pb-2">
          <div className="flex items-center gap-3 mb-4">
            {step > 0 && (
              <button
                onClick={handleBack}
                className="w-9 h-9 rounded-full bg-muted flex items-center justify-center text-foreground"
              >
                ←
              </button>
            )}
            <span className="text-sm text-muted-foreground font-medium">
              {step + 1} of {totalSteps}
            </span>
          </div>
          <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-300"
              style={{ width: `${((step + 1) / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={step}
            custom={direction}
            initial={{ x: direction * 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: direction * -100, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="flex-1 px-5 pt-6"
          >
            {step === 0 && (
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-2">What's your name?</h2>
                <p className="text-muted-foreground text-sm mb-8">So Nova knows what to call you</p>
                <input
                  type="text"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="Enter your name"
                  autoFocus
                  className="w-full text-2xl font-semibold p-4 rounded-2xl border-2 border-border bg-card text-card-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
                  onKeyDown={(e) => e.key === "Enter" && handleNameContinue()}
                />
                <button
                  onClick={handleNameContinue}
                  disabled={!userName.trim()}
                  className="w-full mt-6 py-4 rounded-full bg-primary text-primary-foreground font-semibold text-base disabled:opacity-40 transition-all active:scale-[0.97]"
                >
                  Continue →
                </button>
              </div>
            )}

            {current && current.type === "cards" && (
              <>
                <h2 className="text-xl font-bold text-foreground mb-6">{current.question}</h2>
                <div className="flex flex-col gap-3">
                  {current.options?.map((opt) => (
                    <button
                      key={opt.label}
                      onClick={() => handleSelect(opt.label)}
                      className={`w-full text-left p-4 rounded-2xl border-2 transition-all active:scale-[0.97] ${
                        answers[questionIndex] === opt.label
                          ? "border-primary bg-primary/5 shadow-sm"
                          : "border-border bg-card hover:border-primary/30"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{opt.icon}</span>
                        <div>
                          <p className="font-semibold text-card-foreground">{opt.label}</p>
                          {opt.description && (
                            <p className="text-xs text-muted-foreground mt-0.5">{opt.description}</p>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}

            {current && current.type === "textarea" && (
              <div>
                <h2 className="text-xl font-bold text-foreground mb-6">{current.question}</h2>
                <textarea
                  value={answers[questionIndex]}
                  onChange={(e) => {
                    const next = [...answers];
                    next[questionIndex] = e.target.value;
                    setAnswers(next);
                  }}
                  placeholder={current.placeholder}
                  className="w-full h-32 p-4 rounded-2xl border-2 border-border bg-card text-card-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:border-primary transition-colors"
                />
                <div className="flex flex-wrap gap-2 mt-3">
                  {current.chips?.map((chip) => (
                    <button
                      key={chip}
                      onClick={() => {
                        const next = [...answers];
                        const val = next[questionIndex];
                        next[questionIndex] = val ? `${val}, ${chip}` : chip;
                        setAnswers(next);
                      }}
                      className="px-3 py-1.5 rounded-full bg-accent text-accent-foreground text-xs font-medium hover:bg-primary/10 transition-colors"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
                <button
                  onClick={handleFinish}
                  disabled={!answers[questionIndex]}
                  className="w-full mt-6 py-4 rounded-full bg-primary text-primary-foreground font-semibold text-base disabled:opacity-40 transition-all active:scale-[0.97]"
                >
                  Complete setup →
                </button>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </MobileFrame>
  );
}
