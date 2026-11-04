"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useSession } from "@/lib/auth";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/components/ui/cn";
import { LogOut, Menu, Sun, Moon, LayoutDashboard, Users, School, BookOpen, GraduationCap, ShieldAlert, BarChart3, Settings } from "lucide-react";

const NAV_ITEMS: Array<{ key: string; label: string; href: string; icon: any; roles: string[] }> = [
  { key: "dashboard", label: "nav.dashboard", href: "/dashboard", icon: LayoutDashboard, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER","STUDENT","PARENT"] },
  { key: "students", label: "nav.students", href: "/students", icon: Users, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER"] },
  { key: "teachers", label: "nav.teachers", href: "/teachers", icon: School, roles: ["SUPER_ADMIN","SCHOOL_ADMIN"] },
  { key: "parents", label: "nav.parents", href: "/parents", icon: Users, roles: ["SUPER_ADMIN","SCHOOL_ADMIN"] },
  { key: "gradebook", label: "nav.gradebook", href: "/gradebook", icon: BookOpen, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER"] },
  { key: "homework", label: "nav.homework", href: "/homework", icon: GraduationCap, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER","STUDENT","PARENT"] },
  { key: "timetable", label: "nav.timetable", href: "/timetable", icon: BookOpen, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER","STUDENT","PARENT"] },
  { key: "attendance", label: "nav.attendance", href: "/attendance", icon: ShieldAlert, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER"] },
  { key: "materials", label: "nav.materials", href: "/materials", icon: BookOpen, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER"] },
  { key: "analytics", label: "nav.analytics", href: "/analytics", icon: BarChart3, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER","PARENT"] },
  { key: "schools", label: "nav.schools", href: "/schools", icon: School, roles: ["SUPER_ADMIN"] },
  { key: "users", label: "nav.users", href: "/users", icon: Users, roles: ["SUPER_ADMIN","SCHOOL_ADMIN"] },
  { key: "settings", label: "nav.settings", href: "/settings", icon: Settings, roles: ["SUPER_ADMIN","SCHOOL_ADMIN","TEACHER","STUDENT","PARENT"] },
];

export function Sidebar() {
  const t = useTranslations("nav");
  const c = useTranslations("common");
  const { session } = useSession();
  const pathname = usePathname();
  const router = useRouter();
  const { theme, toggle } = useTheme();
  const user = session.user;
  const memberships = session.memberships || [];
  const role = memberships[0]?.role || (user?.is_superuser ? "SUPER_ADMIN" : "STUDENT");

  const items = NAV_ITEMS.filter((i) => i.roles.includes(role));

  return (
    <aside className="fixed left-0 top-14 bottom-0 w-64 border-r border-border bg-background transition-width duration-300 z-40">
      <div className="flex h-full flex-col">
        <div className="h-12 border-b border-border flex items-center justify-between px-4">
          <div className="text-sm font-semibold tracking-tight">{c("appName") || "EduMind"}</div>
          <Button size="icon" variant="ghost" onClick={() => {}} className="ml-auto -mr-1">
            <Menu className="w-5 h-5" />
          </Button>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
          {items.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.key}
                href={item.href}
                onClick={() => router.push(item.href)}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active ? "bg-primary/10 text-primary" : "text-foreground/70 hover:bg-accent hover:text-foreground"
                )}
              >
                <item.icon className="w-5 h-5" />
                {t(item.key)}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border p-4">
          <div className="text-xs text-muted-foreground mb-3">{user?.full_name || user?.email || "User"}</div>
          <div className="text-xs text-muted-foreground truncate">{memberships[0]?.organization_name || ""}</div>
          <div className="mt-3 space-y-2">
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none group">
              <span>{c("language") || "Language"}</span>
              <select className="bg-transparent text-xs border-none focus:ring-0 text-foreground/60 group-focus:text-primary" defaultValue={typeof document !== "undefined" ? (document.documentElement.lang || "uz") : "uz"} onChange={(e) => {
                const lang = e.target.value as "uz" | "ru" | "en";
                document.documentElement.lang = lang;
                localStorage.setItem("edumind-locale", lang);
                router.refresh();
              }}>
                <option value="uz">Oʻzbekcha</option>
                <option value="ru">Русский</option>
                <option value="en">English</option>
              </select>
            </label>
            <div className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none group">
              <span>{theme}</span>
              <Button size="icon" variant="ghost" onClick={() => toggle(theme === "dark" ? "light" : "dark")} className="p-1">
                {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </div>
        <div className="p-4">
          <Button onClick={handleLogout} className="w-full text-left" variant="destructive" size="sm">
            <LogOut className="w-4 h-4 mr-2" /> {c("logout") || "Logout"}
          </Button>
        </div>
      </div>
    </aside>
  );
  async function handleLogout() {
    const { logout } = useSession();
    await logout();
    router.push("/login");
  }
}
