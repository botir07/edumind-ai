"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { Loader2 } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const t = useTranslations("dashboard");
  const { session } = useSession();
  const role = session.memberships?.[0]?.role || (session.user?.is_superuser ? "SUPER_ADMIN" : "STUDENT");

  if (!session.loaded) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  const target = {
    SUPER_ADMIN: "/super-admin",
    SCHOOL_ADMIN: "/school-admin",
    TEACHER: "/teacher",
    STUDENT: "/student",
    PARENT: "/parent",
  }[role] || "/student";

  React.useEffect(() => {
    if (session.loaded) router.push(target);
  }, [session.loaded, router, target]);

  return null;
}
