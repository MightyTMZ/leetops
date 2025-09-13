import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LeetOps - On-Call Engineering Assessment Platform",
  description: "The standardized benchmark for on-call engineering reliability. Practice real-world incident response scenarios at top tech companies.",
  keywords: ["engineering", "on-call", "incident response", "assessment", "simulation", "tech companies"],
  authors: [{ name: "LeetOps Team" }],
  openGraph: {
    title: "LeetOps - On-Call Engineering Assessment Platform",
    description: "The standardized benchmark for on-call engineering reliability",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
