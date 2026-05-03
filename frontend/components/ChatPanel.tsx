"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble, { type Message } from "./MessageBubble";
import IndexModal from "./IndexModal";

const SHELL_BG = "#0f1117";
const CARD_BG = "#12141a";
const TEXTAREA_MAX_LINES = 3;
const LINE_HEIGHT_PX = 22;

const SUGGESTION_CHIPS = [
  "What are the key points in the documents?",
  "Summarize the most important details.",
  "What should I know before taking action?",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isChatReplyBody(value: unknown): value is { reply: string } {
  return isRecord(value) && typeof value.reply === "string";
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

function NewChatIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.105 2.916a1.125 1.125 0 0 1-.26 1.243l-.923.852c-.303.28-.457.698-.457 1.122v1.118c0 .424.154.841.457 1.122l.923.852c.42.389.59.999.26 1.243l-1.105 2.916a1.125 1.125 0 0 1-1.37.49l-1.217-.456c-.355-.133-.75-.072-1.075.124-.073.044-.146.087-.22.127-.332.183-.582.495-.645.87l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.063-.374-.313-.686-.645-.87a7.52 7.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.075-.124l-1.217.456a1.125 1.125 0 0 1-1.37-.49l-1.105-2.916a1.125 1.125 0 0 1 .26-1.243l.923-.852c.303-.28.457-.698.457-1.122V9.75c0-.424-.154-.841-.457-1.122l-.923-.852a1.125 1.125 0 0 1-.26-1.243l1.105-2.916a1.125 1.125 0 0 1 1.37-.49l1.217.456c.355.133.75.072 1.075-.124.073-.044.146-.087.22-.127.332-.183.582-.495.645-.87l.213-1.281Z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

function AttachIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m18.375 12.625-5.25 5.25a4.5 4.5 0 1 1-6.364-6.364l7.5-7.5a3 3 0 1 1 4.243 4.243l-7.5 7.5a1.5 1.5 0 0 1-2.122-2.122l5.25-5.25"
      />
    </svg>
  );
}

