import styles from "./page.module.css";

// Página provisional: sirve para comprobar que las fuentes y los colores
// de la marca funcionan. En la fase 3 se sustituye por la portada real.
export default function Home() {
  return (
    <main className={styles.pagina}>
      <p className={styles.rotulo}>Tesoros del océano</p>
      <h1 className={styles.logo}>NAHLUU</h1>
      <p className={styles.texto}>Joyas hechas a mano en Gran Canaria</p>
      <p className={styles.aviso}>La tienda abre muy pronto</p>
    </main>
  );
}
