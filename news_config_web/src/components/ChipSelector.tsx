import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

type ChipSelectorProps = {
  label: string;
  options: string[];
  values: string[];
  onToggle: (value: string) => void;
};

export default function ChipSelector({ label, options, values, onToggle }: ChipSelectorProps) {
  return (
    <section className="space-y-4 rounded-3xl border border-white/10 bg-slate-950/50 p-5">
      <div className="space-y-1">
        <h3 className="font-display text-lg text-white">{label}</h3>
        <p className="text-sm text-slate-400">可多选，点击即可启用或取消。</p>
      </div>
      <div className="flex flex-wrap gap-3">
        {options.map((option) => {
          const active = values.includes(option);
          return (
            <button
              key={option}
              type="button"
              onClick={() => onToggle(option)}
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition duration-200",
                active
                  ? "border-cyan-300/50 bg-cyan-400/10 text-cyan-100"
                  : "border-white/10 bg-white/5 text-slate-300 hover:border-amber-300/40 hover:text-white",
              )}
            >
              <Check className={cn("size-3.5", active ? "opacity-100" : "opacity-30")} />
              {option}
            </button>
          );
        })}
      </div>
    </section>
  );
}
