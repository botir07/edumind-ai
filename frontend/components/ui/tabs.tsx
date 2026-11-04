"use client";

import * as React from "react";
import { cn } from "./cn";

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref as any}
        className={cn("inline-flex h-10 w-full items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground", className)}
        {...props}
      />
    );
  }
);
Tabs.displayName = "Tabs";

export interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {}

export const TabsList = React.forwardRef<HTMLDivElement, TabsListProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref as any}
        className={cn("inline-flex h-9 w-auto items-center justify-center rounded-md p-1 text-sm font-medium", className)}
        {...props}
      />
    );
  }
);
TabsList.displayName = "TabsList";

export interface TabsTriggerProps extends React.HTMLAttributes<HTMLButtonElement> {}

export const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, ...props }, ref) => {
    return (
      <button
        ref={ref as any}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 data-[state=active]:bg-background data-[state=active]:text-sm data-[state=active]:text-foreground",
          className,
        )}
        {...props}
      />
    );
  }
);
TabsTrigger.displayName = "TabsTrigger";

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref as any}
        className={cn("mt-2 focus:outline-none", className)}
        {...props}
      />
    );
  }
);
TabsContent.displayName = "TabsContent";
