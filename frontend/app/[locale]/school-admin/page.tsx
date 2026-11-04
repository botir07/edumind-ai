"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import { DashboardGrid, StatCard } from "@/components/dashboard/shell";

export default function SchoolAdminDashboard() {
  const t = useTranslations("dashboard");
  const { session } = useSession();
  const [stats, setStats] = React.useState<any>({});
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const org = session.memberships?.[0]?.organization_id;
    if (!org) { setLoading(false); return; }
    apiFetch(`/api/v1/analytics/school/${org}`)
      .then(setStats).catch(() => {}).finally(() => setLoading(false));
  }, [session.memberships]);

  if (loading) return <div className="flex items-center justify-center min-h-[400px]">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("dashboard") || "School Dashboard"}</h1>
      <DashboardGrid>
        <StatCard title="Students" value={stats.student_count || 0} />
        <StatCard title="Teachers" value={stats.teacher_count || 0} />
        <StatCard title="Classes" value={stats.class_count || 0} />
        <StatCard title="Avg. Score" value={stats.average_score != null ? stats.average_score.toFixed(1) : "—"} />
      </DashboardGrid>
    </div>
  );
}
