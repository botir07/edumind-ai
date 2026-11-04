"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";

export default function ParentDashboard() {
  const t = useTranslations("dashboard");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("dashboard") || "Parent Dashboard"}</h1>
      <p className="text-muted-foreground">Overview of your children's progress.</p>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-border bg-background p-6 text-muted-foreground">Children overview</div>
        <div className="rounded-xl border border-border bg-background p-6 text-muted-foreground">Recent grades</div>
        <div className="rounded-xl border border-border bg-background p-6 text-muted-foreground">Attendance</div>
      </div>
    </div>
  );
}
