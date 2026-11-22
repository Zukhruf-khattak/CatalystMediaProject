import * as React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const variantStyles = {
      primary: "bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm focus-visible:ring-indigo-500",
      secondary: "bg-slate-800 hover:bg-slate-700 text-slate-100 focus-visible:ring-slate-400",
      outline: "border border-slate-700 hover:bg-slate-800 text-slate-200 focus-visible:ring-slate-400",
      ghost: "hover:bg-slate-800 text-slate-300 hover:text-white focus-visible:ring-slate-400",
    };

    const sizeStyles = {
      sm: "h-8 px-3 text-xs",
      md: "h-9 px-4 text-sm",
      lg: "h-11 px-6 text-base",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:opacity-50 disabled:pointer-events-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
