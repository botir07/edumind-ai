"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { aiService } from "@/lib/ai";
import { Loader2, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function AIAnalyticsPage() {
  const t = useTranslations();
  const { session: authSession } = useSession();
  const [analytics, setAnalytics] = React.useState<any>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  const userId = authSession.user?.id;

  React.useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    aiService.analyticsStudent(userId)
      .then((res) => { setAnalytics(res); })
      .catch((e: any) => setError(e.message || "Failed to load analytics"))
      .finally(() => setLoading(false));
  }, [userId]);

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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("learning_analytics") || "Learning Analytics"}</h1>
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("average_score") || "Average Score"}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.average_score !== null ? analytics.average_score.toFixed(1) : "—"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("grade_count") || "Grades"}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics?.grade_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("submissions") || "Submissions"}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics?.submission_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("active_paths") || "Active Paths"}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics?.active_paths}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
