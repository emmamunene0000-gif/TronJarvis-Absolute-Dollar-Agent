"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, type IChartApi, type ISeriesApi, type CandlestickData, type Time, type SeriesMarker } from "lightweight-charts";

type Candle = { time: number; open: number; high: number; low: number; close: number };
type Signal = { id?: number | string; signal: string; bias: "CALL" | "PUT"; time: number; spot: number; confidence: number };

export default function PriceChart({ candles, signals }: { candles: Candle[]; signals: Signal[] }) {
  const host = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  useEffect(() => {
    if (!host.current) return;
    const chart = createChart(host.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "#10130f" }, textColor: "#879087", fontFamily: "ui-monospace, monospace" },
      grid: { vertLines: { color: "#20251f" }, horzLines: { color: "#20251f" } },
      rightPriceScale: { borderColor: "#30372e" },
      timeScale: { borderColor: "#30372e", timeVisible: true, secondsVisible: false },
      crosshair: { vertLine: { color: "#b3e65a55" }, horzLine: { color: "#b3e65a55" } },
    });
    const series = chart.addCandlestickSeries({ upColor: "#b3e65a", downColor: "#ed705e", borderVisible: false, wickUpColor: "#b3e65a", wickDownColor: "#ed705e" });
    chartRef.current = chart;
    seriesRef.current = series;
    const resize = new ResizeObserver(() => chart.timeScale().fitContent());
    resize.observe(host.current);
    return () => { resize.disconnect(); chart.remove(); chartRef.current = null; seriesRef.current = null; };
  }, []);
  useEffect(() => {
    const series = seriesRef.current;
    if (!series || !candles.length) return;
    const sorted = [...candles].sort((a, b) => a.time - b.time);
    series.setData(sorted.map((c): CandlestickData<Time> => ({ time: c.time as Time, open: c.open, high: c.high, low: c.low, close: c.close })));
    const candleTimes = new Set(sorted.map(c => c.time));
    const markers: SeriesMarker<Time>[] = signals.filter(s => Number.isFinite(s.time) && Number.isFinite(s.spot)).flatMap(s => {
      // TRON JSON emits Unix milliseconds; Lightweight Charts requires Unix seconds.
      const seconds = Math.floor(s.time / 1000);
      const candleTime = Math.floor(seconds / 300) * 300;
      if (!candleTimes.has(candleTime)) return [];
      return [{ time: candleTime as Time, position: s.bias === "CALL" ? "belowBar" : "aboveBar", color: s.bias === "CALL" ? "#b3e65a" : "#ed705e", shape: s.bias === "CALL" ? "arrowUp" : "arrowDown", text: `${s.signal} ${s.confidence}%` }];
    });
    series.setMarkers(markers);
  }, [candles, signals]);
  return <div ref={host} className="chart-canvas" aria-label="Market candlestick chart" />;
}
