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
import {
  Input,
} from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Separator,
} from "@/components/ui/separator";
import { Loader2, Plus, AlertTriangle, CheckCircle } from "lucide-react";
import { cn } from "@/components/ui/cn";

export default function LearningPathsPage() {
  const t = useTranslations();
  const { session: authSession } = useSession();
  const [paths, setPaths] = React.useState<Array<any>>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [newTitle, setNewTitle] = React.useState<string>("");
  const [creating, setCreating] = React.useState<boolean>(false);

  const studentId = authSession.user?.id;

  const loadPaths = async () => {
    if (!studentId) return;
    try {
      const res = await aiService.lpList();
      setPaths(res || []);
    } catch (e: any) {
      setError(e.message || "Failed to load learning paths");
    } finally {
      setLoading(false);
    }
  };

  const createPath = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || creating) return;
    setCreating(true);
    try {
      const res = await aiService.lpCreate({
        title: newTitle,
        subject_id: undefined,
        target_topic_id: undefined,
        difficulty: "medium",
        steps: [],
      });
      setPaths((prev) => [...prev, res]);
      setNewTitle("");
    } catch (e: any) {
      setError(e.message || "Failed to create learning path");
    } finally {
      setCreating(false);
    }
  };

  const deletePath = async (id: string) => {
    if (!confirm(t("confirm_delete") || "Delete this learning path?")) return;
    try {
      await aiService.lpDelete(id);
      setPaths((prev) => prev.filter((p) => p.id !== id));
    } catch (e: any) {
      setError(e.message || "Failed to delete path");
    }
  };

  const completeStep = async (pathId: string, stepId: string) => {
    try {
      await aiService.lpCompleteStep(pathId, stepId, { score: 100 });
      await loadPaths();
    } catch (e: any) {
      setError(e.message || "Failed to complete step");
    }
  };

  React.useEffect(() => {
    loadPaths();
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

  const statusColor: Record<string, string> = {
    active: "border-blue/50 bg-blue/5 text-blue-700",
    completed: "border-green/50 bg-green/5 text-green-700",
    paused: "border-amber/50 bg-amber/5 text-amber-700",
    archived: "border-muted bg-muted text-muted-foreground",
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t("learning_paths") || "Learning Paths"}</h1>
          <p className="text-muted-foreground">
            {t("learning_paths_desc") || "Personalized routes to master your target topics."}
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          <span className="ml-2 text-sm text-destructive">{error}</span>
        </div>
      )}

      <form onSubmit={createPath} className="flex gap-2 max-w-md">
        <Input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder={t("new_path_title") || "New learning path title..."}
          disabled={creating}
        />
        <Button type="submit" disabled={creating || !newTitle.trim()}>
          {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
        </Button>
      </form>

      <Separator />

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("title") || "Title"}</TableHead>
              <TableHead>{t("difficulty") || "Difficulty"}</TableHead>
              <TableHead>{t("status") || "Status"}</TableHead>
              <TableHead>{t("progress") || "Progress"}</TableHead>
              <TableHead className="text-right">{t("actions") || "Actions"}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paths.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  {t("no_paths") || "No learning paths yet. Create one to get started."}
                </TableCell>
              </TableRow>
            )}
            {paths.map((path) => (
              <TableRow key={path.id}>
                <TableCell className="font-medium">{path.title}</TableCell>
                <TableCell>{path.difficulty || "—"}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn("border", statusColor[path.status] || "")}>
                    {path.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="w-24 bg-muted rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-primary"
                      style={{ width: `${Math.max(0, Math.min(100, Number(path.progress || 0)))}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {Number(path.progress || 0).toFixed(0)}%
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    onClick={() => deletePath(path.id)}
                    variant="destructive"
                  >
                    <AlertTriangle className="h-4 w-4 mr-1" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {paths.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t("path_details") || "Path Details"}</CardTitle>
            <CardDescription>
              {t("select_path") || "Select a path above to view its steps and progress."}
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  );
}
