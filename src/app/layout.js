import "./globals.css";

export const metadata = {
  title: "Castell",
  description:
    "Simulazione 3D interattiva di un castell 4 de 8: una torre umana catalana con 90 atleti.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