function TypingBubble() {
  return (
    <div className="flex w-full justify-start">
      <div className="flex max-w-[min(100%,36rem)] flex-col">
        <div className="rounded-2xl rounded-tl-[4px] border-[0.5px] border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.05)] px-4 py-3">
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/40"
                style={{ animationDelay: `${i * 120}ms` }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  const showSuggestionChips =
    !isLoading &&
    (messages.length === 0 || messages[messages.length - 1]?.role === "assistant");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    const cap = LINE_HEIGHT_PX * TEXTAREA_MAX_LINES;
    el.style.height = `${Math.min(el.scrollHeight, cap)}px`;
  }

  async function sendMessage(textOverride?: string) {
    const trimmed = (textOverride ?? input).trim();
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

      let assistantMsg: Message;
      if (res.ok && isChatReplyBody(data)) {
        assistantMsg = {
          role: "assistant",
          content: data.reply,
        };
      } else {
        const content = res.ok
          ? "Unexpected response from server."
          : shortErrorFromBody(data);
        assistantMsg = {
          role: "assistant",
          content,
          variant: "error",
        };
      }
      setMessages((prev: Message[]) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev: Message[]) => [
        ...prev,
        {
          role: "assistant",
          content: "Could not reach the server.",
          variant: "error",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleChipClick(label: string) {
    setInput(label);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const cap = LINE_HEIGHT_PX * TEXTAREA_MAX_LINES;
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        cap,
      )}px`;
    }
    window.setTimeout(() => {
      void sendMessage(label);
    }, 0);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  }

  function handleNewChat() {
    setMessages([]);
    setInput("");
    setIsLoading(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  const inputDisabled = isLoading;
  const sendDisabled = !input.trim() || isLoading;

  return (
    <div
      className="flex h-full min-h-0 flex-col px-3 py-4 sm:px-5 sm:py-6"
      style={{ backgroundColor: SHELL_BG }}
    >
      <div
        className="mx-auto flex h-full min-h-0 w-full max-w-3xl flex-col overflow-hidden rounded-2xl border-[0.5px] border-[rgba(255,255,255,0.08)] shadow-[0_24px_80px_rgba(0,0,0,0.35)]"
        style={{ backgroundColor: CARD_BG }}
      >
        <header className="flex flex-shrink-0 items-center justify-between border-b-[0.5px] border-[rgba(255,255,255,0.07)] px-4 py-3 sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#4285f4] via-[#7c4dff] to-[#e040fb] shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]"
              aria-hidden
            />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="truncate text-[15px] font-semibold tracking-tight text-white">
                  RAG Assistant
                </h1>
                <span className="inline-flex flex-shrink-0 items-center rounded-full border-[0.5px] border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.06)] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white/55">
                  Knowledge Base
                </span>
              </div>
            </div>
          </div>
          <div className="flex flex-shrink-0 items-center gap-1">
            <button
              type="button"
              onClick={handleNewChat}
              className="rounded-lg p-2 text-white/50 transition hover:bg-white/[0.06] hover:text-white/85"
              aria-label="New chat"
            >
              <NewChatIcon />
            </button>
            <button
              type="button"
              className="rounded-lg p-2 text-white/50 transition hover:bg-white/[0.06] hover:text-white/85"
              aria-label="Settings"
            >
              <SettingsIcon />
            </button>
          </div>
        </header>

        <div className="messages-scroll min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-5">
          <div className="mx-auto flex min-h-[min(12rem,35vh)] max-w-2xl flex-col gap-4 pb-2">
            {messages.length === 0 && !isLoading ? (
              <div className="flex flex-1 flex-col items-center justify-center py-6 text-center">
                <p className="max-w-md text-sm text-white/40">
                  Index a document and start asking questions.
                </p>
              </div>
            ) : null}

            {messages.map((msg, index) => (
              <MessageBubble key={`${msg.role}-${index}-${msg.variant ?? ""}`} message={msg} />
            ))}

            {isLoading ? <TypingBubble /> : null}

            <div ref={bottomRef} />
          </div>
        </div>

        <div className="flex-shrink-0 border-t-[0.5px] border-[rgba(255,255,255,0.06)] bg-[rgba(15,17,23,0.45)] px-4 pb-4 pt-3 backdrop-blur-sm sm:px-5">
          {showSuggestionChips ? (
            <div className="mx-auto mb-3 flex max-w-2xl flex-wrap gap-2">
              {SUGGESTION_CHIPS.map((label) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => handleChipClick(label)}
                  disabled={isLoading}
                  className="rounded-full border-[0.5px] border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.04)] px-3 py-1.5 text-left text-xs text-white/55 transition hover:border-[rgba(255,255,255,0.16)] hover:bg-[rgba(255,255,255,0.07)] hover:text-white/75 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {label}
                </button>
              ))}
            </div>
          ) : null}

          <div className="mx-auto max-w-2xl">
            <div className="flex items-end gap-1 rounded-[24px] border-[0.5px] border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.03)] px-2 py-2 pl-3 transition focus-within:border-[rgba(66,133,244,0.5)] focus-within:shadow-[0_0_0_1px_rgba(66,133,244,0.12)]">
              <button
                type="button"
                onClick={() => setShowModal(true)}
                disabled={inputDisabled}
                className="mb-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-white/45 transition hover:bg-white/[0.06] hover:text-white/75 disabled:opacity-40"
                aria-label="Attach document"
              >
                <AttachIcon />
              </button>
              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                disabled={inputDisabled}
                placeholder="Ask a question…"
                className="mb-0.5 min-h-[22px] max-h-[66px] flex-1 resize-none border-0 bg-transparent py-2 text-sm leading-[22px] text-white outline-none ring-0 placeholder:text-white/35 disabled:cursor-not-allowed disabled:opacity-60"
                style={{ maxHeight: LINE_HEIGHT_PX * TEXTAREA_MAX_LINES }}
              />
              <button
                type="button"
                onClick={() => void sendMessage()}
                disabled={sendDisabled}
                className="mb-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-[#1a73e8] text-white transition enabled:hover:bg-[#1557b0] disabled:bg-white/15 disabled:text-white/35"
                aria-label="Send"
              >
                <svg className="h-4 w-4 -rotate-90" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0-7 7m7-7 7 7" />
                </svg>
              </button>
            </div>

            <p className="mt-2 text-center text-[11px] text-white/38">Answers grounded in indexed documents</p>

            <div className="mt-2 flex justify-center">
              <button
                type="button"
                onClick={() => setShowModal(true)}
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-white/40 transition hover:bg-white/[0.06] hover:text-white/65"
              >
                <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor" aria-hidden>
                  <path d="M2.75 2A1.75 1.75 0 0 0 1 3.75v8.5C1 13.216 1.784 14 2.75 14h10.5A1.75 1.75 0 0 0 15 12.25v-5.5a.75.75 0 0 0-.22-.53l-4-4A.75.75 0 0 0 10.25 2H2.75Z" />
                </svg>
                Index Documents
              </button>
            </div>
          </div>
        </div>
      </div>

      {showModal && <IndexModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
