import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "AIDEB — AI-based Epilepsy Detection",
  description: "Sistem skrining dan analisis MRI otak untuk deteksi dini epilepsi berbasis kecerdasan buatan.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-dark-medis antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
