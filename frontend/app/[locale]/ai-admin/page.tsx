"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { aiService } from "@/lib/ai";

export default function AIDashboardPage() {
  
  const [health, setHealth] = React.useState<any>(null);
  const [config, setConfig] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    Promise.all([aiService.health(), aiService.config()])
      .then(([h, c]) => { setHealth(h); setConfig(c); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-[400px]">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">AI Core Dashboard</h1>
        <p className="text-muted-foreground">Overview of AI Core components and status.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
        <Card>
          <CardHeader><CardTitle>System Prompt</CardTitle></CardHeader>
          <CardContent className="text-muted-foreground text-center py-8">Operational</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>RAG Engine</CardTitle></CardHeader>
          <CardContent className="text-muted-foreground text-center py-8">
            {config?.rag_enabled ? "Enabled" : "Disabled"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>MCP</CardTitle></CardHeader>
          <CardContent className="text-muted-foreground text-center py-8">
            {config?.mcp_enabled ? "Enabled" : "Disabled"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Cache</CardTitle></CardHeader>
          <CardContent className="text-muted-foreground text-center py-8">
            {config?.cache_enabled ? "Enabled" : "Disabled"}
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Components</CardTitle></CardHeader>
          <CardContent>
            {health && health.components ? (
              <ul className="text-sm space-y-2 text-muted-foreground">
                {Object.entries(health.components as Record<string, string>).map(([k, v]) => (
                  <li key={k} className="flex justify-between">
                    <span>{k}</span>
                    <span className="font-mono">{v}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground">No component data.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Configuration</CardTitle></CardHeader>
          <CardContent>
            {config ? (
              <ul className="text-sm space-y-2 text-muted-foreground">
                <li className="flex justify-between"><span>AI Core</span><span className="font-mono">{String(config.ai_core_enabled)}</span></li>
                <li className="flex justify-between"><span>Default LLM Provider</span><span className="font-mono">{String(config.default_llm_provider || "none")}</span></li>
                <li className="flex justify-between"><span>Providers</span><span className="font-mono">{String(config.providers?.length || 0)}</span></li>
              </ul>
            ) : (
              <p className="text-muted-foreground">No config data.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
