"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function GradebookPage() {
  const t = useTranslations("gradebook");
  const { session } = useSession();
  const [assessments, setAssessments] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const org = session.memberships?.[0]?.organization_id;
    if (!org) { setLoading(false); return; }
    apiFetch(`/api/v1/gradebook/assessments?organization_id=${org}`)
      .then((data: any) => setAssessments(data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [session.memberships]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          <p className="text-muted-foreground">{t("assessments")}</p>
        </div>
      </div>
      {loading ? <div className="flex items-center justify-center py-10">Loading...</div> : (
        <Card>
          <CardHeader><CardTitle>{t("gradebook.assessments")}</CardTitle></CardHeader>
          <CardContent>
            {assessments.length === 0 ? <p className="text-muted-foreground text-center py-8">No assessments.</p> : (
              <table className="w-full text-sm border-collapse">
                <thead><tr className="border-b text-muted-foreground"><th className="pb-3 text-left">Title</th><th className="pb-3 text-left">Category</th><th className="pb-3 text-left">Max score</th></tr></thead>
                <tbody>
                  {assessments.map((a) => (
                    <tr key={a.id} className="border-b"><td className="py-3">{a.title}</td><td className="py-3">{a.category}</td><td className="py-3">{a.max_score}</td></tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
