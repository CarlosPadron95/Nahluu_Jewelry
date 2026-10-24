import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier/flat";

const eslintConfig = defineConfig([
  // Reglas recomendadas por Next.js (rendimiento, accesibilidad y TypeScript)
  ...nextVitals,
  ...nextTs,
  // Desactiva las reglas de formato que ya se encarga Prettier
  prettier,
  // Carpetas que ESLint no revisa
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

export default eslintConfig;
