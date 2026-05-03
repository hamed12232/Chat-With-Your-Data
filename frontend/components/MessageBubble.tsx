"use client";

export type Message = {
  role: "user" | "assistant";
  content: string;
  variant?: "error";
  sources?: string[];
};

interface MessageBubbleProps {
  message: Message;
}

function WarningIcon() {
  return (
    <svg
      className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#f28b82]"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
      />
    </svg>
  );
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isError = message.role === "assistant" && message.variant === "error";
  const sources = message.sources?.filter(Boolean) ?? [];

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div className="flex max-w-[min(100%,36rem)] flex-col gap-2">
        <div
          className={
            isUser
              ? "rounded-2xl rounded-tr-[4px] bg-[#1a73e8] px-4 py-3 text-sm leading-relaxed text-white"
              : isError
                ? "flex gap-2 rounded-2xl rounded-tl-[4px] border-[0.5px] border-[rgba(217,101,112,0.3)] bg-[rgba(217,101,112,0.12)] px-4 py-3 text-sm leading-relaxed text-[#f28b82]"
                : "rounded-2xl rounded-tl-[4px] border-[0.5px] border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.05)] px-4 py-3 text-sm leading-relaxed text-white/90"
          }
        >
          {isError ? (
            <span className="flex gap-2">
              <WarningIcon />
              <span>{message.content}</span>
            </span>
          ) : (
            message.content
          )}
        </div>

        {!isUser && !isError && sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-0.5">
            {sources.map((src, i) => (
              <span
                key={`${src}-${i}`}
                className="inline-flex max-w-full items-center rounded-full bg-[rgba(66,133,244,0.12)] px-2.5 py-0.5 text-[11px] font-medium text-[#8ab4f8]"
              >
                <span className="truncate">{src}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
