import type { Metadata } from "next";
import "./globals.css";
import { LanguageProvider } from "@/components/i18n/LanguageProvider";

export const metadata: Metadata = {
  title: "Hirfati — AI Product Listings for Moroccan Artisans",
  description:
    "Turn a product photo and a Darija voice note into a premium multilingual marketplace listing — instantly.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // AR is the default language → RTL by default; the provider keeps
  // <html lang/dir> in sync when the user switches.
  return (
    <html lang="ar" dir="rtl">
      <body className="min-h-screen bg-charcoal-950 antialiased">
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
