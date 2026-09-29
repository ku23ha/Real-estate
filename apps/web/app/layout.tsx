import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rethos | Deal underwriting",
  description: "Evidence-led real estate underwriting and decision intelligence.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
