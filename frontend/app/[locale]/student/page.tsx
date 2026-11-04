"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";

export default function StudentDashboard() {
  const t = useTranslations("dashboard");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("dashboard") || "Student Dashboard"}</h1>
      <p className="text-muted-foreground">Your lessons, grades, and assignments.</p>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-border bg-background p-6 text-muted-foreground">Today's lessons</div>
        <div className="rounded-xl border border-border bg-background p-6 text-muted-foreground">Upcoming assignments</div>
        <div className="rounded-xl border border-border bg-background p-6 text-muted-foreground">Recent grades</div>
      </div>
    </div>
  );
}
