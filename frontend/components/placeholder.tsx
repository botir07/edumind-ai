"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PlaceholderPageProps { section: string }

export default function PlaceholderPage({ section }: PlaceholderPageProps) {
  const t = useTranslations("common");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{section}</h1>
      <Card>
        <CardHeader><CardTitle>Coming soon</CardTitle></CardHeader>
        <CardContent className="text-muted-foreground text-center py-12">
          This section is scaffolded for Phase 1. Connect it to the corresponding backend endpoints.
        </CardContent>
      </Card>
    </div>
  );
}
