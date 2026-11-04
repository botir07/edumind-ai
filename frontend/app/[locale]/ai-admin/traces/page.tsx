"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { aiService } from "@/lib/ai";

export default function AITracesPage() {
  
  const [traces, setTraces] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    aiService.listTraces().then(setTraces).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-[400px]">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Trace Explorer</h1>
      <p className="text-muted-foreground">AI request traces (no secrets or private content logged).</p>
      <Card>
        <CardHeader><CardTitle>Traces</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Trace ID</TableHead>
                  <TableHead>Operation</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Latency (ms)</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {traces.length === 0 ? (
                  <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground py-4">
                    No traces.
                  </TableCell></TableRow>
                ) : (
                  traces.map((tr) => (
                    <TableRow key={tr.trace_id}>
                      <TableCell className="font-mono text-xs">{tr.trace_id}</TableCell>
                      <TableCell>{tr.operation || "—"}</TableCell>
                      <TableCell>{tr.status || "—"}</TableCell>
                      <TableCell>{String(tr.latency_ms || "—")}</TableCell>
                      <TableCell className="font-mono text-xs">{tr.created_at || "—"}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
