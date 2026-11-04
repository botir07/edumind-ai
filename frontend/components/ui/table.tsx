"use client";

import * as React from "react";
import { cn } from "./cn";

export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {}

export const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ className, ...props }, ref) => {
    return (
      <table
        ref={ref as any}
        className={cn("w-full text-sm border-collapse", className)}
        {...props}
      />
    );
  }
);
Table.displayName = "Table";

export interface TableHeaderProps extends React.HTMLAttributes<HTMLTableSectionElement> {}

export const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  TableHeaderProps
>(({ className, ...props }, ref) => {
  return (
    <thead
      ref={ref as any}
      className={cn("[&_tr]:border-b", className)}
      {...props}
    />
  );
});
TableHeader.displayName = "TableHeader";

export interface TableBodyProps extends React.HTMLAttributes<HTMLTableSectionElement> {}

export const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  TableBodyProps
>(({ className, ...props }, ref) => {
  return (
    <tbody
      ref={ref as any}
      className={cn("[&_tr]:last:border-b-0", className)}
      {...props}
    />
  );
});
TableBody.displayName = "TableBody";

export interface TableFooterProps extends React.HTMLAttributes<HTMLTableSectionElement> {}

export const TableFooter = React.forwardRef<
  HTMLTableSectionElement,
  TableFooterProps
>(({ className, ...props }, ref) => {
  return (
    <tfoot
      ref={ref as any}
      className={cn("[&_tr]:border-b", className)}
      {...props}
    />
  );
});
TableFooter.displayName = "TableFooter";

export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {}

export const TableRow = React.forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ className, ...props }, ref) => {
    return (
      <tr
        ref={ref as any}
        className={cn(
          "border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted",
          className,
        )}
        {...props}
      />
    );
  }
);
TableRow.displayName = "TableRow";

export interface TableHeadProps extends React.HTMLAttributes<HTMLTableCellElement> {}

export const TableHead = React.forwardRef<HTMLTableCellElement, TableHeadProps>(
  ({ className, ...props }, ref) => {
    return (
      <th
        ref={ref as any}
        className={cn(
          "text-left font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0",
          className,
        )}
        {...props}
      />
    );
  }
);
TableHead.displayName = "TableHead";

export interface TableCellProps extends React.HTMLAttributes<HTMLTableCellElement> {
  colSpan?: number;
  rowSpan?: number;
}

export const TableCell = React.forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ className, colSpan, rowSpan, ...props }, ref) => {
    return (
      <td
        ref={ref as any}
        colSpan={colSpan}
        rowSpan={rowSpan}
        className={cn("p-3 align-middle [&:has([role=checkbox])]:pl-0", className)}
        {...props}
      />
    );
  }
);
TableCell.displayName = "TableCell";
