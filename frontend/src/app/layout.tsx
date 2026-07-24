import type { Metadata } from "next";
import "./globals.css";
import ToasterProvider from "@/components/ToasterProvider";

export const metadata: Metadata = {
  title: "BFSI Dispute Resolution Platform",
  description: "Enterprise banking dispute investigation and resolution system",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico" },
    ],
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ToasterProvider />
        {children}
      </body>
    </html>
  );
}
