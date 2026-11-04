"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { aiService } from "@/lib/ai";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Separator,
} from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Loader2, CheckCircle, AlertTriangle, HelpCircle } from "lucide-react";
import { cn } from "@/components/ui/cn";

export default function KnowledgeMapPage() {
  const t = useTranslations();
  const { session: authSession } = useSession();
  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  const studentId = authSession.user?.id;

  React.useEffect(() => {
    if (!studentId) return;
    aiService
      .kmGetMap(studentId)
      .then((res) => {
        setData(res);
      })
      .catch((e: any) => setError(e.message || "Failed to load knowledge map"))
      .finally(() => setLoading(false));
  }, [studentId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin mb-2" />
        <p className="text-muted-foreground">{t("loading") || "Loading..."}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
        <AlertTriangle className="h-4 w-4 text-destructive" />
        <span className="ml-2 text-sm text-destructive">{error}</span>
      </div>
    );
  }

  const states = data?.mastery_states || [];
  const subjects = data?.subjects || [];
  const topics = data?.topics || [];
  const skills = data?.skills || [];

  const statusColor: Record<string, string> = {
    NOT_STARTED: "border-input bg-muted",
    LEARNING: "border-blue/50 bg-blue/5",
    NEEDS_PRACTICE: "border-amber/50 bg-amber/5",
    DEVELOPING: "border-blue/50 bg-blue/5",
    MASTERED: "border-green/50 bg-green/5",
  };

  const statusLabel: Record<string, string> = {
    NOT_STARTED: t("not_started") || "Not Started",
    LEARNING: t("learning") || "Learning",
    NEEDS_PRACTICE: t("needs_practice") || "Needs Practice",
    DEVELOPING: t("developing") || "Developing",
    MASTERED: t("mastered") || "Mastered",
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t("knowledge_map") || "Knowledge Map"}</h1>
          <p className="text-muted-foreground">
            {t("knowledge_map_desc") || "Track your mastery across subjects, topics, and skills."}
          </p>
        </div>
        <Button
          onClick={() => aiService.kmGetMasteryAlgorithm().then((r) => console.log(r))}
          size="sm"
          variant="outline"
        >
          <HelpCircle className="h-4 w-4 mr-2" />
          {t("algorithm") || "Algorithm"}
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("subjects") || "Subjects"}</CardTitle>
            <CardDescription className="text-xs">{subjects.length}</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {subjects.map((s: any) => (
                <li key={s.id} className="flex justify-between">
                  <span className="text-muted-foreground">{s.name}</span>
                  <span className="text-xs font-mono">{s.code}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("topics") || "Topics"}</CardTitle>
            <CardDescription className="text-xs">{topics.length}</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {topics.map((tpc: any) => (
                <li key={tpc.id} className="flex justify-between">
                  <span className="text-muted-foreground">{tpc.name}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("skills") || "Skills"}</CardTitle>
            <CardDescription className="text-xs">{skills.length}</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {skills.map((sk: any) => (
                <li key={sk.id} className="flex justify-between">
                  <span className="text-muted-foreground">{sk.name}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("mastery_states") || "Mastery States"}</CardTitle>
          <CardDescription>
            {t("mastery_desc") || "Computed transparently from real attempt data, not just school grades."}
          </CardDescription>
        </CardHeader>
        <Separator />
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("subject") || "Subject"}</TableHead>
                  <TableHead>{t("topic") || "Topic"}</TableHead>
                  <TableHead>{t("mastery_score") || "Mastery Score"}</TableHead>
                  <TableHead>{t("status") || "Status"}</TableHead>
                  <TableHead>{t("attempts") || "Attempts"}</TableHead>
                  <TableHead>{t("correct") || "Correct"}</TableHead>
                  <TableHead>{t("last_practiced") || "Last Practiced"}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {states.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                      {t("no_mastery_data") || "No mastery data yet. Start practicing to build your knowledge map."}
                    </TableCell>
                  </TableRow>
                )}
                {states.map((st: any) => (
                  <TableRow key={st.id}>
                    <TableCell>{st.subject_id || "—"}</TableCell>
                    <TableCell>{st.topic_id || "—"}</TableCell>
                    <TableCell>
                      <div className="w-20 bg-muted rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-primary"
                          style={{ width: `${Math.max(0, Math.min(100, Number(st.mastery_score || 0)))}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {Number(st.mastery_score || 0).toFixed(0)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={cn("border", statusColor[st.learning_status] || "")}>
                        {statusLabel[st.learning_status] || st.learning_status}
                      </Badge>
                    </TableCell>
                    <TableCell>{st.attempt_count}</TableCell>
                    <TableCell>{st.correct_answers}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {st.last_practiced_at || "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card className="border border-amber/50 bg-amber/5">
        <CardHeader className="flex flex-row items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <CardTitle className="text-sm">{t("estimate_note") || "Important Note"}</CardTitle>
        </CardHeader>
        <CardDescription className="text-sm">
          {t("mastery_estimate_note") || "Mastery score is an estimate, not objective truth. It is computed from your real attempt data, not only from school grades. You and your teacher can see why a particular status was assigned."}
        </CardDescription>
      </Card>
    </div>
  );
}
