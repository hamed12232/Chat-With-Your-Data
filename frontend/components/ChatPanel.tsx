"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble, { type Message } from "./MessageBubble";
import IndexModal from "./IndexModal";

let idCounter = 0;
function uid() {
  return String(++idCounter);
}

const EMPTY_STATE_HINTS = [
  "What does this document say about…?",
  "Summarise the key findings.",
  "List all action items mentioned.",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }

  async function sendMessage() {
    const question = input.trim();
    if (!question || isLoading) return;

    const userMsg: Message = { id: uid(), role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsLoading(true);

    try {
      const res = await fetch(`${apiUrl}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      const assistantMsg: Message = {
        id: uid(),
        role: "assistant",
        content: res.ok ? data.answer : "Request failed.",
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "assistant", content: "Could not reach the API." },
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

  return (
    <div className="flex h-full flex-col">
      {/* ── Header ── */}
      <header className="flex flex-shrink-0 items-center justify-between border-b border-surface-border bg-surface-raised px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/20">
            <svg className="h-4 w-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white">Chat With Your Data</h1>
            <p className="text-[11px] text-gray-500">RAG · GPT-4o · Chroma</p>
          </div>
        </div>

        <a
          href={`${apiUrl}/health`}
          target="_blank"
          rel="noreferrer"
          className="rounded-md border border-surface-border px-3 py-1.5 text-xs text-gray-400 transition hover:border-accent/40 hover:text-accent"
        >
          /health
        </a>
      </header>

      {/* ── Message list ── */}
      <div className="messages-scroll flex-1 overflow-y-auto px-4 py-6 md:px-8">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-6 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
              <svg className="h-7 w-7 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            </div>
            <div>
              <p className="text-base font-medium text-white">Ask anything about your documents</p>
              <p className="mt-1 text-sm text-gray-500">
                Index a file first, then start chatting.
              </p>
            </div>
            <div className="flex flex-col gap-2">
              {EMPTY_STATE_HINTS.map((hint) => (
                <button
                  key={hint}
                  onClick={() => setInput(hint)}
                  className="rounded-xl border border-surface-border bg-surface-raised px-4 py-2.5 text-left text-sm text-gray-400 transition hover:border-accent/40 hover:text-gray-200"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-5">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/20 text-accent text-xs font-semibold">
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

      {/* ── Composer ── */}
      <div className="flex-shrink-0 border-t border-surface-border bg-surface-raised">
        <div className="mx-auto max-w-2xl px-4 py-4">
          <div className="flex items-end gap-2 rounded-2xl border border-surface-border bg-surface px-4 py-3 transition focus-within:border-accent/50">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents…"
              className="flex-1 resize-none bg-transparent text-sm text-white placeholder-gray-500 outline-none"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="mb-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-accent text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Send"
            >
              <svg className="h-4 w-4 -rotate-90" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0-7 7m7-7 7 7" />
              </svg>
            </button>
          </div>

          {/* Index documents trigger — lives just below the composer */}
          <div className="mt-2 flex items-center justify-center">
            <button
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

      {/* ── Index modal ── */}
      {showModal && <IndexModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
