import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lumo AI — Chat with your data",
  description: "Lumo AI: retrieval-augmented assistant over your indexed documents.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="lumo-app h-full font-sans text-[#e8f4ff] antialiased">{children}</body>
    </html>
  );
}
