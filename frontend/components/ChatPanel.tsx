"use client";

import Image from "next/image";
import { useEffect, useId, useRef, useState } from "react";
import lumoLogo from "@/Logo/image.png";
import MessageBubble, { type Message } from "./MessageBubble";
import IndexModal from "./IndexModal";

let idCounter = 0;
function uid() {
  return String(++idCounter);
}

const SUGGESTION_CHIPS = [
  "What does this document say about…?",
  "Summarise the key findings.",
  "List all action items mentioned.",
];

function pickSources(data: Record<string, unknown>): string[] | undefined {
  const raw = data.sources ?? data.citations ?? data.source_chunks ?? data.references;
  if (!Array.isArray(raw)) return undefined;
  const labels = raw
    .map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object" && "label" in item && typeof (item as { label: unknown }).label === "string") {
        return (item as { label: string }).label;
      }
      if (item && typeof item === "object" && "name" in item && typeof (item as { name: unknown }).name === "string") {
        return (item as { name: string }).name;
      }
      return null;
    })
    .filter((s): s is string => Boolean(s));
  return labels.length ? labels : undefined;
}

function TypingSparkle() {
  const gid = useId().replace(/:/g, "");
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden className="drop-shadow-[0_0_10px_rgba(34,211,238,0.35)]">
      <defs>
        <linearGradient id={`lumo-typing-${gid}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#22d3ee" />
        </linearGradient>
      </defs>
      <path d="M12 3l1.35 5.4L18.75 12l-5.4 1.35L12 18.75l-1.35-5.4L5.25 12l5.4-1.35L12 3z" fill={`url(#lumo-typing-${gid})`} />
    </svg>
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

  const LINE_HEIGHT_PX = 22;
  const MAX_TEXTAREA_HEIGHT = LINE_HEIGHT_PX * 3 + 8;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
  }

  async function sendMessage(overrideQuestion?: string) {
    const question = (overrideQuestion ?? input).trim();
    if (!question || isLoading) return;

    const userMsg: Message = { id: uid(), role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    if (overrideQuestion === undefined) {
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
    setIsLoading(true);

    try {
      const res = await fetch(`${apiUrl}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = (await res.json()) as Record<string, unknown>;
      const sources = res.ok ? pickSources(data) : undefined;

      let assistantMsg: Message;
      if (res.ok) {
        const content = typeof data.answer === "string" ? data.answer : "Request failed.";
        assistantMsg = { id: uid(), role: "assistant", content, sources };
      } else {
        assistantMsg = { id: uid(), role: "assistant", content: "Request failed.", isError: true };
      }
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: "assistant",
          content: "Could not reach the API.",
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function newChat() {
    if (isLoading) return;
    setMessages([]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  const iconBtn =
    "flex h-9 w-9 items-center justify-center rounded-full text-[#89a3c9] transition hover:bg-cyan-400/10 hover:text-[#e8f4ff] hover:shadow-[0_0_16px_rgba(34,211,238,0.12)]";

  return (
    <div className="relative flex h-full min-h-0 w-full min-w-0 flex-col">
      <header className="flex flex-shrink-0 items-center justify-between gap-3 pt-5 pb-2">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <Image
            src={lumoLogo}
            alt="Lumo AI"
            width={240}
            height={72}
            sizes="(max-width: 480px) 140px, 200px"
            className="h-9 shrink-0 w-auto max-w-[min(200px,52vw)] object-contain object-left drop-shadow-[0_0_14px_rgba(34,211,238,0.2)] sm:h-10"
            priority
          />
          <div className="h-8 w-px shrink-0 bg-gradient-to-b from-transparent via-cyan-400/30 to-transparent" aria-hidden />
          <div className="min-w-0 text-left">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#5c7399]">RAG</p>
            <p className="truncate text-[13px] font-medium leading-tight text-[#e8f4ff]">Indexed docs</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-0.5">
          <button
            type="button"
            onClick={newChat}
            disabled={isLoading}
            className={`${iconBtn} disabled:opacity-40`}
            aria-label="New chat"
            title="New chat"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
          </button>
          <button type="button" className={iconBtn} aria-label="Settings" title="Settings">
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.37.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.075-.124l-1.217.456a1.125 1.125 0 0 1-1.37-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281Z"
              />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
        </div>
      </header>

      <div className="messages-scroll flex min-h-0 flex-1 flex-col overflow-y-auto pb-2 pt-4">
        {messages.length === 0 && !isLoading ? (
          <div className="flex min-h-0 w-full flex-1 flex-col items-center justify-center px-2 py-12 text-center">
            <p className="max-w-sm text-[15px] leading-relaxed text-[#89a3c9]">
              Ask anything about your indexed documents — answers stay grounded in what you&apos;ve uploaded.
            </p>
          </div>
        ) : (
          <div className="flex w-full flex-col gap-8">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {isLoading && (
              <div className="flex justify-start gap-3" aria-live="polite" aria-busy>
                <div className="mt-0.5 flex-shrink-0">
                  <TypingSparkle />
                </div>
                <div className="flex items-center gap-1.5 pt-1">
                  <span className="typing-dot" />
                  <span className="typing-dot typing-dot-delay-1" />
                  <span className="typing-dot typing-dot-delay-2" />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="flex-shrink-0 pb-5 pt-2">
        {showSuggestionChips && (
          <div className="mb-3 flex flex-wrap gap-2">
            {SUGGESTION_CHIPS.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => sendMessage(chip)}
                disabled={isLoading}
                className="rounded-full border border-cyan-400/15 bg-[#061428]/80 px-3.5 py-2 text-left text-[13px] text-[#89a3c9] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-sm transition hover:border-cyan-400/30 hover:text-[#e8f4ff] hover:shadow-[0_0_20px_rgba(34,211,238,0.08)] disabled:opacity-50"
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        <div className="rounded-[28px] border border-cyan-400/15 bg-[#061428]/85 p-3 shadow-[0_12px_40px_rgba(0,0,0,0.35),inset_0_1px_0_rgba(255,255,255,0.05)] backdrop-blur-md transition-shadow focus-within:border-cyan-400/35 focus-within:shadow-[0_0_0_1px_rgba(34,211,238,0.25),0_12px_40px_rgba(0,0,0,0.35),0_0_28px_rgba(34,211,238,0.12)]">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask Lumo AI…"
            className="mb-2 min-h-[24px] max-h-[78px] w-full resize-none border-0 bg-transparent px-1 text-[15px] text-[#e8f4ff] outline-none ring-0 placeholder:text-[#5c7399]"
            style={{ lineHeight: `${LINE_HEIGHT_PX}px` }}
          />
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1">
              <button type="button" className={iconBtn} aria-label="Attach file" title="Attach">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </button>
              <button
                type="button"
                onClick={() => setShowModal(true)}
                className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[13px] text-[#89a3c9] transition hover:bg-cyan-400/10 hover:text-[#e8f4ff]"
              >
                <svg className="h-4 w-4 text-cyan-400/90" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M2.75 2A1.75 1.75 0 0 0 1 3.75v8.5C1 13.216 1.784 14 2.75 14h10.5A1.75 1.75 0 0 0 15 12.25v-5.5a.75.75 0 0 0-.22-.53l-4-4A.75.75 0 0 0 10.25 2H2.75Z" />
                </svg>
                Index Documents
              </button>
            </div>
            <button
              type="button"
              onClick={() => sendMessage()}
              disabled={!input.trim() || isLoading}
              className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-[#0f2844] text-white shadow-none transition enabled:bg-gradient-to-br enabled:from-[#2563eb] enabled:to-[#0891b2] enabled:shadow-[0_4px_20px_rgba(37,99,235,0.45)] enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:text-[#5c7399] disabled:hover:brightness-100"
              aria-label="Send"
            >
              <svg className="h-5 w-5 -rotate-90" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0-7 7m7-7 7 7" />
              </svg>
            </button>
          </div>
        </div>

        <p className="mt-3 text-center text-[12px] leading-snug text-[#5c7399]">
          Answers grounded in indexed documents. AI can make mistakes — check important details.
        </p>
      </div>

      {showModal && <IndexModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
