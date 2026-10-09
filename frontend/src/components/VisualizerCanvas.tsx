import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { AlgorithmStep, VisualizationLabels } from '../types';
import { LatexFormula } from './LatexFormula';
import { observeSvgMathConnections } from '../lib/svgMathConnections';

interface VisualizerCanvasProps {
  step: AlgorithmStep;
  viewType: 'tape' | 'tiling';
  playbackSpeed: number;
  labels: VisualizationLabels;
}

export const VisualizerCanvas: React.FC<VisualizerCanvasProps> = ({ step, viewType, playbackSpeed, labels }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = React.useState<{ width: number; height: number }>({ width: 620, height: 700 });
  const [reducedMotion, setReducedMotion] = React.useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(query.matches);
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  React.useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 50 && height > 50) {
          setSize({ width: Math.floor(width), height: Math.floor(height) });
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = d3.select(containerRef.current);
    container.selectAll('*').interrupt().remove();

    const { width } = size;
    // Keep complete scenes in view when the mathematical caption uses vertical space.
    const height = Math.max(size.height, step.phase === 'E0' || step.phase === 'E3' ? 520 : 400);
    const timing: Timing = (ms) => reducedMotion ? 0 : ms / playbackSpeed;

    const svg = container
      .append('svg')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .attr('role', 'img')
      .attr('aria-label', `${step.badge}. ${step.equation}`)
      .attr('class', 'w-full h-full block');

    if (step.type === 'E0_SWAP') {
      renderAnimatedE0Scene(svg, step, width, height, timing, labels);
    } else if (step.phase === 'E3') {
      renderAnimatedE3Scene(svg, step, width, height, viewType, timing, labels);
    } else if (viewType === 'tiling' && step.type !== 'E0_NOOP') {
      renderAnimatedTiling(svg, step, width, height, timing, labels);
    } else {
      renderAnimatedTape(svg, step, width, height, timing, labels);
    }
    const disconnectMathConnections = observeSvgMathConnections(svg.node()!);
    return () => { disconnectMathConnections(); svg.selectAll('*').interrupt(); svg.remove(); };
  }, [step, viewType, size, playbackSpeed, reducedMotion, labels]);

  return (
    <section className="bg-surface border border-border flex flex-col overflow-hidden h-full min-h-0 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 px-3.5 py-2 border-b border-border bg-surface-elevated shrink-0 min-h-[38px]">
        <span className="text-sm font-semibold text-main">{step.badge}</span>
        <div className="font-math max-w-full overflow-x-auto">
          <LatexFormula step={step} displayMode="compact" />
        </div>
      </div>
      <div ref={containerRef} className="w-full flex-1 min-h-0 bg-surface p-2 flex items-center justify-center overflow-hidden" />
    </section>
  );
};

type Timing = (milliseconds: number) => number;

function label(template: string, values: Record<string, number | null>) {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(values[key] ?? ''));
}


function appendCaption(
  group: d3.Selection<SVGGElement, unknown, null, undefined>,
  text: string,
  x: number,
  y: number,
  width: number,
  height = 56
) {
  return group.append('foreignObject').attr('x', x).attr('y', y).attr('width', width).attr('height', height)
    .append('xhtml:div')
    .style('font-family', 'var(--font-sans)')
    .style('font-size', '14px')
    .style('line-height', '1.4')
    .style('white-space', 'pre-line')
    .style('color', 'var(--text-muted)')
    .text(text);
}

