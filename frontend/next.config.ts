import type { NextConfig } from "next";

// Cabeceras de seguridad que se envían con todas las páginas.
// La política de contenido (CSP) completa se añadirá en la fase de seguridad,
// cuando sepamos todos los servicios que carga la web (Stripe, Cloudinary...).
const cabecerasDeSeguridad = [
  // Obliga a usar HTTPS durante 2 años (el navegador lo ignora en localhost)
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  // Nadie puede meter nuestra web dentro de un iframe (evita el clickjacking)
  { key: "X-Frame-Options", value: "DENY" },
  // El navegador no intenta adivinar el tipo de los archivos
  { key: "X-Content-Type-Options", value: "nosniff" },
  // Al salir a otra web, solo se comparte el dominio, no la ruta completa
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // Desactivamos permisos que la tienda no necesita
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  // Opciones que trae por defecto Next.js 16
  cacheComponents: true,
  partialPrefetching: true,

  // No anunciar que la web está hecha con Next.js
  poweredByHeader: false,
  reactStrictMode: true,

  async headers() {
    return [{ source: "/:path*", headers: cabecerasDeSeguridad }];
  },
};

export default nextConfig;
