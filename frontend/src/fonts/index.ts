// Fuentes de la marca, alojadas en la propia web.
// Así no dependemos de Google Fonts: carga más rápida y sin
// enviar datos de los visitantes a terceros (mejor para el RGPD).
import localFont from "next/font/local";

// Cormorant Garamond: títulos, logo y nombres de producto
export const cormorant = localFont({
  src: [
    { path: "./cormorant-garamond-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "./cormorant-garamond-latin-400-italic.woff2", weight: "400", style: "italic" },
  ],
  variable: "--font-cormorant",
  display: "swap",
});

// Jost: texto, menús y botones
export const jost = localFont({
  src: [
    { path: "./jost-latin-300-normal.woff2", weight: "300", style: "normal" },
    { path: "./jost-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "./jost-latin-500-normal.woff2", weight: "500", style: "normal" },
  ],
  variable: "--font-jost",
  display: "swap",
});