// --- Animated D3 Tape Measure View ---
function renderAnimatedTape(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  step: AlgorithmStep,
  width: number,
  height: number,
  timing: Timing,
  labels: VisualizationLabels
) {
  const margin = { top: 24, right: 24, bottom: 24, left: 24 };
  const chartW = width - margin.left - margin.right;
  const chartH = height - margin.top - margin.bottom;
  const g = svg.append('g').attr('transform', `translate(${margin.left}, ${margin.top})`);

  const { m, n, q, r, isDummy } = step;
  const maxVal = Math.max(m, n, 1);
  const scale = d3.scaleLinear().domain([0, maxVal]).range([0, chartW]);

  const barH = 48;
  // Keep the comparison together and center the complete scene, including its result.
  const sceneH = step.verification ? 340 : 290;
  const yTarget = Math.max(36, (chartH - sceneH) / 2 + 28);
  const yRuler = yTarget + barH + 64;
  const stagger = Math.min(120, 300 / Math.max(q ?? 0, 1));
  const ready = step.type === 'E0_NOOP';

  // Row 1: Target rod m
  g.append('text')
    .attr('x', 0)
    .attr('y', yTarget - 12)
    .attr('fill', 'var(--color-m)')
    .attr('font-size', '15px')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-weight', '700')
    .text(`${labels.target} · m = ${m}`);

  const targetW = Math.max(scale(m), 4);
  const targetBar = g.append('rect')
      .attr('data-math-value', m)
    .attr('x', 0)
    .attr('y', yTarget)
    .attr('width', 0)
    .attr('height', barH)
    .attr('fill', 'var(--fill-rod-m)')
    .attr('stroke', 'var(--color-m)')
    .attr('stroke-width', 1.5);

  targetBar.transition()
    .duration(timing(450))
    .ease(d3.easeCubicOut)
    .attr('width', targetW);

  if (targetW >= 60) {
    g.append('text')
      .attr('x', targetW / 2)
      .attr('y', yTarget + barH / 2 + 5)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-main)')
      .attr('font-family', 'var(--font-math)')
      .attr('font-size', '16px')
      .attr('font-weight', '700')
      .attr('opacity', 0)
      .text(`m = ${m}`)
      .transition()
      .delay(timing(200))
      .duration(timing(300))
      .attr('opacity', 1);
  }

  // Row 2: Measuring stick n
  g.append('text')
    .attr('x', 0)
    .attr('y', yRuler - 12)
    .attr('fill', 'var(--color-n)')
    .attr('font-size', '15px')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-weight', '700')
    .text(ready ? `${labels.measure} · n = ${n}` : label(q === 1 ? labels.oneCopy : labels.copies, { q, n }));

  if (isDummy || ready) {
    const stickW = scale(n);
    const dummyStick = g.append('rect')
      .attr('data-math-value', n)
      .attr('x', 0)
      .attr('y', yRuler)
      .attr('width', 0)
      .attr('height', barH)
      .attr('fill', 'var(--fill-rod-n)')
      .attr('stroke', 'var(--color-n)')
      .attr('stroke-dasharray', '5 4')
      .attr('stroke-width', 1.5);

    dummyStick.transition()
      .duration(timing(500))
      .ease(d3.easeCubicOut)
      .attr('width', stickW);

    if (stickW >= 60) g.append('text')
      .attr('x', stickW / 2)
      .attr('y', yRuler + barH / 2 + 5)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--color-n)')
      .attr('font-family', 'var(--font-sans)')
      .attr('font-size', '12px')
      .attr('opacity', 0)
      .text(`n = ${n}`)
      .transition()
      .delay(timing(250))
      .duration(timing(300))
      .attr('opacity', 1);

    g.append('text')
      .attr('x', 0)
      .attr('y', yRuler + barH + 28)
      .attr('fill', ready ? 'var(--color-n)' : 'var(--color-r)')
      .attr('font-family', 'var(--font-sans)')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('opacity', 0)
      .text(ready ? labels.ready : label(labels.remainder, { r }))
      .transition()
      .delay(timing(400))
      .duration(timing(300))
      .attr('opacity', 1);
    appendCaption(g, ready ? '' : labels.dummy, 0, yRuler + barH + 50, chartW);
    return;
  }

  let curX = 0;
  const stickW = scale(n);
  const grouped = stickW < 10;
  const pieceCount = grouped ? 1 : (q || 0);
  const drawnStickW = grouped ? scale((q || 0) * n) : stickW;

  for (let i = 0; i < pieceCount; i++) {
    const startX = curX;
    const stick = g.append('rect')
      .attr('data-math-value', n)
      .attr('x', startX)
      .attr('y', yRuler)
      .attr('width', 0)
      .attr('height', barH)
      .attr('fill', 'var(--fill-rod-n)')
      .attr('stroke', 'var(--color-n)')
      .attr('stroke-width', 1.5);

    stick.transition()
      .delay(timing(i * stagger))
      .duration(timing(400))
      .ease(d3.easeCubicOut)
      .attr('width', drawnStickW);

    if (drawnStickW >= 75) {
      g.append('text')
        .attr('x', startX + drawnStickW / 2)
        .attr('y', yRuler + barH / 2 + 5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text-main)')
        .attr('font-family', 'var(--font-math)')
        .attr('font-size', '15px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(grouped ? `${q} × ${n}` : `n = ${n}`)
        .transition()
        .delay(timing(i * stagger + 200))
        .duration(timing(250))
        .attr('opacity', 1);
    }

    curX += drawnStickW;
  }

  // Subtraction tick marks on target rod m
  if (!grouped && q && q > 0) {
    for (let i = 1; i <= q; i++) {
      const tickX = i * stickW;
      if (tickX < targetW - 2) {
        g.append('line')
          .attr('x1', tickX)
          .attr('y1', yTarget)
          .attr('x2', tickX)
          .attr('y2', yTarget + barH)
          .attr('stroke', 'var(--color-n)')
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '3 3')
          .attr('opacity', 0)
          .transition()
          .delay(timing(i * stagger + 150))
          .duration(timing(300))
          .attr('opacity', 0.65);
      }
    }
  }

  const remainderDelay = (grouped ? 0 : (q || 0) * stagger) + 100;

  if (r && r > 0) {
    const remW = scale(r);
    const remRect = g.append('rect')
      .attr('data-math-value', r)
      .attr('x', curX)
      .attr('y', yRuler)
      .attr('width', 0)
      .attr('height', barH)
      .attr('fill', 'var(--fill-rod-r)')
      .attr('stroke', 'var(--color-r)')
      .attr('stroke-width', 1.5);

    remRect.transition()
      .delay(timing(remainderDelay))
      .duration(timing(400))
      .ease(d3.easeCubicOut)
      .attr('width', remW);

    if (remW >= 75) {
      g.append('text')
        .attr('x', curX + remW / 2)
        .attr('y', yRuler + barH / 2 + 5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text-main)')
        .attr('font-family', 'var(--font-math)')
        .attr('font-size', '15px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(`r = ${r}`)
        .transition()
        .delay(timing(remainderDelay + 200))
        .duration(timing(250))
        .attr('opacity', 1);
    }

    const remTextX = 0;
    g.append('text')
      .attr('x', remTextX)
      .attr('y', yRuler + barH + 30)
      .attr('fill', 'var(--color-r)')
      .attr('font-family', 'var(--font-sans)')
      .attr('font-size', '14px')
      .attr('font-weight', '700')
      .attr('opacity', 0)
      .text(label(labels.remainder, { r }))
      .transition()
      .delay(timing(remainderDelay + 250))
      .duration(timing(250))
      .attr('opacity', 1);
    appendCaption(g, label(labels.next, { n, r }), 0, yRuler + barH + 54, chartW);
  } else if (r === 0) {
    g.append('text')
      .attr('x', 0)
      .attr('y', yRuler + barH + 30)
      .attr('fill', 'var(--color-gcd)')
      .attr('font-family', 'var(--font-sans)')
      .attr('font-size', '15px')
      .attr('font-weight', '700')
      .attr('opacity', 0)
      .text(labels.exact)
      .transition()
      .delay(timing(remainderDelay))
      .duration(timing(400))
      .attr('opacity', 1);

    if (step.verification) {
      const vY = yRuler + barH + 48;
      const verification = g.append('g').attr('opacity', 0);

      verification.append('text')
        .attr('x', 0)
        .attr('y', vY + 18)
        .attr('fill', 'var(--color-gcd)')
        .attr('font-family', 'var(--font-sans)')
        .attr('font-size', '16px')
        .attr('font-weight', '700')
        .text(`gcd(${step.initialM}, ${step.initialN}) = ${n}`);

      verification.append('text')
        .attr('x', 0)
        .attr('y', vY + 42)
        .attr('fill', 'var(--text-main)')
        .attr('font-family', 'var(--font-sans)')
        .attr('font-size', '14px')
        .text(label(labels.verification, { n }));

      verification.append('text')
        .attr('x', 0)
        .attr('y', vY + 66)
        .attr('fill', 'var(--text-muted)')
        .attr('font-family', 'var(--font-math)')
        .attr('font-size', '14px')
        .text(`${step.initialM} = ${step.verification.factorM} × ${n}   ·   ${step.initialN} = ${step.verification.factorN} × ${n}`);

      verification.transition()
        .delay(timing(remainderDelay + 250))
        .duration(timing(400))
        .attr('opacity', 1);
    }
  }
}

