"use client";

import { useRef, useState } from "react";

interface IndexModalProps {
  onClose: () => void;
}

type UploadState = "idle" | "uploading" | "success" | "error";

export default function IndexModal({ onClose }: IndexModalProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setFiles(Array.from(e.dataTransfer.files));
    }
  }

  async function handleUpload() {
    if (files.length === 0) return;
    setUploadState("uploading");
    setErrorMessage("");

    const formData = new FormData();
    files.forEach((f) => formData.append("file", f));

    try {
      const res = await fetch(`${apiUrl}/index/`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail ?? `Server error ${res.status}`);
      }
      setUploadState("success");
    } catch (err: unknown) {
      setUploadState("error");
      setErrorMessage(err instanceof Error ? err.message : "Upload failed");
    }
  }

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-md rounded-2xl border border-surface-border bg-surface-raised p-6 shadow-2xl">
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Index documents</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-400 transition hover:bg-surface-border hover:text-white"
          >
            <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
              <path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z" />
            </svg>
          </button>
        </div>

        {/* Drop zone */}
        {uploadState !== "success" && (
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed border-surface-border bg-surface/60 px-6 py-10 transition hover:border-accent/50 hover:bg-surface"
          >
            <svg className="h-8 w-8 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
            </svg>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-300">
                Drop PDF files here, or{" "}
                <span className="text-accent underline underline-offset-2">browse</span>
              </p>
              <p className="mt-1 text-xs text-gray-500">PDF, TXT — up to 50 MB each</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        )}

        {/* Selected files list */}
        {files.length > 0 && uploadState !== "success" && (
          <ul className="mt-4 space-y-1">
            {files.map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-xs text-gray-400">
                <svg className="h-3.5 w-3.5 flex-shrink-0 text-accent" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M3.75 2A1.75 1.75 0 0 0 2 3.75v8.5C2 13.216 2.784 14 3.75 14h8.5A1.75 1.75 0 0 0 14 12.25v-5.5a.75.75 0 0 0-.22-.53l-4-4A.75.75 0 0 0 9.25 2H3.75Z" />
                </svg>
                <span className="truncate">{f.name}</span>
                <span className="ml-auto flex-shrink-0 text-gray-600">
                  {(f.size / 1024).toFixed(0)} KB
                </span>
              </li>
            ))}
          </ul>
        )}

        {/* Success state */}
        {uploadState === "success" && (
          <div className="flex flex-col items-center gap-3 py-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10 text-green-400">
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <p className="text-sm font-medium text-white">Documents indexed</p>
            <p className="text-xs text-gray-400">Your files are ready to query.</p>
          </div>
        )}

        {/* Error message */}
        {uploadState === "error" && (
          <p className="mt-3 text-xs text-red-400">{errorMessage}</p>
        )}

        {/* Actions */}
        <div className="mt-5 flex justify-end gap-2">
          {uploadState === "success" ? (
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
                onClick={handleUpload}
                disabled={files.length === 0 || uploadState === "uploading"}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
              >
                {uploadState === "uploading" ? "Indexing…" : "Index documents"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
