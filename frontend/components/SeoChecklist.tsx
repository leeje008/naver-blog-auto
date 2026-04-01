"use client";

import { CheckCircle2, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface SeoItem {
  key: string;
  label: string;
  score: number;
  max_score: number;
  passed: boolean;
  suggestions: string[];
}

interface SeoChecklistProps {
  items: SeoItem[];
}

function SeoCheckItem({ item }: { item: SeoItem }) {
  const [open, setOpen] = useState(false);
  const pct = item.max_score > 0 ? Math.round((item.score / item.max_score) * 100) : 0;

  return (
    <div
      className={cn(
        "rounded-lg border p-3 transition-colors",
        item.passed ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"
      )}
    >
      <button
        type="button"
        className="flex w-full items-start gap-2 text-left"
        onClick={() => setOpen(!open)}
      >
        {item.passed ? (
          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-[#03C75A]" />
        ) : (
          <XCircle className="mt-0.5 size-4 shrink-0 text-red-500" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-medium">{item.label}</span>
            <span className="text-xs font-mono text-muted-foreground">
              {item.score}/{item.max_score} ({pct}%)
            </span>
          </div>
        </div>
        {item.suggestions.length > 0 && (
          open ? (
            <ChevronUp className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronDown className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          )
        )}
      </button>
      {open && item.suggestions.length > 0 && (
        <ul className="mt-2 ml-6 space-y-1">
          {item.suggestions.map((s, i) => (
            <li key={i} className="text-xs text-muted-foreground">
              - {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function SeoChecklist({ items }: SeoChecklistProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {items.map((item) => (
        <SeoCheckItem key={item.key} item={item} />
      ))}
    </div>
  );
}