// --- Animated D3 Tiling View ---
function renderAnimatedTiling(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  step: AlgorithmStep,
  width: number,
  height: number,
  timing: Timing,
  labels: VisualizationLabels
) {
  const margin = { top: 34, right: 30, bottom: 32, left: 110 };
  const chartW = width - margin.left - margin.right;
  const chartH = height - margin.top - margin.bottom;
  const g = svg.append('g').attr('transform', `translate(${margin.left}, ${margin.top})`);

  const { m, n, q, r, isDummy } = step;

  if (isDummy || m < n) {
    appendCaption(g, label(labels.tilingDummy, { m, n }), -80, chartH / 2 - 20, chartW + 80);
    appendCaption(g, labels.tilingNext, -80, chartH / 2 + 24, chartW + 80);
    return;
  }

  const aspect = m / Math.max(n, 1);
  let rectW = chartW * 0.88;
  let rectH = rectW / aspect;

  if (rectH > chartH * 0.76) {
    rectH = chartH * 0.76;
    rectW = rectH * aspect;
  }

  const startX = (chartW - rectW) / 2;
  const startY = (chartH - rectH) / 2;

  // Outer bounding box
  g.append('rect')
    .attr('data-math-values', `${m} ${n}`)
    .attr('x', startX)
    .attr('y', startY)
    .attr('width', rectW)
    .attr('height', rectH)
    .attr('fill', 'rgba(125, 125, 125, 0.05)')
    .attr('stroke', 'var(--color-m)')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0)
    .transition()
    .duration(timing(300))
    .attr('opacity', 1);

  g.append('text')
    .attr('x', startX + rectW / 2)
    .attr('y', startY - 12)
    .attr('text-anchor', 'middle')
    .attr('fill', 'var(--color-m)')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-size', '14px')
    .attr('font-weight', '700')
    .text(`Width = ${m}`);

  g.append('text')
    .attr('x', startX - 14)
    .attr('y', startY + rectH / 2 + 5)
    .attr('text-anchor', 'end')
    .attr('fill', 'var(--color-n)')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-size', '14px')
    .attr('font-weight', '700')
    .text(`Height = ${n}`);

  const squareSide = rectH;
  const stagger = Math.min(140, 300 / Math.max(q ?? 0, 1));
  const grouped = squareSide < 10;
  const pieceCount = grouped ? 1 : (q || 0);
  const drawnWidth = grouped ? (q || 0) * squareSide : squareSide;
  let curX = startX;

  for (let i = 0; i < pieceCount; i++) {
    const sX = curX;
    const sq = g.append('rect')
      .attr('data-math-value', n)
      .attr('x', sX)
      .attr('y', startY)
      .attr('width', 0)
      .attr('height', 0)
      .attr('fill', 'var(--fill-rod-n)')
      .attr('stroke', 'var(--color-n)')
      .attr('stroke-width', 1.5);

    sq.transition()
      .delay(timing(i * stagger))
      .duration(timing(450))
      .ease(d3.easeCubicOut)
      .attr('width', drawnWidth)
      .attr('height', squareSide);

    if (squareSide >= 60) {
      g.append('text')
        .attr('x', sX + squareSide / 2)
        .attr('y', startY + squareSide / 2 + 5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text-main)')
        .attr('font-family', 'var(--font-sans)')
        .attr('font-size', squareSide < 55 ? '12px' : '14px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(`${n}×${n}`)
        .transition()
        .delay(timing(i * stagger + 200))
        .duration(timing(250))
        .attr('opacity', 1);
    }

    curX += drawnWidth;
  }

  if (grouped) appendCaption(g, label(labels.grouped, { q, n }), startX, startY + squareSide + 50, rectW);

  const remW = rectW - ((q || 0) * squareSide);
  if (remW > 1) {
    const remSq = g.append('rect')
      .attr('data-math-value', r)
      .attr('x', curX)
      .attr('y', startY)
      .attr('width', 0)
      .attr('height', squareSide)
      .attr('fill', 'var(--fill-rod-r)')
      .attr('stroke', 'var(--color-r)')
      .attr('stroke-width', 1.5);

    remSq.transition()
      .delay(timing((grouped ? 0 : (q || 0) * stagger) + 100))
      .duration(timing(400))
      .ease(d3.easeCubicOut)
      .attr('width', remW);

    if (remW >= 60) {
      g.append('text')
        .attr('x', curX + remW / 2)
        .attr('y', startY + squareSide / 2 + 5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text-main)')
        .attr('font-family', 'var(--font-sans)')
        .attr('font-size', '13px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(`r=${r}`)
        .transition()
        .delay(timing((grouped ? 0 : (q || 0) * stagger) + 250))
        .duration(timing(250))
        .attr('opacity', 1);
    } else {
      g.append('text')
        .attr('x', Math.min(curX + remW, chartW))
        .attr('y', startY + squareSide + 24)
        .attr('text-anchor', 'end')
        .attr('fill', 'var(--color-r)')
        .attr('font-family', 'var(--font-sans)')
        .attr('font-size', '13px')
        .attr('font-weight', '700')
        .attr('opacity', 0)
        .text(`r=${r}`)
        .transition()
        .delay(timing((grouped ? 0 : (q || 0) * stagger) + 250))
        .duration(timing(250))
        .attr('opacity', 1);
    }
  }
}

// The same pieces change roles; their lengths never change during a transfer.
function renderRodTransfer(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  width: number,
  height: number,
  timing: Timing,
  targetValue: number,
  measureValue: number,
  measureSource: 'm' | 'r',
  step: AlgorithmStep,
  labels: VisualizationLabels
) {
  const margin = { top: 16, right: 24, bottom: 16, left: 24 };
  const chartW = width - margin.left - margin.right;
  const chartH = height - margin.top - margin.bottom;
  const g = svg.append('g').attr('transform', `translate(${margin.left}, ${margin.top})`);

  // Source and destination columns share one scale, with separate arrow lanes.
  const gutter = Math.min(112, chartW * 0.27);
  const rodW = (chartW - gutter) / 2;
  const destinationX = rodW + gutter;
  const scale = d3.scaleLinear().domain([0, Math.max(targetValue, measureValue, 1)]).range([0, rodW]);
  const barH = Math.min(40, Math.max(28, chartH * 0.07));
  const rowGap = barH + 64;
  const targetY = Math.max(140, chartH * 0.25);
  const measureY = targetY + rowGap;
  const remainderY = measureY + rowGap;
  const settled = timing(1) === 0;

  appendCaption(g, measureSource === 'm'
    ? label(labels.swapExplanation, { m: step.m, n: step.n })
    : labels.reassignment, 0, 0, chartW, 64);
  g.append('text')
    .attr('y', 82)
    .attr('fill', 'var(--text-muted)')
    .attr('font-family', 'var(--font-math)')
    .attr('font-size', '14px')
    .text(label(labels.invariant, { m: step.m, n: step.n, nextM: targetValue, nextN: measureValue }));

  const transfers = [
    { value: targetValue, source: 'n', destination: 'm', sourceY: measureY, destinationY: targetY, laneX: rodW + gutter * 0.28, delay: 200 },
    { value: measureValue, source: measureSource, destination: 'n', sourceY: remainderY, destinationY: measureY, laneX: rodW + gutter * 0.65, delay: 750 },
  ] as const;

  for (const transfer of transfers) {
    const pieceW = scale(transfer.value);
    const sourceColor = `var(--color-${transfer.source})`;
    const destinationColor = `var(--color-${transfer.destination})`;
    const sourceCenterY = transfer.sourceY + barH / 2;
    const destinationCenterY = transfer.destinationY + barH / 2;
    const bend = 10;

    // Each connector leaves its source edge and enters its destination edge.
    // The two vertical lanes occupy different row intervals, so they never cross.
    g.append('path')
      .attr('data-math-value', transfer.value)
      .attr('d', `M ${pieceW + 4} ${sourceCenterY}
        H ${transfer.laneX - bend}
        Q ${transfer.laneX} ${sourceCenterY} ${transfer.laneX} ${sourceCenterY - bend}
        V ${destinationCenterY + bend}
        Q ${transfer.laneX} ${destinationCenterY} ${transfer.laneX + bend} ${destinationCenterY}
        H ${destinationX - 8}`)
      .attr('fill', 'none')
      .attr('stroke', sourceColor)
      .attr('stroke-width', 2);
    g.append('path')
      .attr('data-math-value', transfer.value)
      .attr('d', `M ${destinationX - 9} ${destinationCenterY - 4} L ${destinationX - 1} ${destinationCenterY} L ${destinationX - 9} ${destinationCenterY + 4} Z`)
      .attr('fill', sourceColor);

    const assignment = g.append('text')
      .attr('data-math-value', transfer.value)
      .attr('x', transfer.laneX + (transfer.destination === 'm' ? 9 : -9))
      .attr('y', (sourceCenterY + destinationCenterY) / 2 - 16)
      .attr('text-anchor', transfer.destination === 'm' ? 'start' : 'end')
      .attr('fill', sourceColor)
      .attr('font-family', 'var(--font-math)')
      .attr('font-size', '16px')
      .attr('opacity', 0)
      .text(`${transfer.destination} ← ${transfer.source}`);

    // Dashed source evidence remains after the solid piece has moved away.
    const origin = g.append('g').attr('transform', `translate(0, ${transfer.sourceY})`);
    origin.append('rect')
      .attr('data-math-value', transfer.value)
      .attr('width', pieceW)
      .attr('height', barH)
      .attr('fill', 'none')
      .attr('stroke', sourceColor)
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '5 4');
    const sourceLabel = origin.append('text')
      .attr('y', -14)
      .attr('fill', sourceColor)
      .attr('font-family', 'var(--font-math)')
      .attr('font-size', '18px')
      .attr('opacity', settled ? 1 : 0)
      .text(`${transfer.source} = ${transfer.value}`);
    origin.append('text')
      .attr('y', -40)
      .attr('fill', 'var(--text-muted)')
      .attr('font-family', 'var(--font-sans)')
      .attr('font-size', '12px')
      .text(transfer.source === 'n' ? labels.fromStick : transfer.source === 'r' ? labels.fromRemainder : labels.fromTarget);

    const destinationLabel = g.append('text')
      .attr('x', destinationX)
      .attr('y', transfer.destinationY - 40)
      .attr('fill', 'var(--text-muted)')
      .attr('font-family', 'var(--font-sans)')
      .attr('font-size', '12px')
      .attr('opacity', settled ? 1 : 0)
      .text(transfer.destination === 'm' ? labels.newTarget : labels.newMeasure);

    const piece = g.append('g')
      .attr('transform', settled
        ? `translate(${destinationX}, ${transfer.destinationY})`
        : `translate(0, ${transfer.sourceY})`);
    const rod = piece.append('rect')
      .attr('data-math-value', transfer.value)
      .attr('width', pieceW)
      .attr('height', barH)
      .attr('fill', `var(--fill-rod-${settled ? transfer.destination : transfer.source})`)
      .attr('stroke', settled ? destinationColor : sourceColor)
      .attr('stroke-width', 1.5);
    const pieceLabel = piece.append('text')
      .attr('y', -14)
      .attr('fill', settled ? destinationColor : sourceColor)
      .attr('font-family', 'var(--font-math)')
      .attr('font-size', '18px')
      .text(`${settled ? transfer.destination : transfer.source} = ${transfer.value}`);

    if (settled) continue;

    // The first rod reaches its new row before the second rod starts moving.
    piece.transition()
      .delay(timing(transfer.delay))
      .duration(timing(150))
      .ease(d3.easeCubicInOut)
      .attr('transform', `translate(${destinationX}, ${transfer.sourceY})`)
      .transition()
      .duration(timing(250))
      .attr('transform', `translate(${destinationX}, ${transfer.destinationY})`)
      .on('end', () => {
        rod.attr('fill', `var(--fill-rod-${transfer.destination})`).attr('stroke', destinationColor);
        pieceLabel.attr('fill', destinationColor).text(`${transfer.destination} = ${transfer.value}`);
        sourceLabel.attr('opacity', 1);
        destinationLabel.attr('opacity', 1);
      });
    assignment.transition()
      .delay(timing(transfer.delay))
      .duration(timing(100))
      .attr('opacity', 1)
      .transition()
      .delay(timing(200))
      .duration(timing(100))
      .attr('opacity', 0);
  }
  appendTransferSummary(g, targetValue, measureValue, chartW, remainderY + barH + 28, labels);
}

