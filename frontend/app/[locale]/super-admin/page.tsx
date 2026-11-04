"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import { DashboardGrid, StatCard } from "@/components/dashboard/shell";

export default function SuperAdminDashboard() {
  const t = useTranslations("dashboard");
  const [orgs, setOrgs] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    apiFetch<{ data: any[]; meta: any }>("/api/v1/organizations")
      .then((d) => setOrgs(d.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-[400px]">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("dashboard") || "Super Admin Dashboard"}</h1>
      <div className="rounded-xl border border-border bg-background p-6">
        <h3 className="font-semibold mb-4">Organizations</h3>
        {orgs.length === 0 ? <p className="text-muted-foreground">No schools yet.</p> : (
          <table className="w-full text-sm border-collapse">
            <thead><tr className="border-b text-muted-foreground"><th className="pb-3 text-left">Name</th><th className="pb-3 text-left">Code</th></tr></thead>
            <tbody>
              {orgs.map((o) => (
                <tr key={o.id} className="border-b"><td className="py-3">{o.name}</td><td className="py-3 text-muted-foreground">{o.code}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
