"use client";

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/components/ui/cn";

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
}

export function StatCard({ title, value, subtitle, trend }: StatCardProps) {
  return (
    <Card className="border-t-2">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <CardDescription className="ml-auto text-right">{trend}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{subtitle || ""}</p>
      </CardContent>
    </Card>
  );
}

export function DashboardGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">{children}</div>;
}
