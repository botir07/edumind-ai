"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { aiService } from "@/lib/ai";

export default function AIProvidersPage() {
  
  const [config, setConfig] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    aiService.config().then(setConfig).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-[400px]">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Provider Configuration</h1>
      <p className="text-muted-foreground">
        Language model and embedding providers. No provider is connected by default;
        connect one only via explicit authorization.
      </p>
      <Card>
        <CardHeader><CardTitle>Provider Status</CardTitle></CardHeader>
        <CardContent>
          <ul className="text-sm space-y-3 text-muted-foreground">
            <li className="flex justify-between">
              <span>AI Core Enabled</span>
              <span className="font-mono">{String(config?.ai_core_enabled)}</span>
            </li>
            <li className="flex justify-between">
              <span>Default LLM Provider</span>
              <span className="font-mono">{String(config?.default_llm_provider || "none")}</span>
            </li>
            <li className="flex justify-between">
              <span>Default Embedding Provider</span>
              <span className="font-mono">{String(config?.default_embedding_provider || "none")}</span>
            </li>
            <li className="flex justify-between">
              <span>Enabled Providers</span>
              <span className="font-mono">{String(config?.providers?.length || 0)}</span>
            </li>
          </ul>
          <p className="mt-4 text-xs text-muted-foreground">
            Provider API keys are never stored in the UI or source code; they are supplied
            at runtime via environment variables.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
