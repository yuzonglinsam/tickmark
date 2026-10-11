"use client";

import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { BarChart, LineChart, ScatterChart, TreemapChart, CustomChart } from "echarts/charts";
import {
  GridComponent, TooltipComponent, MarkLineComponent, MarkAreaComponent, LegendComponent,
  DataZoomComponent, VisualMapComponent, GraphicComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";

echarts.use([
  BarChart, LineChart, ScatterChart, TreemapChart, CustomChart, GridComponent, TooltipComponent,
  MarkLineComponent, MarkAreaComponent, LegendComponent, DataZoomComponent, VisualMapComponent,
  GraphicComponent, SVGRenderer,
]);

export const C = {
  ink1: "#e6edf3",
  ink2: "#aab6c2",
  ink3: "#6f7c89",
  grid: "#18202a",
  axis: "#283340",
  panel: "#0b0f14",
  s1: "#3987e5",
  s2: "#d95926",
  s3: "#199e70",
  muted: "#3a4553",
  amber: "#f2a33a",
  good: "#2fbf71",
  critical: "#e5484d",
  tiers: ["#3d8ee8", "#6aa3e0", "#9db8d3", "#d8a77f", "#e57e4d", "#e5484d"],
};

export const baseTooltip = {
  trigger: "axis" as const,
  backgroundColor: "#0e131a",
  borderColor: "#283340",
  borderWidth: 1,
  padding: [8, 10],
  textStyle: { color: C.ink1, fontSize: 12, fontFamily: "Inter Variable, sans-serif" },
  extraCssText: "border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.45);",
};

export const axisCommon = {
  axisLine: { lineStyle: { color: C.axis } },
  axisTick: { show: false },
  axisLabel: { color: C.ink3, fontSize: 11, fontFamily: "JetBrains Mono Variable, monospace" },
  splitLine: { lineStyle: { color: C.grid } },
};

export function EChart({ option, height = 260, className, onEvents }: {
  // ECharts option typing is very strict for callbacks; options are validated visually instead.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  option: EChartsOption | Record<string, any>;
  height?: number | string;
  className?: string;
  onEvents?: Record<string, (p: unknown) => void>;
}) {
  return (
    <ReactEChartsCore
      echarts={echarts}
      option={{ backgroundColor: "transparent", animationDuration: 600, animationEasing: "cubicOut", ...option }}
      style={{ height, width: "100%" }}
      className={className}
      opts={{ renderer: "svg" }}
      notMerge
      lazyUpdate
      onEvents={onEvents}
    />
  );
}
