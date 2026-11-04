import type { Metadata } from "next";
import { SessionProvider } from "@/lib/auth";
import { ThemeProvider } from "@/components/theme-provider";
import { Sidebar } from "@/components/layout/sidebar";
import { cn } from "@/components/ui/cn";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@/app/globals.css";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      retry: 1,
    },
  },
});

export default function RootLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale;

  return (
    <html lang={locale} dir="ltr" className="h-full">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0f172a" />
        <title>EduMind AI</title>
      </head>
      <body className="h-full bg-[#f8fafc] text-foreground antialiased">
        <QueryClientProvider client={queryClient}>
          <ThemeProvider defaultTheme="system">
            <SessionProvider>
              <div className="flex h-screen flex-col overflow-hidden">
                <nav className="sticky top-0 z-50 h-14 border-b border-border bg-background/95 backdrop-blur flex items-center justify-between px-4 sm:px-6 lg:px-8">
                  <div className="flex items-center gap-2">
                    <span className="font-bold tracking-tight text-navy">EduMind</span>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">AI</span>
                  </div>
                  <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
                    <a href="/dashboard" className="hover:text-primary transition-colors">
                      Dashboard
                    </a>
                    <a href="/students" className="hover:text-primary transition-colors">
                      Students
                    </a>
                  </div>
                  <div className="ml-auto flex items-center gap-3">
                    <button className="text-sm hover:text-primary transition-colors">Help</button>
                  </div>
                </nav>
                <div className="flex flex-1 overflow-hidden">
                  <Sidebar />
                  <main className="flex-1 overflow-y-auto bg-[#f1f5f9] dark:bg-[#0f172a] p-4 md:p-6 lg:p-8">
                    {children}
                  </main>
                </div>
              </div>
            </SessionProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}

export const metadata: Metadata = { title: "EduMind AI" };
