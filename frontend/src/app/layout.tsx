import type { Metadata } from "next";

import { cormorant, jost } from "@/fonts";

import "./globals.css";

// Datos que ven Google y las redes sociales (se ampliarán en la fase de SEO)
export const metadata: Metadata = {
  title: "Nahluu Jewelry · Tesoros del océano",
  description:
    "Joyas hechas a mano en Gran Canaria en plata 925 chapada en oro. Collares y pendientes con alma de océano.",
};

// Plantilla común a todas las páginas
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // Por ahora en español; en la fase 3 el idioma dependerá de la ruta (/es o /en)
    <html lang="es" className={`${cormorant.variable} ${jost.variable}`}>
      <body>{children}</body>
    </html>
  );
}
