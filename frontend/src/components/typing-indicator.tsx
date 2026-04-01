export default function TypingIndicator() {
  return (
    <div className="flex gap-4 max-w-2xl">
      <div className="flex-shrink-0 w-12 h-12 bg-primary rounded-xl shadow-soft flex items-center justify-center">
        <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1.07A7.001 7.001 0 0 1 14 23h-4a7.001 7.001 0 0 1-6.93-6H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zm-4 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm8 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z" />
        </svg>
      </div>
      <div className="flex flex-col gap-2">
        <span className="font-headline font-bold text-xs text-on-surface uppercase tracking-tight">
          Niyog Assistant
        </span>
        <div className="bg-background px-5 py-4 rounded-2xl rounded-tl-none border border-outline inline-flex items-center gap-1.5">
          <span className="w-2 h-2 bg-on-surface-variant/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
          <span className="w-2 h-2 bg-on-surface-variant/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
          <span className="w-2 h-2 bg-on-surface-variant/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}
