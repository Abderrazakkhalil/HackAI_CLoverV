import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hirfati — AI Product Listings for Moroccan Artisans",
  description:
    "Turn a product photo and a Darija voice note into a premium English marketplace listing — instantly.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-charcoal-950 antialiased">
        {children}
      </body>
    </html>
  );
}
