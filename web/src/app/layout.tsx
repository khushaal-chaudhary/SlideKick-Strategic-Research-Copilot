import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Strategic Research Copilot | AI-Powered Research Analyst",
  description:
    "An AI research analyst that builds knowledge graphs, performs multi-step strategic analysis with self-reflection, and delivers insights. Built with LangGraph, Neo4j, and Next.js.",
  keywords: [
    "AI research",
    "knowledge graph",
    "LangGraph",
    "Neo4j",
    "strategic analysis",
    "RAG",
    "agentic AI",
  ],
  authors: [
    {
      name: "Khushaal Chaudhary",
      url: "https://khushaalchaudhary.com",
    },
  ],
  creator: "Khushaal Chaudhary",
  openGraph: {
    type: "website",
    locale: "en_US",
    title: "Strategic Research Copilot",
    description:
      "AI-powered research analyst with knowledge graphs and self-reflection",
    siteName: "Strategic Research Copilot",
  },
  twitter: {
    card: "summary_large_image",
    title: "Strategic Research Copilot",
    description:
      "AI-powered research analyst with knowledge graphs and self-reflection",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
