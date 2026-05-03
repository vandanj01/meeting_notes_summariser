import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from '../../components/Sidebar';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Summarise Meeting Transcripts",
  description: "Locally deployed AI agent to parse meeting transcripts through Microsoft's phi3 model on Ollama",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex h-screen bg-gray-50 overflow-hidden">
        <Sidebar />
        <main className = "flex-1 h-screen oveflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
