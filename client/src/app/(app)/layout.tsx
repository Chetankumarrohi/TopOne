import ".app/(app)/globals.css";

export const metadata = {
  title: "InvestiGenie",
  description: "AI-Native Wealth Operating System",
};

const themeInitializer = `
  (function () {
    try {
      var saved = localStorage.getItem("investigenie-theme");
      var theme = saved === "light" ? "light" : "dark";
      document.documentElement.dataset.theme = theme;
    } catch (_) {
      document.documentElement.dataset.theme = "dark";
    }
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: themeInitializer,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}