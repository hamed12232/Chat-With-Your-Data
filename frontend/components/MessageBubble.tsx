"use client";

import { useId } from "react";

export type Role = "user" | "assistant";

export interface Message {
  id: string;
  role: Role;
  content: string;
  isError?: boolean;
  sources?: string[];
}

function SparkleIcon({ className }: { className?: string }) {
  const gid = useId().replace(/:/g, "");
  return (
    <svg
      className={`drop-shadow-[0_0_10px_rgba(34,211,238,0.3)] ${className ?? ""}`}
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <defs>
        <linearGradient id={`lumo-spark-${gid}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#22d3ee" />
        </linearGradient>
      </defs>
      <path d="M12 3l1.35 5.4L18.75 12l-5.4 1.35L12 18.75l-1.35-5.4L5.25 12l5.4-1.35L12 3z" fill={`url(#lumo-spark-${gid})`} />
    </svg>
  );
}

function AssistantActions() {
  const btn =
    "flex h-8 w-8 items-center justify-center rounded-full text-[#89a3c9] transition hover:bg-cyan-400/10 hover:text-[#5ce1e6]";
  return (
    <div className="mt-2 flex items-center gap-0.5 opacity-75 transition hover:opacity-100">
      <button type="button" className={btn} aria-label="Good response" title="Good response">
        <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.25c.806 0 1.533-.446 2.1-1.08l2.59-3.24a2.751 2.751 0 0 1 4.215 0l2.59 3.24c.567.634 1.294 1.08 2.1 1.08H18.75c-.806 0-1.533.446-2.1 1.08l-2.59 3.24a2.751 2.751 0 0 1-4.215 0l-2.59-3.24c-.567-.634-1.294-1.08-2.1-1.08h-3.75Z" />
        </svg>
      </button>
      <button type="button" className={btn} aria-label="Bad response" title="Bad response">
        <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17.367 13.75c-.806 0-1.533.446-2.1 1.08l-2.59 3.24a2.751 2.751 0 0 1-4.215 0l-2.59-3.24c-.567-.634-1.294-1.08-2.1-1.08H5.25c.806 0 1.533-.446 2.1-1.08l2.59-3.24a2.751 2.751 0 0 1 4.215 0l2.59 3.24c.567.634 1.294 1.08 2.1 1.08h3.75Z" />
        </svg>
      </button>
      <button type="button" className={btn} aria-label="Regenerate" title="Regenerate">
        <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M16.023 9.348h4.992v-.001M5.978 19.566c.61.609 1.545 1.146 2.652 1.09 1.165-.063 2.268-.727 3.086-1.572l.08-.08M5.978 4.434c.61-.609 1.545-1.146 2.652-1.09 1.165.063 2.268.727 3.086 1.572l3.114 3.114M19.566 18.022v4.992h-.001M4.434 5.978V.986h-.001"
          />
        </svg>
      </button>
      <button type="button" className={btn} aria-label="Copy" title="Copy">
        <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.987 1.022 2.11 2.126.048.39.053.794.053 1.218v6.75a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 18v-6.75c0-.424.005-.828.053-1.218.123-1.104 1.01-1.998 2.11-2.126.639-.074 1.281-.135 1.927-.184"
          />
        </svg>
      </button>
      <button type="button" className={btn} aria-label="More" title="More">
        <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
        </svg>
      </button>
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isError = message.isError === true;

  if (isUser) {
    return (
      <div className="flex w-full justify-end">
        <div className="max-w-[min(85%,520px)] rounded-full border border-cyan-400/12 bg-[#061428]/90 px-4 py-2.5 text-[15px] leading-snug text-[#e8f4ff] shadow-[0_0_24px_rgba(34,211,238,0.06),inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-sm">
          {message.content}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex w-full justify-start gap-3">
        <div className="mt-0.5 flex-shrink-0">
          <SparkleIcon className="opacity-45" />
        </div>
        <div className="min-w-0 flex-1 border-l-2 border-red-400/35 pl-3 text-[15px] leading-relaxed text-[#fca5a5]">
          <p className="flex gap-2">
            <span className="inline-flex flex-shrink-0" aria-hidden>
              <svg className="mt-0.5 h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
              </svg>
            </span>
            <span>{message.content}</span>
          </p>
        </div>
      </div>
    );
  }

  const chips = message.sources?.filter(Boolean) ?? [];

  return (
    <div className="flex w-full justify-start gap-3">
      <div className="mt-0.5 flex-shrink-0">
        <SparkleIcon />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[15px] leading-[1.65] text-[#e8f4ff]">{message.content}</div>
        {chips.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {chips.map((label, i) => (
              <span
                key={`${label}-${i}`}
                className="inline-flex max-w-full truncate rounded-full border border-cyan-400/15 bg-cyan-400/10 px-2.5 py-0.5 text-[11px] font-medium text-[#7dd3fc]"
                title={label}
              >
                {label}
              </span>
            ))}
          </div>
        )}
        <AssistantActions />
      </div>
    </div>
  );
}
