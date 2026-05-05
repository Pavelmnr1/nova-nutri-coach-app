import type { ReactNode } from "react";

export function MobileFrame({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-start justify-center bg-muted/30 md:py-8">
      <div className="w-full max-w-[390px] min-h-screen md:min-h-[844px] md:rounded-[2.5rem] md:border-[8px] md:border-foreground/10 md:shadow-2xl bg-background overflow-hidden relative">
        {children}
      </div>
    </div>
  );
}
