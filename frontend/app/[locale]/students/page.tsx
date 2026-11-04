"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Plus, UserPlus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/components/ui/cn";

export default function StudentsPage() {
  const t = useTranslations("students");
  const { session } = useSession();
  const [students, setStudents] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [search, setSearch] = React.useState("");
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    load();
  }, [search]);

  async function load() {
    setLoading(true);
    try {
      const org = session.memberships?.[0]?.organization_id;
      const url = org ? `/api/v1/students?organization_id=${org}&search=${encodeURIComponent(search)}&page_size=20` : `/api/v1/students?search=${encodeURIComponent(search)}`;
      const data = await apiFetch<{ data: any[]; meta: any }>(url);
      setStudents(data.data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load students");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-2">
          <UserPlus className="w-6 h-6" />
          <h1 className="text-xl font-bold">{t("title") || "Students"}</h1>
        </div>
        <div className="flex items-center gap-2">
          <Input
            placeholder={t("searchPlaceholder") || "Search students..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64"
          />
          <Button onClick={() => {}} disabled>
            <Plus className="w-4 h-4" /> {t("addStudent") || "Add student"}
          </Button>
        </div>
      </div>
      {error && <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive text-sm">{error}</div>}
      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-10 text-muted-foreground">Loading...</div>
          ) : students.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No students found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="pb-3 font-medium">{t("students") || "Students"}</th>
                    <th className="pb-3 font-medium">{t("studentNumber") || "Student number"}</th>
                    <th className="pb-3 font-medium">{t("status") || "Status"}</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.id} className="border-b last:border-0 hover:bg-accent/50">
                      <td className="py-3">{s.user?.full_name || s.student_number}</td>
                      <td className="py-3 text-muted-foreground">{s.student_number}</td>
                      <td className="py-3">
                        <span className={cn("inline-flex items-center rounded-full px-2 py-1 text-xs font-medium", s.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700")}>
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
