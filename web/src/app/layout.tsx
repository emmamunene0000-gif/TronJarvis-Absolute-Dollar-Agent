import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TRON | Absolute Dollar Agent",
  description: "Transparent TRON signal monitoring and risk-aware Deriv execution console.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
