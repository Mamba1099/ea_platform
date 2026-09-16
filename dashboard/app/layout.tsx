import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EA Platform",
  description: "Trading automation operations dashboard"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
