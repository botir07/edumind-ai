"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { aiService } from "@/lib/ai";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Loader2, AlertTriangle, Send, HelpCircle } from "lucide-react";

const ERROR_TYPES: Array<{ id: string; label: string }> = [
  { id: "conceptual", label: "Conceptual" },
  { id: "calculation", label: "Calculation" },
  { id: "reading", label: "Reading" },
  { id: "logic", label: "Logic" },
  { id: "formula", label: "Formula" },
  { id: "misunderstanding", label: "Misunderstanding" },
  { id: "incomplete", label: "Incomplete" },
  { id: "repeated", label: "Repeated" },
];

export default function ErrorAnalysisPage() {
  const t = useTranslations();
  const { session: authSession } = useSession();
  const [history, setHistory] = React.useState<any>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [analyzing, setAnalyzing] = React.useState<boolean>(false);
  const [question, setQuestion] = React.useState<string>("");
  const [studentAnswer, setStudentAnswer] = React.useState<string>("");
  const [correctAnswer, setCorrectAnswer] = React.useState<string>("");
  const [result, setResult] = React.useState<any>(null);

  const studentId = authSession.user?.id;

  const loadHistory = async () => {
    if (!studentId) return;
    try {
      const res = await aiService.eaHistory();
      setHistory(res || []);
    } catch (e: any) {
      setError(e.message || "Failed to load error history");
    } finally {
      setLoading(false);
    }
  };

  const analyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || analyzing) return;
    setAnalyzing(true);
    setError(null);
    setResult(null);
    try {
      const res = await aiService.eaAnalyze({
        student_id: studentId,
        question,
        student_answer: studentAnswer || undefined,
        correct_answer: correctAnswer || undefined,
      });
      setResult(res);
      await loadHistory();
    } catch (e: any) {
      setError(e.message || "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  React.useEffect(() => {
    loadHistory();
  }, [studentId]);

  const typeLabel: Record<string, string> = {
    conceptual: "Conceptual Error",
    calculation: "Calculation Error",
    reading: "Reading Error",
    logic: "Logic Error",
    formula: "Formula Error",
    misunderstanding: "Misunderstanding",
    incomplete: "Incomplete Answer",
    repeated: "Repeated Error",
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t("error_analysis") || "Error Analysis"}</h1>
          <p className="text-muted-foreground">{t("error_analysis_desc") || "Understand why you made mistakes."}</p>
        </div>
        <Button size="sm" variant="outline" onClick={loadHistory}>
          <HelpCircle className="h-4 w-4 mr-2" />
          {t("error_categories") || "Error Categories"}
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          <span className="ml-2 text-sm text-destructive">{error}</span>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("analyze_answer") || "Analyze an Answer"}</CardTitle>
            <CardDescription>{t("analyze_desc") || "Enter a question and answers."}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={analyze} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("question") || "Question"}</label>
                <Input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={t("enter_question") || "e.g. Solve 2x + 3 = 7"} className="h-10" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("your_answer") || "Your Answer"}</label>
                <Input value={studentAnswer} onChange={(e) => setStudentAnswer(e.target.value)} placeholder={t("enter_your_answer") || "e.g. x = 5"} className="h-10" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("correct_answer") || "Correct Answer"}</label>
                <Input value={correctAnswer} onChange={(e) => setCorrectAnswer(e.target.value)} placeholder={t("enter_correct_answer") || "e.g. x = 2"} className="h-10" />
              </div>
              <Button type="submit" disabled={analyzing || !question.trim()}>
                {analyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                {analyzing ? " " + (t("analyzing") || "Analyzing...") : " " + (t("analyze") || "Analyze")}
              </Button>
            </form>
          </CardContent>
        </Card>

        {result && (
          <Card className="border border-blue/50 bg-blue/5">
            <CardHeader>
              <CardTitle>{t("analysis_result") || "Analysis Result"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{t("error_type") || "Error Type"}</div>
                  <div className="font-medium capitalize">{typeLabel[result.error_type] || result.error_type}</div>
                </div>
              </div>
              <Separator />
              <div className="text-sm text-foreground">{result.explanation || t("no_explanation") || "No explanation available."}</div>
            </CardContent>
          </Card>
        )}
      </div>

      <Separator />

      <Card>
        <CardHeader>
          <CardTitle>{t("error_history") || "Error History"}</CardTitle>
          <CardDescription>{t("history_desc") || "Your recent error analyses."}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("question") || "Question"}</TableHead>
                  <TableHead>{t("error_type") || "Error Type"}</TableHead>
                  <TableHead>{t("date") || "Date"}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center text-muted-foreground">{t("no_errors") || "No error history yet."}</TableCell>
                  </TableRow>
                ) : (
                  history.map((h: any) => (
                    <TableRow key={h.id}>
                      <TableCell className="text-sm truncate max-w-xs">{h.question}</TableCell>
                      <TableCell><Badge variant="outline" className="text-xs capitalize">{typeLabel[h.error_type] || h.error_type}</Badge></TableCell>
                      <TableCell className="text-xs text-muted-foreground">{h.created_at || "—"}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