function appendTransferSummary(
  group: d3.Selection<SVGGElement, unknown, null, undefined>,
  m: number,
  n: number,
  width: number,
  y: number,
  labels: VisualizationLabels
) {
  group.append('text')
    .attr('y', y)
    .attr('fill', 'var(--text-main)')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .text(labels.readyForDivision);
  appendCaption(group,
    `${label(labels.nextPass, { m, n, q: Math.floor(m / n) })}\n${label(labels.predictedRemainder, { r: m % n })}`,
    0, y + 10, width, 64);
}

// --- Animated Step E0 Swap Scene (Prevent Dummy Division Pass) ---
function renderAnimatedE0Scene(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  step: AlgorithmStep,
  width: number,
  height: number,
  timing: Timing,
  labels: VisualizationLabels
) {
  renderRodTransfer(svg, width, height, timing, step.n, step.m, 'm', step, labels);
}

// --- Animated Step E3 Reduction Scene ---
function renderAnimatedE3Scene(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  step: AlgorithmStep,
  width: number,
  height: number,
  viewType: 'tape' | 'tiling',
  timing: Timing,
  labels: VisualizationLabels
) {
  if (viewType === 'tape') {
    renderRodTransfer(svg, width, height, timing, step.n, step.r ?? 0, 'r', step, labels);
    return;
  }

  const margin = { top: 16, right: 24, bottom: 16, left: 24 };
  const chartW = width - margin.left - margin.right;
  const chartH = height - margin.top - margin.bottom;
  const g = svg.append('g').attr('transform', `translate(${margin.left}, ${margin.top})`);
  renderE3TilingReduction(g, step, chartW, chartH, timing, labels);
}

