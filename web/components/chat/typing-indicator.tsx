"use client";

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-0.5">
      <span className="sr-only">Coach is typing</span>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="inline-block size-1.5 rounded-full bg-muted-foreground/40"
          style={{
            animation: `typing-dot 1.4s infinite ${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}
