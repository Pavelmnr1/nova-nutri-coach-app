import { createFileRoute, Link } from "@tanstack/react-router";
import { MobileFrame } from "@/components/MobileFrame";
import { getUserProfile } from "@/lib/storage";
import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "NutriCoach — Your AI Nutritionist Who Actually Knows You" },
      { name: "description", content: "A personal AI nutrition coach that remembers your habits, struggles, and progress. Built for Eastern European cuisine." },
      { property: "og:title", content: "NutriCoach — Your AI Nutritionist" },
      { property: "og:description", content: "Not a generic bot. A coach that knows you." },
    ],
  }),
  component: LandingPage,
});

function LandingPage() {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const profile = getUserProfile();
    if (profile) {
      navigate({ to: "/dashboard" });
    } else {
      setChecking(false);
    }
  }, [navigate]);

  if (checking) return null;

  return (
    <MobileFrame>
      <div
        className="min-h-screen flex flex-col items-center justify-center px-8 text-center"
        style={{
          background: "linear-gradient(180deg, #F0FFF4 0%, #FFFFFF 100%)",
        }}
      >
        <div
          className="mb-8"
          style={{ animation: "fade-up 0.8s ease-out" }}
        >
          <div className="w-20 h-20 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">🧠🌿</span>
          </div>
          <h1 className="text-3xl font-extrabold text-foreground tracking-tight">
            NutriCoach
          </h1>
          <p className="text-primary font-semibold mt-1 text-sm">
            Your AI nutritionist who actually knows you
          </p>
        </div>

        <p
          className="text-muted-foreground text-sm leading-relaxed max-w-[280px] mb-10"
          style={{ animation: "fade-up 0.8s ease-out 0.2s both" }}
        >
          Not a generic bot. A coach that remembers your habits, your struggles,
          and your progress.
        </p>

        <Link
          to="/onboarding"
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground font-semibold text-base px-8 py-4 rounded-full shadow-lg transition-all hover:shadow-xl active:scale-[0.97]"
          style={{
            animation: "fade-up 0.8s ease-out 0.4s both",
            boxShadow: "0 4px 24px oklch(0.65 0.19 145 / 30%)",
          }}
        >
          Start my journey
          <span>→</span>
        </Link>
      </div>
    </MobileFrame>
  );
}
