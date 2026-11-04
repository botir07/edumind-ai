"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import { DashboardGrid, StatCard } from "@/components/dashboard/shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, Users, GraduationCap, ShieldAlert } from "lucide-react";

export default function TeacherDashboard() {
  const t = useTranslations("dashboard");
  const { session } = useSession();
  const [stats, setStats] = React.useState<any>({});
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const org = session.memberships?.[0]?.organization_id;
    if (!org) { setLoading(false); return; }
    apiFetch(`/api/v1/analytics/school/${org}`)
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [session.memberships]);

  if (loading) return <div className="flex items-center justify-center min-h-[400px]">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Teacher Dashboard</h1>
          <p className="text-muted-foreground">Manage your classes and assignments.</p>
        </div>
      </div>
      <DashboardGrid>
        <StatCard title="Students" value={stats.student_count || 0} />
        <StatCard title="Average Score" value={stats.average_score != null ? stats.average_score.toFixed(1) : "—"} />
        <StatCard title="Classes" value={stats.class_count || 0} />
      </DashboardGrid>
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Quick actions</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2"><GraduationCap className="w-5 h-5" /><span>Gradebook</span></div>
            <div className="flex items-center gap-2"><BookOpen className="w-5 h-5" /><span>Homework</span></div>
            <div className="flex items-center gap-2"><ShieldAlert className="w-5 h-5" /><span>Attendance</span></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>{t("recentActivity") || "Recent activity"}</CardTitle></CardHeader>
          <CardContent className="h-64 overflow-y-auto text-sm">
            <p className="text-muted-foreground text-center py-10">No recent activity.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
