"use client";

export type Role = "user" | "assistant";

export interface Message {
  id: string;
  role: Role;
  content: string;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}
    >
      {/* Avatar — assistant only */}
      {!isUser && (
        <div className="mr-3 mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-accent text-xs font-semibold">
          AI
        </div>
      )}

      <div className="flex max-w-[72%] flex-col gap-1">
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-accent text-white rounded-br-sm"
              : "bg-surface-raised text-gray-100 rounded-bl-sm border border-surface-border"
          }`}
        >
          {message.content}
        </div>
      </div>

      {/* Avatar — user only */}
      {isUser && (
        <div className="ml-3 mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-accent text-white text-xs font-semibold">
          U
        </div>
      )}
    </div>
  );
}
