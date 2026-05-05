import { createFileRoute } from "@tanstack/react-router";
import { MobileFrame } from "@/components/MobileFrame";
import { BottomNav } from "@/components/BottomNav";
import { getUserProfile, getMeals, getUserName } from "@/lib/storage";
import { useState, useRef, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import ReactMarkdown from "react-markdown";

export const Route = createFileRoute("/coach")({
  component: CoachPage,
});

type Msg = { role: "user" | "assistant"; content: string };

function getInitialMessage(profile: ReturnType<typeof getUserProfile>): string {
  const name = getUserName();
  const goal = profile?.goal?.toLowerCase() || "reach your nutrition goals";
  return `Hi${name ? ` ${name}` : ""}! I'm Nova 🌿 I've looked at your profile and I'm ready to help you ${goal}. Ask me anything — what to eat, how you're doing, or just tell me what you had for lunch!`;
}

function getQuickReplies(profile: ReturnType<typeof getUserProfile>): string[] {
  const craving = profile?.eatingPattern?.includes("Crave") ? "a healthier swap for sweets" : "a healthy snack";
  return [
    "What should I eat for dinner?",
    "Am I on track today?",
    `Give me ${craving}`,
  ];
}

function CoachPage() {
  const profile = getUserProfile();
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", content: getInitialMessage(profile) },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const quickReplies = getQuickReplies(profile);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Msg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const meals = getMeals().slice(0, 10);
      const { data, error } = await supabase.functions.invoke("nova-chat", {
        body: {
          messages: [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
          profile,
          meals,
        },
      });

      if (error) throw error;
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I'm having trouble right now. Please try again! 🌿" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MobileFrame>
      <div className="h-screen flex flex-col bg-background">
        {/* Header */}
        <div className="px-5 pt-5 pb-3 border-b border-border flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-xl">🌿</span>
          </div>
          <div>
            <h1 className="text-base font-bold text-foreground">Nova</h1>
            <p className="text-xs text-muted-foreground">Your personal nutrition coach</p>
          </div>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3 pb-32">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mr-2 mt-1 shrink-0">
                  <span className="text-sm">🌿</span>
                </div>
              )}
              <div
                className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-br-md"
                    : "bg-card border border-border text-card-foreground rounded-bl-md"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="prose prose-sm max-w-none [&>p]:m-0">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <span className="text-sm">🌿</span>
              </div>
              <div className="px-4 py-3 rounded-2xl bg-card border border-border rounded-bl-md">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}

          {/* Quick replies */}
          {messages.length <= 1 && !isLoading && (
            <div className="flex flex-wrap gap-2 pt-2">
              {quickReplies.map((qr) => (
                <button
                  key={qr}
                  onClick={() => sendMessage(qr)}
                  className="px-3 py-2 rounded-full bg-accent text-accent-foreground text-xs font-medium hover:bg-primary/10 transition-colors active:scale-[0.97]"
                >
                  {qr}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="absolute bottom-16 left-0 right-0 p-3 bg-background border-t border-border max-w-[390px] mx-auto">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
              placeholder="Ask Nova anything..."
              className="flex-1 px-4 py-3 rounded-full border border-border bg-card text-card-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:border-primary transition-colors"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isLoading}
              className="w-11 h-11 rounded-full bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-40 active:scale-[0.95] transition-all shrink-0"
            >
              ↑
            </button>
          </div>
        </div>

        <BottomNav />
      </div>
    </MobileFrame>
  );
}
