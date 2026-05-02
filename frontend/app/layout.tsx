import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Chatbot — Chat With Your Data",
  description: "Retrieval-Augmented Generation chatbot powered by LangChain, Chroma, and GPT-4o.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-surface text-white antialiased">{children}</body>
    </html>
  );
}
