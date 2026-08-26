import "./globals.css";

export const metadata = {
  title: "TopOne",
  description: "AI-Native Wealth Operating System",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}