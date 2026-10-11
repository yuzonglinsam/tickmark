import { cn } from "@/lib/utils";

export function Panel({ title, eyebrow, action, children, className, bodyClassName }: {
  title?: React.ReactNode;
  eyebrow?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={cn("panel flex min-w-0 flex-col", className)}>
      {(title || eyebrow || action) && (
        <header className="flex items-start justify-between gap-3 border-b border-hairline px-5 py-3.5">
          <div className="min-w-0">
            {eyebrow && <div className="label-caps mb-1">{eyebrow}</div>}
            {title && <h2 className="text-[14px] font-medium text-ink-1">{title}</h2>}
          </div>
          {action}
        </header>
      )}
      <div className={cn("flex-1 p-5", bodyClassName)}>{children}</div>
    </section>
  );
}

export function Stat({ label, value, sub, className }: { label: React.ReactNode; value: React.ReactNode; sub?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("min-w-0", className)}>
      <div className="label-caps">{label}</div>
      <div className="num mt-1.5 text-[22px] font-semibold tracking-tight text-ink-1">{value}</div>
      {sub && <div className="mt-1 text-[12px] text-ink-3">{sub}</div>}
    </div>
  );
}