// --- 2D Tiling Reduction View for Step E3 ---
function renderE3TilingReduction(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  step: AlgorithmStep,
  chartW: number,
  chartH: number,
  timing: Timing,
  labels: VisualizationLabels
) {
  const { m, n, r, nextM = n, nextN = (r ?? 0) } = step;

  g.append('text')
    .attr('y', 24)
    .attr('fill', 'var(--text-muted)')
    .attr('font-family', 'var(--font-math)')
    .attr('font-size', '14px')
    .text(label(labels.invariant, { m, n, nextM, nextN }));
  appendCaption(g, labels.tilingReduction, 0, 60, chartW);

  // One scale preserves the remainder's area across its quarter turn.
  const unit = Math.min(chartW * 0.38, (chartH - 120) * 0.65) / Math.max(m, n, 1);
  const boxW = m * unit;
  const boxH = n * unit;

  const leftX = chartW * 0.24 - boxW / 2;
  const centerY = chartH / 2 + 10;

  // Left: Previous Rectangle
  const leftG = g.append('g').attr('transform', `translate(${leftX}, ${centerY - boxH / 2})`);
  leftG.append('rect')
    .attr('data-math-values', `${m} ${n}`)
    .attr('width', boxW)
    .attr('height', boxH)
    .attr('fill', 'rgba(125, 125, 125, 0.05)')
    .attr('stroke', 'var(--color-m)')
    .attr('stroke-width', 1.5);

  leftG.append('text')
    .attr('x', boxW / 2)
    .attr('y', -10)
    .attr('text-anchor', 'middle')
    .attr('fill', 'var(--color-m)')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-size', '13px')
    .attr('font-weight', '700')
    .text(`Previous: ${m} × ${n}`);

  // Highlight untiled portion
  const untiledW = (r ?? 0) * unit;
  leftG.append('rect')
    .attr('data-math-values', `${n} ${r ?? 0}`)
    .attr('x', boxW - untiledW)
    .attr('y', 0)
    .attr('width', untiledW)
    .attr('height', boxH)
    .attr('fill', 'var(--fill-rod-r)')
    .attr('stroke', 'var(--color-r)')
    .attr('stroke-width', 1.5);

  // Transition Arrow
  g.append('text')
    .attr('x', chartW / 2)
    .attr('y', centerY + 6)
    .attr('text-anchor', 'middle')
    .attr('fill', 'var(--color-n)')
    .attr('font-size', '24px')
    .text('⟶');

  g.append('text')
    .attr('x', chartW / 2)
    .attr('y', centerY + 30)
    .attr('text-anchor', 'middle')
    .attr('fill', 'var(--text-muted)')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .text(labels.rotate);

  // Right: Next Rectangle
  const rightBoxW = nextM * unit;
  const rightBoxH = nextN * unit;
  const rightX = chartW * 0.76 - rightBoxW / 2;

  const rightG = g.append('g').attr('transform', `translate(${rightX}, ${centerY - rightBoxH / 2})`);
  rightG.attr('opacity', 0).transition().delay(timing(300)).duration(timing(400)).attr('opacity', 1);
  rightG.append('rect')
    .attr('data-math-values', `${nextM} ${nextN}`)
    .attr('width', rightBoxW)
    .attr('height', rightBoxH)
    .attr('fill', 'var(--fill-rod-n)')
    .attr('stroke', 'var(--color-n)')
    .attr('stroke-width', 1.5);

  rightG.append('text')
    .attr('x', rightBoxW / 2)
    .attr('y', -10)
    .attr('text-anchor', 'middle')
    .attr('fill', 'var(--color-n)')
    .attr('font-family', 'var(--font-sans)')
    .attr('font-size', '13px')
    .attr('font-weight', '700')
    .text(`New Canvas: ${nextM} × ${nextN}`);

  appendTransferSummary(g, nextM, nextN, chartW, centerY + Math.max(boxH, rightBoxH) / 2 + 42, labels);
}
