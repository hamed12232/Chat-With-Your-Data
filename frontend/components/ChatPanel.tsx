"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble, { type Message } from "./MessageBubble";
import IndexModal from "./IndexModal";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isChatReplyBody(value: unknown): value is { reply: string } {
  return (
    isRecord(value) &&
    typeof value.reply === "string"
  );
}

function shortErrorFromBody(body: unknown): string {
  if (!isRecord(body)) return "Request failed.";
  const { detail } = body;
  if (typeof detail === "string") {
    const t = detail.trim();
    return t.length > 180 ? `${t.slice(0, 177)}…` : t;
  }
  if (Array.isArray(detail)) {
    const first = detail[0];
    if (isRecord(first)) {
      const msg = first.msg;
      if (typeof msg === "string" && msg.trim()) {
        const t = msg.trim();
        return t.length > 180 ? `${t.slice(0, 177)}…` : t;
      }
    }
    return "Invalid request.";
  }
  return "Something went wrong.";
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }

  async function sendMessage() {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMsg: Message = { role: "user", content: trimmed };
    setMessages((prev: Message[]) => [...prev, userMsg]);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsLoading(true);

    try {
      const res = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });

      let data: unknown;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      let assistantContent: string;
      if (res.ok && isChatReplyBody(data)) {
        assistantContent = data.reply;
      } else {
        assistantContent = res.ok
          ? "Unexpected response from server."
          : shortErrorFromBody(data);
      }

      const assistantMsg: Message = {
        role: "assistant",
        content: assistantContent,
      };
      setMessages((prev: Message[]) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev: Message[]) => [
        ...prev,
        {
          role: "assistant",
          content: "Could not reach the server.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  }

  const inputDisabled = isLoading;
  const sendDisabled = !input.trim() || isLoading;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="messages-scroll min-h-0 flex-1 overflow-y-auto px-4 py-6 md:px-8">
        {messages.length === 0 ? (
          <div className="flex h-full min-h-[40vh] flex-col items-center justify-center text-center">
            <p className="max-w-md text-sm text-gray-400">
              Index a document and start asking questions.
            </p>
          </div>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-5 pb-4">
            {messages.map((msg, index) => (
              <MessageBubble key={`${msg.role}-${index}`} message={msg} />
            ))}

            {isLoading && (
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">
                  AI
                </div>
                <div className="flex gap-1 rounded-2xl rounded-bl-sm border border-surface-border bg-surface-raised px-4 py-3">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-500"
                      style={{ animationDelay: `${i * 120}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="flex-shrink-0 border-t border-surface-border bg-surface-raised">
        <div className="mx-auto max-w-2xl px-4 py-4">
          <div className="flex items-end gap-2 rounded-2xl border border-surface-border bg-surface px-4 py-3 transition focus-within:border-accent/50">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={inputDisabled}
              placeholder="Ask a question…"
              className="flex-1 resize-none bg-transparent text-sm text-white outline-none placeholder:text-gray-500 disabled:cursor-not-allowed disabled:opacity-60"
            />
            <button
              type="button"
              onClick={() => void sendMessage()}
              disabled={sendDisabled}
              className="mb-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-accent text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Send"
            >
              <svg className="h-4 w-4 -rotate-90" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0-7 7m7-7 7 7" />
              </svg>
            </button>
          </div>

          <div className="mt-2 flex items-center justify-center">
            <button
              type="button"
              onClick={() => setShowModal(true)}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-gray-500 transition hover:bg-surface-border hover:text-gray-300"
            >
              <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
                <path d="M2.75 2A1.75 1.75 0 0 0 1 3.75v8.5C1 13.216 1.784 14 2.75 14h10.5A1.75 1.75 0 0 0 15 12.25v-5.5a.75.75 0 0 0-.22-.53l-4-4A.75.75 0 0 0 10.25 2H2.75Z" />
              </svg>
              Index Documents
            </button>
          </div>
        </div>
      </div>

      {showModal && <IndexModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
