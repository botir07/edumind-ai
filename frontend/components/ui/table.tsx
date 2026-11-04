"use client";

import * as React from "react";
import { cn } from "@/components/ui/cn";

export type TableProps = React.HTMLAttributes<HTMLTableElement>;
export function Table({ className, ...props }: TableProps) {
  return <table className={cn("w-full text-sm border-collapse", className)} {...props} />;
}

export type TableHeaderProps = React.HTMLAttributes<HTMLTableSectionElement>;
export function TableHeader({ className, ...props }: TableHeaderProps) {
  return <thead className={cn("", className)} {...props} />;
}

export type TableBodyProps = React.HTMLAttributes<HTMLTableSectionElement>;
export function TableBody({ className, ...props }: TableBodyProps) {
  return <tbody className={cn("", className)} {...props} />;
}

export type TableFooterProps = React.HTMLAttributes<HTMLTableSectionElement>;
export function TableFooter({ className, ...props }: TableFooterProps) {
  return <tfoot className={cn("", className)} {...props} />;
}

export type TableRowProps = React.HTMLAttributes<HTMLTableRowElement>;
export function TableRow({ className, ...props }: TableRowProps) {
  return (
    <tr className={cn("border-b transition-colors hover:bg-accent/50 data-[state=selected]:bg-accent", className)} {...props} />
  );
}

export type TableHeadProps = React.HTMLAttributes<HTMLTableCellElement>;
export function TableHead({ className, ...props }: TableHeadProps) {
  return (
    <th
      className={cn(
        "text-left font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0",
        className
      )}
      {...props}
    />
  );
}

export type TableCellProps = React.HTMLAttributes<HTMLTableCellElement> & {
  colSpan?: number;
  rowSpan?: number;
};
export function TableCell({ className, colSpan, rowSpan, ...props }: TableCellProps) {
  return (
    <td className={cn("p-3 align-middle", className)} colSpan={colSpan} rowSpan={rowSpan} {...props} />
  );
}

export type TableCaptionProps = React.HTMLAttributes<HTMLTableCaptionElement>;
export function TableCaption({ className, ...props }: TableCaptionProps) {
  return <caption className={cn("mt-4 text-sm text-muted-foreground", className)} {...props} />;
}
