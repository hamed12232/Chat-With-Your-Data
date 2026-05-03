"use client";

import { useRef, useState } from "react";

interface IndexModalProps {
  onClose: () => void;
}

type UploadStatus = "idle" | "uploading" | "success" | "error";

export default function IndexModal({ onClose }: IndexModalProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dropError, setDropError] = useState<string>("");
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [chunks, setChunks] = useState<number>(0);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  function isPdf(f: File): boolean {
    return f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf");
  }

  function selectFile(f: File) {
    if (!isPdf(f)) {
      setDropError("Only PDF files are accepted.");
      setFile(null);
      return;
    }
    setDropError("");
    setFile(f);
    setStatus("idle");
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    if (picked) selectFile(picked);
    // Reset input so re-selecting the same file fires onChange again
    e.target.value = "";
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) selectFile(dropped);
  }

  async function handleStartIndexing() {
    if (!file || status === "uploading") return;

    setStatus("uploading");
    setDropError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${apiUrl}/index/`, {
        method: "POST",
        body: formData,
      });

      const data: { status?: string; chunks?: number; detail?: string } =
        await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data?.detail ?? `Server error ${res.status}`);
      }

      setChunks(data.chunks ?? 0);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose();
  }

  const canIndex = file !== null && status !== "uploading";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-md rounded-2xl border border-surface-border bg-surface-raised p-6 shadow-2xl">

        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Index Documents</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1 text-gray-400 transition hover:bg-surface-border hover:text-white"
          >
            <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
              <path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z" />
            </svg>
          </button>
        </div>

        {/* Drop zone — hidden once upload succeeds */}
        {status !== "success" && (
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed border-surface-border bg-surface/60 px-6 py-10 transition hover:border-accent/50 hover:bg-surface"
          >
            <svg
              className="h-8 w-8 text-gray-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"
              />
            </svg>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-300">
                Drop a PDF here, or{" "}
                <span className="text-accent underline underline-offset-2">browse</span>
              </p>
              <p className="mt-1 text-xs text-gray-500">PDF files only — up to 50 MB</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        )}

        {/* Non-PDF drop error */}
        {dropError && (
          <p className="mt-2 text-xs text-red-400">{dropError}</p>
        )}

        {/* Selected file name */}
        {file && status !== "success" && (
          <div className="mt-3 flex items-center gap-2 rounded-lg border border-surface-border bg-surface px-3 py-2">
            <svg
              className="h-4 w-4 flex-shrink-0 text-accent"
              viewBox="0 0 16 16"
              fill="currentColor"
            >
              <path d="M3.75 2A1.75 1.75 0 0 0 2 3.75v8.5C2 13.216 2.784 14 3.75 14h8.5A1.75 1.75 0 0 0 14 12.25v-5.5a.75.75 0 0 0-.22-.53l-4-4A.75.75 0 0 0 9.25 2H3.75Z" />
            </svg>
            <span className="truncate text-xs text-gray-300">{file.name}</span>
            <span className="ml-auto flex-shrink-0 text-xs text-gray-600">
              {(file.size / 1024).toFixed(0)} KB
            </span>
          </div>
        )}

        {/* Status section */}
        {status === "uploading" && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-surface-border bg-surface px-4 py-3">
            <svg
              className="h-4 w-4 flex-shrink-0 animate-spin text-accent"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                d="M12 3a9 9 0 1 0 9 9"
              />
            </svg>
            <p className="text-sm text-gray-300">Indexing your document...</p>
          </div>
        )}

        {status === "success" && (
          <div className="flex flex-col items-center gap-3 py-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10 text-green-400">
              <svg
                className="h-6 w-6"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <p className="text-sm font-medium text-white">
              Done! {chunks} chunk{chunks !== 1 ? "s" : ""} indexed successfully.
            </p>
          </div>
        )}

        {status === "error" && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3">
            <svg
              className="h-4 w-4 flex-shrink-0 text-red-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
              />
            </svg>
            <p className="text-sm text-red-400">Something went wrong. Please try again.</p>
          </div>
        )}

        {/* Actions */}
        <div className="mt-5 flex justify-end gap-2">
          {status === "success" ? (
            <button
              onClick={onClose}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-hover"
            >
              Done
            </button>
          ) : (
            <>
              <button
                onClick={onClose}
                className="rounded-lg px-4 py-2 text-sm text-gray-400 transition hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleStartIndexing}
                disabled={!canIndex}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
              >
                Start Indexing
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
