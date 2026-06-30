import { BadgeCheck, Building2, ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";

type TemplateCardProps = {
  title: string;
  summary: string;
  audience: string;
  selected: boolean;
  onClick: () => void;
};

export default function TemplateCard({
  title,
  summary,
  audience,
  selected,
  onClick,
}: TemplateCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "group relative overflow-hidden rounded-3xl border p-5 text-left transition duration-300",
        selected
          ? "border-cyan-300/60 bg-slate-900 shadow-[0_0_0_1px_rgba(103,232,249,0.25),0_18px_45px_rgba(8,47,73,0.38)]"
          : "border-white/10 bg-white/5 hover:border-amber-300/40 hover:bg-white/[0.07]",
      )}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(250,204,21,0.12),transparent_36%),radial-gradient(circle_at_bottom_left,rgba(34,211,238,0.08),transparent_34%)]" />
      <div className="relative flex items-start justify-between gap-4">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="rounded-full border border-white/10 bg-white/5 p-2 text-cyan-200">
              <Building2 className="size-4" />
            </span>
            <span className="font-display text-lg text-white">{title}</span>
          </div>
          <p className="text-sm leading-6 text-slate-300">{summary}</p>
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-amber-200/80">
            <BadgeCheck className="size-3.5" />
            {audience}
          </div>
        </div>
        <ChevronRight
          className={cn(
            "mt-1 size-5 transition duration-300",
            selected ? "text-cyan-300" : "text-slate-500 group-hover:text-amber-200",
          )}
        />
      </div>
    </button>
  );
}
