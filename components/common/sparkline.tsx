export function Sparkline({ values, width = 84, height = 26, color = "var(--series-1)" }: {
  values: (number | null)[];
  width?: number;
  height?: number;
  color?: string;
}) {
  const pts = values.map((v, i) => ({ v, i })).filter((p): p is { v: number; i: number } => p.v !== null);
  if (pts.length < 2) return <svg width={width} height={height} aria-hidden />;
  const min = Math.min(...pts.map((p) => p.v));
  const max = Math.max(...pts.map((p) => p.v));
  const span = max - min || Math.abs(max) || 1;
  const x = (i: number) => 3 + (i / Math.max(1, values.length - 1)) * (width - 6);
  const y = (v: number) => height - 4 - ((v - min) / span) * (height - 8);
  const d = pts.map((p, k) => `${k ? "L" : "M"}${x(p.i).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");
  const last = pts[pts.length - 1];
  const area = `${d} L${x(last.i).toFixed(1)},${height} L${x(pts[0].i).toFixed(1)},${height} Z`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden className="overflow-visible">
      <path d={area} fill={color} opacity={0.08} />
      <path d={d} fill="none" stroke={color} strokeWidth={1.75} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(last.i)} cy={y(last.v)} r={2.6} fill={color} stroke="var(--panel)" strokeWidth={1.5} />
    </svg>
  );
}
