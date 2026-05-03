"use client";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="mr-3 mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">
          AI
        </div>
      )}

      <div className="flex max-w-[72%] flex-col gap-1">
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "rounded-br-sm bg-accent text-white"
              : "rounded-bl-sm border border-surface-border bg-surface-raised text-gray-100"
          }`}
        >
          {message.content}
        </div>
      </div>

      {isUser && (
        <div className="ml-3 mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold text-white">
          U
        </div>
      )}
    </div>
  );
}
