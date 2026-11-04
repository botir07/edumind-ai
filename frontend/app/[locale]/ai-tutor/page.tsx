"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { aiService } from "@/lib/ai";
import {
  Button,
} from "@/components/ui/button";
import {
  Input,
} from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Loader2, MessageCircle, Send, Check, AlertTriangle } from "lucide-react";
import { cn } from "@/components/ui/cn";

const MODES: Array<{ id: string; label: string }> = [
  { id: "explain", label: "Explain" },
  { id: "step_by_step", label: "Step-by-Step" },
  { id: "practice", label: "Practice" },
  { id: "quiz", label: "Quiz" },
  { id: "exam_preparation", label: "Exam Preparation" },
  { id: "homework_help", label: "Homework Help" },
  { id: "revision", label: "Revision" },
];

export default function AITutorPage() {
  const t = useTranslations();
  const { session: authSession } = useSession();
  const [mode, setMode] = React.useState<string>("explain");
  const [locale, setLocale] = React.useState<string>("uz");
  const [inputValue, setInputValue] = React.useState<string>("");
  const [messages, setMessages] = React.useState<Array<{ role: string; content: string }>>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [provider, setProvider] = React.useState<string>("none");

  const studentId = authSession.user?.id;

  const createSession = async () => {
    if (!studentId) return;
    try {
      const res = await aiService.tutorCreateSession({ mode, locale, title: "AI Tutor Session" });
      setSessionId(res.id);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Failed to create session");
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;
    if (!sessionId) await createSession();
    if (!sessionId) return;

    const userMsg = inputValue;
    setInputValue("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);
    setError(null);

    try {
      const res = await aiService.tutorChat({
        session_id: sessionId,
        message: userMsg,
        mode,
        locale,
        use_rag: false,
        use_mcp: false,
        use_cache: false,
        top_k: 10,
      });
      setMessages((prev) => [...prev, { role: "assistant", content: res.content }]);
      setProvider(res.provider || "none");
    } catch (e: any) {
      setError(e.message || "Tutor request failed");
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I couldn't process your request." }]);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (!sessionId) createSession();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t("ai_tutor") || "AI Tutor"}</h1>
          <p className="text-muted-foreground">
            {t("ai_tutor_desc") || "Your intelligent learning assistant. Ask questions, get explanations, and practice."}
          </p>
        </div>
        <div className="flex items-center gap-2 px-2 py-1 rounded-full border border-border bg-background">
          <span className="text-xs font-medium text-muted-foreground">Mode:</span>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="text-xs bg-transparent border-none focus:ring-0"
          >
            {MODES.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
          <span className="text-xs font-medium text-muted-foreground">|</span>
          <span className="text-xs font-medium text-muted-foreground">Lang:</span>
          <select
            value={locale}
            onChange={(e) => setLocale(e.target.value)}
            className="text-xs bg-transparent border-none focus:ring-0"
          >
            <option value="uz">Oʻzbekcha</option>
            <option value="ru">Русский</option>
            <option value="en">English</option>
          </select>
          <Badge variant={provider === "none" ? "destructive" : "secondary"}>
            {provider === "none" ? "AI not configured" : provider}
          </Badge>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          <span className="ml-2 text-sm text-destructive">{error}</span>
        </div>
      )}

      <div className="flex-1 min-h-[400px] max-h-[600px] overflow-y-auto border border-border rounded-lg bg-background p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <MessageCircle className="h-12 w-12 opacity-50" />
            <p className="mt-2">{t("ask_tutor") || "Ask me anything about your lessons..."}</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "flex gap-3 max-w-[85%]",
              msg.role === "user" ? "flex-row-reverse ml-auto" : "ml-0",
            )}
          >
            <div className="rounded-xl p-3 shadow-sm">
              {msg.role === "user" ? (
                <div className="bg-primary text-primary-foreground">{msg.content}</div>
              ) : (
                <div className="bg-background border border-border text-foreground">{msg.content}</div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm text-muted-foreground">{t("typing") || "Thinking..."}</span>
          </div>
        )}
      </div>

      <form onSubmit={sendMessage} className="flex gap-2 border-t border-border pt-4">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={t("ask_question") || "Type your question..."}
          disabled={loading}
          className="flex-1"
        />
        <Button type="submit" disabled={loading || !inputValue.trim()}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </form>

      {provider === "none" && (
        <Card className="border border-amber/50 bg-amber/5">
          <CardHeader className="flex flex-row items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <CardTitle className="text-sm">AI Provider Not Configured</CardTitle>
          </CardHeader>
          <CardDescription className="text-sm">
            No real AI Model Provider is connected. The tutor will return a clear message instead of fake answers.
            Contact an administrator to configure a provider.
          </CardDescription>
        </Card>
      )}
    </div>
  );
}
