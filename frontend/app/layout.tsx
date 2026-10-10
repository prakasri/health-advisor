import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
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
  title: "Health Advisor — understand your HbA1c",
  description:
    "Educational diabetes risk assessment: understand your HbA1c and get a personalised food, activity and check-up plan to discuss with your doctor.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:shadow"
        >
          Skip to content
        </a>
        <header className="no-print border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
            <Link href="/" className="text-lg font-bold text-teal-800">
              Health Advisor
            </Link>
            <span className="text-sm text-slate-600">Educational guidance · not a diagnosis</span>
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-3xl flex-1 px-4 py-8">
          {children}
        </main>
        <footer className="no-print border-t border-slate-200 bg-white">
          <p className="mx-auto max-w-3xl px-4 py-4 text-sm text-slate-600">
            For education and wellness only. Not medical advice. In an emergency, contact your local
            emergency number.
          </p>
        </footer>
      </body>
    </html>
  );
}
