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
  title: "SlideKick | Research That Kicks!",
  description:
    "Your AI research sidekick that digs through knowledge graphs, crunches data, argues with itself, and delivers killer insights. No coffee breaks needed.",
  keywords: [
    "AI research",
    "knowledge graph",
    "LangGraph",
    "Neo4j",
    "strategic analysis",
    "RAG",
    "agentic AI",
    "SlideKick",
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
    title: "SlideKick - Research That Kicks!",
    description:
      "AI research sidekick with knowledge graphs, self-reflection, and killer insights",
    siteName: "SlideKick",
  },
  twitter: {
    card: "summary_large_image",
    title: "SlideKick - Research That Kicks!",
    description:
      "AI research sidekick with knowledge graphs, self-reflection, and killer insights",
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
