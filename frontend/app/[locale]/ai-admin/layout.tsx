"use client";

import * as React from "react";
import { useSession } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { cn } from "@/components/ui/cn";
import { LayoutDashboard, Settings, FileText, ShieldAlert, Terminal, Bot, Server } from "lucide-react";

const AI_ADMIN_ITEMS: Array<{ key: string; label: string; href: string; icon: any }> = [
  { key: "dashboard", label: "Dashboard", href: "/[locale]/ai-admin", icon: LayoutDashboard },
  { key: "providers", label: "Provider Configuration", href: "/[locale]/ai-admin/providers", icon: Settings },
  { key: "prompts", label: "Prompt Management", href: "/[locale]/ai-admin/prompts", icon: FileText },
  { key: "documents", label: "Document Management", href: "/[locale]/ai-admin/documents", icon: FileText },
  { key: "tools", label: "MCP Tools", href: "/[locale]/ai-admin/tools", icon: Bot },
  { key: "security", label: "Security Events", href: "/[locale]/ai-admin/security", icon: ShieldAlert },
  { key: "traces", label: "Trace Explorer", href: "/[locale]/ai-admin/traces", icon: Terminal },
];

export function AIAdminLayout({ children }: { children: React.ReactNode }) {
  const { session } = useSession();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <nav className="sticky top-0 z-50 h-14 border-b border-border bg-background/95 backdrop-blur flex items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2">
          <span className="font-bold tracking-tight text-navy">EduMind</span>
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">AI Core</span>
        </div>
        <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
          {AI_ADMIN_ITEMS.map((item) => (
            <a key={item.key} href={item.href} className="hover:text-primary transition-colors">
              {item.label}
            </a>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Button onClick={() => setSidebarOpen(!sidebarOpen)} size="sm" variant="outline">
            <Server className="w-4 h-4 mr-2" />
          </Button>
          <Button variant="destructive" size="sm" onClick={() => {}}>
            Logout
          </Button>
        </div>
      </nav>
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r border-border bg-background transform transition-transform duration-300",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          "md:relative md:translate-x-0 md:w-auto md:border-r-0 md:static"
        )}
      >
        <div className="flex h-full flex-col">
          <div className="h-12 border-b border-border flex items-center justify-between px-4">
            <span className="font-semibold">AI Core</span>
            <Button size="icon" variant="ghost" onClick={() => setSidebarOpen(false)}>
              <span className="sr-only">Close</span>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
            {AI_ADMIN_ITEMS.map((item) => (
              <a
                key={item.key}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </a>
            ))}
          </nav>
          <div className="p-4 border-t border-border">
            <div className="text-xs text-muted-foreground mb-3">
              {session.user?.full_name || session.user?.email || "Admin"}
            </div>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto bg-[#f1f5f9] dark:bg-[#0f172a] p-4 md:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
}
