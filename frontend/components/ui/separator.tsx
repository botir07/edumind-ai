"use client";

import * as React from "react";
import { cn } from "./cn";

export interface SeparatorProps extends React.HTMLAttributes<HTMLHRElement> {}

export const Separator = React.forwardRef<HTMLHRElement, SeparatorProps>(
  ({ className, ...props }, ref) => {
    return (
      <hr
        ref={ref as any}
        className={cn("border-t border-border", className)}
        {...props}
      />
    );
  }
);
Separator.displayName = "Separator";
