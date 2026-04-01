import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";

interface ChatMessageProps {
  role: "assistant" | "user";
  content: string;
  timestamp?: string;
}

export default function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  if (role === "assistant") {
    return (
      <div className="flex gap-4 max-w-2xl">
        <div className="flex-shrink-0 w-12 h-12 bg-primary rounded-xl shadow-soft flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1.07A7.001 7.001 0 0 1 14 23h-4a7.001 7.001 0 0 1-6.93-6H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zm-4 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm8 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z" />
          </svg>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="font-headline font-bold text-xs text-on-surface uppercase tracking-tight">
              Niyog Assistant
            </span>
            {timestamp && (
              <span className="font-body text-[11px] text-on-surface-variant">
                {timestamp}
              </span>
            )}
          </div>
          <div className="bg-background p-5 rounded-2xl rounded-tl-none border border-outline prose prose-sm max-w-none text-on-surface">
            <ReactMarkdown
              remarkPlugins={[remarkBreaks]}
              components={{
                p: ({ children }) => <p className="leading-relaxed text-[15px] mb-3 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-on-surface">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc list-inside space-y-1 text-[15px] mb-3">{children}</ul>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                code: ({ children }) => <code className="bg-surface-container px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-4 max-w-2xl ml-auto flex-row-reverse">
      <div className="flex-shrink-0 w-12 h-12 bg-primary-container rounded-xl flex items-center justify-center">
        <span className="font-headline font-bold text-sm text-on-primary-container">
          You
        </span>
      </div>
      <div className="flex flex-col gap-2 items-end">
        {timestamp && (
          <span className="font-body text-[11px] text-on-surface-variant">
            {timestamp}
          </span>
        )}
        <div className="bg-primary text-white p-5 rounded-2xl rounded-tr-none">
          <p className="leading-relaxed text-[15px] whitespace-pre-wrap">
            {content}
          </p>
        </div>
      </div>
    </div>
  );
}
