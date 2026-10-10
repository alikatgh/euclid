import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import type { LessonScene, LessonVariable } from '../types/curriculum';
import { normalizeMathValue, splitLinkedNumbers } from '../lib/mathConnections';
import { accumulationValues, axisPosition, axisTicks, canDrawIndividualUnits, compareContributions, exactContributionLabel, exactValueLabel, divisionSegments, formatSceneNumber, visibleSceneIndices } from '../lib/curriculumSceneMath';
import { LinkedNumber } from './MathConnections';
import { MathematicalText } from './MathematicalText';
import './CurriculumScene.css';

type SceneOf<K extends LessonScene['kind']> = Extract<LessonScene, { kind: K }>;
type MotionSettings = { duration: number };
const colors = ['var(--color-m)', 'var(--color-n)', 'var(--color-gcd)', 'var(--color-q)', 'var(--color-r)'];
const ink = 'var(--text-main)', muted = 'var(--text-muted)', border = 'var(--border-color)', surface = 'var(--bg-surface-elevated)';
const numeric = (value: number | string) => normalizeMathValue(value) ?? undefined;

/** React owns these tokens: do not run the D3 mutation observer on this SVG. */
function SceneText({ text, x, y, size = 15, color = ink, anchor = 'start', weight = 400, interactive = true }: {
  text: string; x: number; y: number; size?: number; color?: string; anchor?: 'start' | 'middle' | 'end'; weight?: number; interactive?: boolean;
}) {
  return <text x={x} y={y} fontSize={size} fill={color} textAnchor={anchor} fontWeight={weight}>
    {splitLinkedNumbers(text).map((part, index) => <tspan key={index} data-math-value={part.value}
      data-math-keyboard={part.value && interactive ? 'true' : undefined} tabIndex={part.value && interactive ? 0 : undefined}
      role={part.value && interactive ? 'button' : undefined} aria-label={part.value && interactive ? `${part.text}, highlight matching values` : undefined}>{part.text}</tspan>)}
  </text>;
}
function wrapSceneText(text: string, width: number): string[] {
  const lines: string[] = [];
  for (const word of text.split(/\s+/)) {
    const last = lines.at(-1);
    if (!last || last.length + word.length + 1 > width) lines.push(word); else lines[lines.length - 1] += ` ${word}`;
  }
  return lines;
}
function WrappedText({ text, x, y, width = 30, size = 14, color = muted, anchor = 'start' }: {
  text: string; x: number; y: number; width?: number; size?: number; color?: string; anchor?: 'start' | 'middle' | 'end';
}) {
  return <g>{wrapSceneText(text, width).map((line, index) => <SceneText key={index} text={line} x={x} y={y + index * (size + 5)} size={size} color={color} anchor={anchor} />)}</g>;
}
function SceneSvg({ children, height = 350, label, description }: { children: ReactNode; height?: number; label: string; description: string }) {
  const id = useId();
  return <svg viewBox={`0 0 720 ${height}`} role="group" aria-labelledby={`${id}-title ${id}-desc`} className="curriculum-scene__svg">
    <title id={`${id}-title`}>{label}</title><desc id={`${id}-desc`}>{description}</desc>{children}</svg>;
}
function Arrow({ fromX, fromY, toX, toY, color = muted, bend = 0 }: { fromX: number; fromY: number; toX: number; toY: number; color?: string; bend?: number }) {
  const id = useId();
  return <g aria-hidden="true"><defs><marker id={id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill={color} /></marker></defs>
    <path d={bend ? `M ${fromX} ${fromY} Q ${(fromX + toX) / 2} ${(fromY + toY) / 2 + bend} ${toX} ${toY}` : `M ${fromX} ${fromY} L ${toX} ${toY}`}
      fill="none" stroke={color} strokeWidth="2" markerEnd={`url(#${id})`} /></g>;
}
function UnitDots({ count, x, y, columns = 8, spacing = 11, color = 'var(--color-m)' }: { count: number; x: number; y: number; columns?: number; spacing?: number; color?: string }) {
  return <g aria-hidden="true" data-math-value={numeric(count)}>{Array.from({ length: count }, (_, index) => <rect key={index}
    x={x + (index % columns) * spacing} y={y + Math.floor(index / columns) * spacing} width={spacing - 3} height={spacing - 3} rx="1.5" fill={color} />)}</g>;
}

function DivisionScene({ scene, transition, units }: { scene: SceneOf<'division'>; transition: MotionSettings; units: boolean }) {
  const model = divisionSegments(scene.m, scene.n);
  const x = (value: number) => 48 + value / model.scaleMaximum * 624;
  const width = (value: number) => value / model.scaleMaximum * 624;
  return <SceneSvg label="Division as equal lengths" height={345} description={`${scene.m} units contain ${scene.q} complete copies of ${scene.n} and ${scene.r} units left over. All lengths use the same scale.`}>
    <SceneText text={`The whole length: ${scene.m}`} x={48} y={30} weight={600} />
    <motion.rect initial={false} animate={{ x: 48, y: 45, width: width(scene.m), height: 32 }} transition={transition} rx="3" fill="var(--fill-rod-m)" stroke="var(--color-m)" strokeWidth="2" data-math-value={numeric(scene.m)} />
    {scene.m === 0 && <SceneText text="0 units: empty length" x={60} y={68} color={muted} />}
    <SceneText text={`One measuring piece: ${scene.n}`} x={48} y={113} weight={600} color="var(--color-n)" />
    <motion.rect initial={false} animate={{ x: 48, y: 128, width: width(scene.n), height: 28 }} transition={transition} rx="3" fill="var(--fill-rod-n)" stroke="var(--color-n)" strokeWidth={scene.highlight === 'divisor' ? 3 : 2} data-math-value={numeric(scene.n)} />
    <SceneText text="Fit complete pieces. Keep the leftover." x={48} y={197} color={muted} />
    {model.groups.map((group, index) => <g key={index} data-math-value={numeric(group.length)}>
      <motion.rect initial={false} animate={{ x: x(group.start), y: 213, width: width(group.length), height: 44 }} transition={transition} fill="var(--fill-rod-n)" stroke="var(--color-n)" strokeWidth={scene.highlight === 'quotient' ? 3 : 1.5} />
      {width(group.length) > 32 && <SceneText text={group.copies > 1 ? `${group.copies} × ${scene.n}` : String(scene.n)} x={x(group.start + group.length / 2)} y={241} anchor="middle" color="var(--color-n)" size={group.copies > 1 ? 17 : 14} weight={600} />}</g>)}
    {scene.r > 0 && <g data-math-value={numeric(scene.r)}><motion.rect initial={false} animate={{ x: x(scene.q * scene.n), y: 213, width: width(scene.r), height: 44 }} transition={transition} fill="var(--fill-rod-r)" stroke="var(--color-r)" strokeWidth={scene.highlight === 'remainder' ? 3 : 1.5} />
      {width(scene.r) >= 38 && <SceneText text={String(scene.r)} x={x(scene.q * scene.n + scene.r / 2)} y={241} anchor="middle" color="var(--color-r)" weight={600} />}</g>}
    {units && model.scaleMaximum <= 80 && <g aria-hidden="true">{Array.from({ length: model.scaleMaximum + 1 }, (_, index) => <line key={index} x1={x(index)} x2={x(index)} y1={261} y2={index % 5 ? 265 : 270} stroke={muted} strokeWidth="0.8" />)}</g>}
    <SceneText text={`Complete copies: ${scene.q}`} x={48} y={300} color="var(--color-n)" weight={600} />
    <SceneText text={`Leftover: ${scene.r}`} x={672} y={300} anchor="end" color={scene.r ? 'var(--color-r)' : 'var(--color-gcd)'} weight={600} />
    <SceneText text={scene.q > 12 ? 'Copies are grouped; their combined length is still to scale.' : scene.r === 0 ? 'No leftover: the measuring piece divides the whole exactly.' : scene.q === 0 ? 'The measuring piece is too long. There are no complete copies yet.' : `${scene.r} is smaller than one measuring piece of ${scene.n}.`} x={48} y={329} size={13} color={muted} />
  </SceneSvg>;
}
function RegistersScene({ scene, transition }: { scene: SceneOf<'registers'>; transition: MotionSettings }) {
  const count = scene.registers.length, columns = Math.min(4, Math.max(1, count)), cardWidth = Math.min(145, 624 / columns - 16), gap = 624 / columns;
  const positions = new Map(scene.registers.map((register, index) => [register.symbol, { x: 48 + index % columns * gap + (gap - cardWidth) / 2, y: 150 + Math.floor(index / columns) * 190 }]));
  const height = Math.max(355, 160 + Math.ceil(count / columns) * 190);
  const display = (value: LessonVariable['value']) => typeof value === 'number' ? formatSceneNumber(value) : value;
  return <SceneSvg label="Assignment moves values between named registers" height={height} description={scene.registers.map((register) => `${register.symbol} contains ${register.value}${register.previous !== undefined ? `, previously ${register.previous}` : ''}. ${register.meaning}`).join(' ')}>
    <SceneText text="The name stays. The stored value can change." x={48} y={30} color={muted} />
    {scene.arrows.map((arrow, index) => {
      const from = positions.get(arrow.from), to = positions.get(arrow.to); if (!from || !to) return null;
      const lane = 62 + index % 3 * 25, fromX = from.x + cardWidth / 2, toX = to.x + cardWidth / 2;
      return <g key={`${arrow.from}-${arrow.to}-${index}`}><path d={`M ${fromX} ${from.y - 7} V ${lane} H ${toX} V ${to.y - 18}`} stroke={colors[index % colors.length]} strokeWidth="2" fill="none" />
        <Arrow fromX={toX} fromY={to.y - 28} toX={toX} toY={to.y - 7} color={colors[index % colors.length]} />
        <rect x={(fromX + toX) / 2 - 55} y={lane - 12} width={110} height={19} fill="var(--bg-surface)" />
        <SceneText text={arrow.label ?? `${arrow.from} → ${arrow.to}`} x={(fromX + toX) / 2} y={lane + 2} anchor="middle" size={12} color={colors[index % colors.length]} /></g>;
    })}
    {scene.registers.map((register, index) => {
      const point = positions.get(register.symbol)!, changed = register.previous !== undefined && register.previous !== register.value, color = changed ? 'var(--color-gcd)' : colors[index % colors.length];
      return <g key={register.symbol}><motion.rect initial={false} animate={{ x: point.x, y: point.y, width: cardWidth, height: 120 }} transition={transition} rx="9" fill={surface} stroke={color} strokeWidth={changed ? 2.5 : 1.5} />
        <WrappedText text={register.symbol} x={point.x + cardWidth / 2} y={point.y + 24} anchor="middle" width={Math.floor(cardWidth / 8)} size={register.symbol.length > 12 ? 14 : 18} color={color} />
        {register.previous !== undefined && <SceneText text={`was ${display(register.previous)}`} x={point.x + cardWidth / 2} y={point.y + 64} size={13} color={muted} anchor="middle" />}
        <SceneText text={display(register.value)} x={point.x + cardWidth / 2} y={point.y + 101} anchor="middle" size={String(register.value).length > 8 ? 18 : 29} weight={600} />
        <WrappedText text={register.meaning} x={point.x + cardWidth / 2} y={point.y + 148} width={18} anchor="middle" size={12} /></g>;
    })}
  </SceneSvg>;
}
function GridScene({ scene, units }: { scene: SceneOf<'grid'>; units: boolean }) {
  const activeCell = scene.cells?.find((cell) => cell.active), rows = visibleSceneIndices(scene.rows, activeCell?.row ?? -1, 12), columns = visibleSceneIndices(scene.columns, activeCell?.column ?? -1, 12);
  const cellSize = Math.min(36, 554 / Math.max(columns.length, 1)), startX = Math.max(118, (720 - columns.length * cellSize) / 2), top = 74;
  const lookup = new Map(scene.cells?.map((cell) => [`${cell.row}:${cell.column}`, cell])), occupiedCount = scene.cells ? scene.cells.length : scene.rows * scene.columns;
  const compressed = rows.includes(null) || columns.includes(null), height = top + rows.length * cellSize + 85;
  return <SceneSvg label="A grid of countable cells" height={height} description={`${scene.rows} rows and ${scene.columns} columns. ${occupiedCount} occupied cells.${compressed ? ' Omitted rows or columns are marked with dots.' : ''} ${scene.caption}`}>
    <SceneText text={`${scene.rows} rows × ${scene.columns} columns`} x={48} y={28} weight={600} /><SceneText text={`${occupiedCount} occupied cells`} x={672} y={28} anchor="end" color="var(--color-gcd)" />
    {columns.map((column, index) => <SceneText key={index} text={column === null ? '⋯' : scene.columnLabels?.[column] ?? String(column + 1)} x={startX + (index + 0.5) * cellSize} y={top - 16} anchor="middle" size={12} color={muted} />)}
    {rows.map((row, rowIndex) => <g key={rowIndex}><SceneText text={row === null ? '⋮' : scene.rowLabels?.[row] ?? String(row + 1)} x={startX - 15} y={top + (rowIndex + 0.63) * cellSize} anchor="end" size={12} color={muted} />
      {columns.map((column, columnIndex) => {
        if (row === null || column === null) return <SceneText key={columnIndex} text={row === null && column === null ? '⋱' : row === null ? '⋮' : '⋯'} x={startX + (columnIndex + 0.5) * cellSize} y={top + (rowIndex + 0.64) * cellSize} anchor="middle" color={muted} size={13} interactive={false} />;
        const cell = lookup.get(`${row}:${column}`), occupied = !scene.cells || Boolean(cell), color = cell?.active ? 'var(--color-r)' : colors[Math.abs(cell?.group ?? 0) % colors.length];
        return <g key={columnIndex} data-math-value={cell?.value !== undefined ? numeric(cell.value) : undefined}>
          <rect x={startX + columnIndex * cellSize + 2} y={top + rowIndex * cellSize + 2} width={cellSize - 4} height={cellSize - 4} rx="3" stroke={occupied ? color : border} strokeWidth={cell?.active ? 2.5 : 1} fill={occupied ? color : 'none'} fillOpacity={occupied ? cell?.active ? 0.3 : 0.15 : undefined} strokeDasharray={!occupied ? '2 3' : undefined} />
          {occupied && units && ((cell?.label || (cell?.value !== undefined && String(cell.value).length <= 4)) ? <SceneText text={cell.label ?? String(cell.value)} x={startX + (columnIndex + 0.5) * cellSize} y={top + (rowIndex + 0.64) * cellSize} anchor="middle" size={cellSize > 30 ? 13 : 10} color={color} /> : <circle cx={startX + (columnIndex + 0.5) * cellSize} cy={top + (rowIndex + 0.5) * cellSize} r="3" fill={color} />)}</g>;
      })}</g>)}
    <SceneText text={compressed ? '⋯ marks omitted cells. Labels keep their original indices.' : 'Outlined empty cells do not contribute to the count.'} x={48} y={height - 40} size={13} color={muted} />
  </SceneSvg>;
}
function NumberLineScene({ scene, transition }: { scene: SceneOf<'number-line'>; transition: MotionSettings }) {
  const position = (value: number) => 68 + axisPosition(value, scene.min, scene.max, scene.logarithmic) * 584;
  const uniquePoints = [...new Set(scene.points.map((point) => point.value))].sort((a, b) => a - b);
  const ticks = scene.logarithmic && uniquePoints.length >= 2 && uniquePoints.length <= 10 ? [...new Set([scene.min, ...uniquePoints, scene.max])].sort((a, b) => a - b) : axisTicks(scene.min, scene.max, scene.logarithmic);
  const jumps = scene.jumps ?? [], axisY = 122 + Math.min(jumps.length, 6) * 28;
  const lanes: { left: number; right: number }[][] = [], laneHeights: number[] = [];
  const labels = scene.points.map((point) => {
    const x = position(point.value), size = point.active ? 15 : 13, lines = wrapSceneText(point.label, 24);
    const width = Math.max(...lines.map((line) => line.length), 1) * size * .64;
    const anchor = x < 140 ? 'start' as const : x > 580 ? 'end' as const : 'middle' as const;
    const labelX = Math.max(48 + (anchor === 'end' ? width : anchor === 'middle' ? width / 2 : 0), Math.min(672 - (anchor === 'start' ? width : anchor === 'middle' ? width / 2 : 0), x));
    const left = labelX - (anchor === 'end' ? width : anchor === 'middle' ? width / 2 : 0), right = left + width;
    let lane = lanes.findIndex((used) => used.every((other) => right + 14 < other.left || left - 14 > other.right));
    if (lane < 0) { lane = lanes.length; lanes.push([]); laneHeights.push(0); }
    lanes[lane].push({ left, right }); laneHeights[lane] = Math.max(laneHeights[lane], lines.length * (size + 5) + 14);
    return { x, labelX, anchor, lane, size };
  });
  const labelY = (lane: number) => axisY + 64 + laneHeights.slice(0, lane).reduce((sum, value) => sum + value, 0);
  const height = axisY + 80 + laneHeights.reduce((sum, value) => sum + value, 0);
  return <SceneSvg label={scene.logarithmic ? 'Logarithmic number line' : 'Number line with directed jumps'} height={height} description={`${scene.logarithmic ? 'Equal distance means equal ratio.' : 'Equal distance means equal difference.'} Bounds ${scene.min} to ${scene.max}. ${scene.points.map((point) => `${point.label}: ${point.value}`).join('. ')}.`}>
    <SceneText text={scene.logarithmic ? 'Equal spaces show equal ratios' : 'Equal spaces show equal differences'} x={48} y={30} weight={600} />
    {jumps.map((jump, index) => {
      const from = position(jump.from), to = position(jump.to), lift = 42 + index % 6 * 28;
      return <g key={`${index}-${jump.from}-${jump.to}`}><Arrow fromX={from} fromY={axisY - 12} toX={to} toY={axisY - 12} bend={-lift * 2} color={colors[index % colors.length]} />
        <SceneText text={jump.label ?? (scene.logarithmic ? `× ${formatSceneNumber(jump.to / jump.from)}` : `${jump.to - jump.from >= 0 ? '+' : ''}${formatSceneNumber(jump.to - jump.from)}`)} x={(from + to) / 2} y={axisY - lift - 21} anchor="middle" color={colors[index % colors.length]} size={13} weight={600} /></g>;
    })}
    <Arrow fromX={56} fromY={axisY} toX={665} toY={axisY} color={muted} />
    {ticks.map((tick, index) => <g key={`${tick}-${index}`}><line x1={position(tick)} x2={position(tick)} y1={axisY - 6} y2={axisY + 8} stroke={muted} /><SceneText text={formatSceneNumber(tick)} x={position(tick)} y={axisY + 28} anchor="middle" size={12} color={muted} /></g>)}
    {scene.points.map((point, index) => {
      const { x, lane, labelX, anchor, size } = labels[index], y = labelY(lane);
      return <g key={index}><motion.circle initial={false} animate={{ cx: x, cy: axisY, r: point.active ? 7 : 5 }} transition={transition} fill={colors[index % colors.length]} stroke="var(--bg-surface)" strokeWidth="2" data-math-value={numeric(point.value)} />
        <line x1={x} x2={x} y1={axisY + 10} y2={y - 16} stroke={colors[index % colors.length]} strokeDasharray="3 4" />
        <WrappedText text={point.label} x={labelX} y={y} anchor={anchor} width={24} size={size} color={colors[index % colors.length]} /></g>;
    })}
  </SceneSvg>;
}
function StaircaseScene({ scene, transition, units }: { scene: SceneOf<'staircase'>; transition: MotionSettings; units: boolean }) {
  const indices = visibleSceneIndices(scene.count, scene.active, 16), base = scene.base ?? 1;
  const values = scene.values ?? Array.from({ length: scene.count }, (_, index) => base + index);
  const maximum = Math.max(1, ...values), minimum = Math.min(0, ...values);
  const width = 600 / Math.max(1, indices.length), unitHeight = 204 / (maximum - minimum), zeroY = 268 + minimum * unitHeight;
  return <SceneSvg label="Build a staircase one step at a time" height={345} description={`${scene.count} columns. ${scene.values ? 'Column heights show actual term values.' : `Step labels begin with ${base}.`} ${scene.active >= 0 ? `Focused step ${scene.active + 1}, value ${values[scene.active]}.` : 'No step is selected yet.'} Column heights show the labeled values.`}>
    <SceneText text={scene.values ? 'Column heights show the actual term values.' : 'Each new column adds one more unit of height.'} x={48} y={28} color={muted} /><line x1={48} x2={672} y1={zeroY} y2={zeroY} stroke={muted} />
    {indices.map((index, position) => {
      if (index === null) return <SceneText key={`gap-${position}`} text="⋯" x={60 + (position + 0.5) * width} y={258} anchor="middle" size={24} color={muted} />;
      const value = values[index], height = Math.abs(value) * unitHeight, color = index === scene.active ? 'var(--color-n)' : index < scene.active ? 'var(--color-m)' : muted, x = 60 + position * width + 3;
      return <g key={index}><motion.rect initial={false} animate={{ x, y: value >= 0 ? zeroY - height : zeroY, width: width - 6, height }} transition={transition} fill={color} fillOpacity={index <= scene.active ? 0.2 : 0.05} stroke={color} strokeWidth={index === scene.active ? 2.5 : 1} strokeDasharray={index > scene.active ? '4 3' : undefined} data-math-value={numeric(value)} />
        {units && value > 0 && canDrawIndividualUnits(value, 16) && Array.from({ length: value - 1 }, (_, unit) => <line key={unit} x1={x + 1} x2={x + width - 7} y1={zeroY - (unit + 1) * unitHeight} y2={zeroY - (unit + 1) * unitHeight} stroke={color} strokeOpacity="0.5" />)}
        <SceneText text={String(value)} x={x + (width - 6) / 2} y={value >= 0 ? zeroY - height - 10 : zeroY + height - 10} anchor="middle" size={14} color={color} weight={index === scene.active ? 600 : 400} />
        <SceneText text={scene.labels?.[index] ?? String(value)} x={x + (width - 6) / 2} y={291} anchor="middle" size={12} color={color} /></g>;
    })}<SceneText text={indices.includes(null) ? 'Dotted gaps mark omitted columns; heights still use the same scale.' : 'Solid: reached · highlighted: current · dashed: later steps'} x={48} y={329} size={13} color={muted} />
  </SceneSvg>;
}
function GraphScene({ scene, transition }: { scene: SceneOf<'graph'>; transition: MotionSettings }) {
  const point = (node: SceneOf<'graph'>['nodes'][number]) => ({ x: 70 + node.x * 580, y: 62 + node.y * 280 });
  const nodes = new Map(scene.nodes.map((node) => [node.id, node])), compact = scene.nodes.length > 12, radius = compact ? 21 : 29;
  const graphHeight = Math.max(420, ...scene.nodes.map((node) => point(node).y + radius + 20 + Math.ceil(node.label.length / (compact ? 12 : 18)) * 20 + 44));
  const cardWidth = (node: SceneOf<'graph'>['nodes'][number]) => Math.max(104, Math.min(172, node.label.length * 7 + 24));
  const edgeDistance = (node: SceneOf<'graph'>['nodes'][number], dx: number, dy: number, length: number) => node.value !== undefined ? radius
    : Math.min(cardWidth(node) / 2 / Math.max(0.000001, Math.abs(dx / length)), 32 / Math.max(0.000001, Math.abs(dy / length)));
  return <SceneSvg label="Follow the decisions and dependencies" height={graphHeight} description={`${scene.nodes.length} nodes. ${scene.directed === false ? 'Connections' : 'Arrows'} connect ${scene.edges.map((edge) => `${nodes.get(edge.from)?.label ?? edge.from} to ${nodes.get(edge.to)?.label ?? edge.to}${edge.label ? `, ${edge.label}` : ''}`).join('; ')}.`}>
    {scene.edges.map((edge, index) => {
      const fromNode = nodes.get(edge.from), toNode = nodes.get(edge.to); if (!fromNode || !toNode) return null;
      const from = point(fromNode), to = point(toNode), dx = to.x - from.x, dy = to.y - from.y, length = Math.hypot(dx, dy) || 1;
      const fromGap = edgeDistance(fromNode, dx, dy, length) + 5, toGap = edgeDistance(toNode, dx, dy, length) + 7;
      const fromX = from.x + dx / length * fromGap, fromY = from.y + dy / length * fromGap, toX = to.x - dx / length * toGap, toY = to.y - dy / length * toGap;
      const color = edge.active ? 'var(--color-n)' : muted, bend = scene.edges.some((other) => other.from === edge.to && other.to === edge.from) ? (edge.from < edge.to ? 44 : -44) : 0;
      return <g key={`${edge.from}-${edge.to}-${index}`} opacity={edge.active ? 1 : 0.65}>
        {scene.directed !== false ? <Arrow fromX={fromX} fromY={fromY} toX={toX} toY={toY} color={color} bend={bend} /> : <line x1={fromX} y1={fromY} x2={toX} y2={toY} stroke={color} strokeWidth="2" />}
        {edge.label && <g><rect x={(from.x + to.x) / 2 - Math.min(140, edge.label.length * 3.9)} y={(from.y + to.y) / 2 + bend / 2 - 19} width={Math.min(280, edge.label.length * 7.8)} height={20} rx="4" fill="var(--bg-surface)" />
          <SceneText text={edge.label} x={(from.x + to.x) / 2} y={(from.y + to.y) / 2 + bend / 2 - 4} anchor="middle" size={12} color={color} /></g>}</g>;
    })}
    {scene.nodes.map((node) => {
      const p = point(node), color = node.active ? 'var(--color-n)' : 'var(--color-m)';
      const rationalName = node.label.match(/^([+-]?\d+)\/([1-9]\d*)$/);
      const valueLabel = node.value === undefined ? '' : rationalName && Number(rationalName[1]) / Number(rationalName[2]) === node.value ? node.label : formatSceneNumber(node.value);
      const valueSize = Math.max(12, Math.min(compact ? 16 : 20, (radius * 2 - 10) / Math.max(1, valueLabel.length * .6)));
      const labelLines = wrapSceneText(node.label, compact ? 12 : 18).length;
      const labelY = node.y >= .15 && node.y < .5 ? p.y - radius - 16 - (labelLines - 1) * (compact ? 16 : 18) : p.y + radius + 20;
      return <g key={node.id}>{node.value === undefined ? <motion.rect initial={false} animate={{ x: p.x - cardWidth(node) / 2, y: p.y - 32, width: cardWidth(node), height: 64 }} transition={transition} rx="10" fill={surface} stroke={color} strokeWidth={node.active ? 3 : 1.5} /> : <motion.circle initial={false} animate={{ cx: p.x, cy: p.y, r: radius }} transition={transition} fill={surface} stroke={color} strokeWidth={node.active ? 3 : 1.5} data-math-value={numeric(node.value)} />}
        {node.value !== undefined ? <><SceneText text={valueLabel} x={p.x} y={p.y + 6} anchor="middle" size={valueSize} color={color} weight={600} />
          <WrappedText text={node.label} x={p.x} y={labelY} anchor="middle" width={compact ? 12 : 18} size={compact ? 11 : 13} color={node.active ? ink : muted} /></> : <WrappedText text={node.label} x={p.x} y={p.y + (node.label.length > 20 ? -5 : 5)} anchor="middle" width={20} size={14} color={color} />}</g>;
    })}<SceneText text={scene.directed === false ? 'A line pairs the quantities it connects.' : 'Follow the arrowhead. Highlighted paths show the current action.'} x={48} y={graphHeight - 9} color={muted} size={13} />
  </SceneSvg>;
}
function BalanceScene({ scene, transition }: { scene: SceneOf<'balance'>; transition: MotionSettings }) {
  const comparison = compareContributions(scene.left, scene.right), maximum = Math.max(1, ...scene.left.concat(scene.right).map((term) => Math.abs(term.value * (term.coefficient ?? 1))));
  const termsHeight = Math.max(scene.left.length, scene.right.length, 1) * 94, height = termsHeight + 168;
  return <SceneSvg label="Compare signed contributions" height={height} description={`Left total ${comparison.leftLabel}, right total ${comparison.rightLabel}. ${comparison.equal ? 'The two totals are equal.' : 'The totals are not equal.'} Bars point right for positive contributions and left for negative contributions, with a shared scale.`}>
    <SceneText text="Left expression" x={191} y={29} anchor="middle" weight={600} /><SceneText text="Right expression" x={529} y={29} anchor="middle" weight={600} /><line x1={360} x2={360} y1={45} y2={termsHeight + 44} stroke={border} />
    {[scene.left, scene.right].map((terms, side) => <g key={side}>{terms.map((term, index) => {
      const centerX = side === 0 ? 191 : 529, y = 66 + index * 94, contribution = term.value * (term.coefficient ?? 1), displacement = contribution / maximum * 116, color = contribution < 0 ? 'var(--color-r)' : 'var(--color-m)';
      return <g key={index}><SceneText text={term.label} x={centerX} y={y} anchor="middle" color={muted} size={13} /><line x1={centerX - 122} x2={centerX + 122} y1={y + 25} y2={y + 25} stroke={border} /><line x1={centerX} x2={centerX} y1={y + 12} y2={y + 40} stroke={muted} />
        <motion.rect initial={false} animate={{ x: centerX + Math.min(0, displacement), y: y + 16, width: Math.abs(displacement), height: 18 }} transition={transition} fill={color} fillOpacity="0.2" stroke={color} data-math-value={numeric(contribution)} />
        {Math.abs(displacement) >= 12 && <Arrow fromX={centerX} fromY={y + 25} toX={centerX + displacement} toY={y + 25} color={color} />}
        <SceneText text={`${term.coefficient ?? 1} × ${exactValueLabel(term)} = ${exactContributionLabel(term)}`} x={centerX} y={y + 62} anchor="middle" size={15} color={color} weight={600} /></g>;
    })}{terms.length === 0 && <SceneText text="No contributions: 0" x={side === 0 ? 191 : 529} y={80} anchor="middle" color={muted} />}</g>)}
    <rect x={50} y={termsHeight + 48} width={620} height={61} rx="8" fill={surface} stroke={comparison.equal ? 'var(--color-gcd)' : border} />
    <SceneText text={comparison.leftLabel} x={191} y={termsHeight + 89} anchor="middle" size={28} weight={600} /><SceneText text={comparison.equal ? '=' : '≠'} x={360} y={termsHeight + 90} anchor="middle" size={34} color={comparison.equal ? 'var(--color-gcd)' : 'var(--color-r)'} /><SceneText text={comparison.rightLabel} x={529} y={termsHeight + 89} anchor="middle" size={28} weight={600} />
    <SceneText text="← negative · zero at each center mark · positive →" x={360} y={height - 22} anchor="middle" size={13} color={muted} />
  </SceneSvg>;
}
function GrowthScene({ scene, transition, units }: { scene: SceneOf<'growth'>; transition: MotionSettings; units: boolean }) {
  const maximum = Math.max(1, ...scene.stages.map((stage) => Math.abs(stage.value))), allCountable = scene.stages.every((stage) => canDrawIndividualUnits(stage.value));
  const stagesRef = useRef<HTMLOListElement>(null);
  useEffect(() => {
    const rail = stagesRef.current, focused = rail?.querySelector<HTMLElement>('[aria-current="step"]');
    if (!rail || !focused) return;
    const left = focused.offsetLeft - rail.offsetLeft, right = left + focused.offsetWidth;
    if (left < rail.scrollLeft) rail.scrollLeft = left;
    else if (right > rail.scrollLeft + rail.clientWidth) rail.scrollLeft = right - rail.clientWidth;
  }, [scene.stages]);
  return <div className="curriculum-growth"><div className="curriculum-growth__heading"><span>Base <LinkedNumber value={scene.base} /></span><span>Current exponent <LinkedNumber value={scene.exponent} /></span></div>
    <ol ref={stagesRef} tabIndex={0} data-reading-scroll className="curriculum-growth__stages" aria-label="Successive quantities in the scaling process">{scene.stages.map((stage, index) => {
      const ratio = index && scene.stages[index - 1].value !== 0 ? stage.value / scene.stages[index - 1].value : null, countable = units && allCountable, barHeight = Math.abs(stage.value) / maximum * 100;
      return <li key={index} className={`curriculum-growth__stage${stage.active ? ' is-active' : ''}`} aria-current={stage.active ? 'step' : undefined}>
        {index > 0 && <span className="curriculum-growth__operation" aria-label={ratio !== null ? `multiply by ${ratio}` : 'next stage'}>{ratio !== null ? <>× <LinkedNumber value={formatSceneNumber(ratio)} /></> : '→'}</span>}
        <div className="curriculum-growth__label"><MathematicalText text={stage.label} /></div>
        <svg viewBox="0 0 116 134" role="group" aria-label={countable ? `${stage.value} individual units` : `${stage.value}. Magnitude on a shared linear scale with maximum ${maximum}.`}>
          {countable ? <UnitDots count={stage.value} x={9} y={10} columns={8} spacing={12} color={stage.active ? 'var(--color-n)' : 'var(--color-m)'} /> : <><line x1={12} x2={104} y1={stage.value < 0 ? 15 : 117} y2={stage.value < 0 ? 15 : 117} stroke={muted} />
            <motion.rect initial={false} animate={{ x: 31, y: stage.value < 0 ? 15 : 117 - barHeight, width: 54, height: barHeight }} transition={transition} fill={stage.value < 0 ? 'var(--fill-rod-r)' : 'var(--fill-rod-m)'} stroke={stage.value < 0 ? 'var(--color-r)' : 'var(--color-m)'} strokeWidth="2" data-math-value={numeric(stage.value)} />
            <SceneText text={stage.value < 0 ? 'negative ↓' : '0'} x={stage.value < 0 ? 58 : 16} y={stage.value < 0 ? 130 : 131} anchor={stage.value < 0 ? 'middle' : 'start'} size={11} color={muted} /></>}
        </svg><div className="curriculum-growth__value"><LinkedNumber value={stage.value} /></div></li>;
    })}</ol><p className="curriculum-scene__scale-note">{units && allCountable ? 'Each little square is one unit. Count the squares in a stage.' : <>All bars share one magnitude scale: <LinkedNumber value={maximum} /> reaches full height. Tiny bars keep their labeled value; downward bars are negative.</>}</p></div>;
}
function AccumulationScene({ scene, transition }: { scene: SceneOf<'accumulation'>; transition: MotionSettings }) {
  const snapshots = useMemo(() => accumulationValues(scene.terms, scene.operation), [scene.terms, scene.operation]), indices = visibleSceneIndices(scene.terms.length, scene.active, 12);
  const included = Math.max(0, Math.min(scene.active + 1, scene.terms.length)), identity = scene.operation === 'sum' ? 0 : 1, activeValues = snapshots.slice(0, included).map((value, index) => index === included - 1 ? scene.total : value);
  const minimum = Math.min(0, identity, ...activeValues), maximum = Math.max(1, identity, ...activeValues), xAt = (index: number) => 82 + (index + 1) * 565 / Math.max(1, scene.terms.length), yAt = (value: number) => 271 - (value - minimum) / (maximum - minimum) * 117;
  const railWidth = 624 / Math.max(indices.length, 1), paths = [{ x: 82, y: yAt(identity), value: identity }, ...activeValues.map((value, index) => ({ x: xAt(index), y: yAt(value), value }))];
  return <SceneSvg label={scene.operation === 'sum' ? 'Collect terms into a running sum' : 'Combine factors into a running product'} height={365} description={`${included} of ${scene.terms.length} ${scene.operation === 'sum' ? 'terms' : 'factors'} included. Starting value ${identity}. Current ${scene.operation} ${scene.total}. Point heights show running results; fractional positions use numerical approximations.`}>
    <SceneText text={scene.operation === 'sum' ? 'Add the next term to what you already have.' : 'Multiply by the next factor.'} x={48} y={29} weight={600} />
    {indices.map((index, position) => {
      if (index === null) return <SceneText key={`gap-${position}`} text="⋯" x={48 + (position + 0.5) * railWidth} y={82} anchor="middle" color={muted} />;
      const active = index === scene.active, reached = index <= scene.active, color = active ? 'var(--color-n)' : reached ? 'var(--color-m)' : muted;
      return <g key={index}><rect x={48 + position * railWidth + 3} y={49} width={railWidth - 6} height={47} rx="5" fill={surface} stroke={color} strokeWidth={active ? 2.5 : 1} strokeDasharray={reached ? undefined : '4 3'} data-math-value={numeric(scene.terms[index])} />
        <SceneText text={formatSceneNumber(scene.terms[index])} x={48 + (position + 0.5) * railWidth} y={79} anchor="middle" color={color} size={String(scene.terms[index]).length > 5 ? 13 : 20} weight={active ? 600 : 400} />
        <SceneText text={`i = ${index + (scene.indexStart ?? 1)}`} x={48 + (position + 0.5) * railWidth} y={117} anchor="middle" color={muted} size={11} /></g>;
    })}<line x1={82} x2={659} y1={yAt(0)} y2={yAt(0)} stroke={border} strokeDasharray="4 4" /><line x1={82} x2={82} y1={147} y2={283} stroke={muted} />
    <SceneText text={formatSceneNumber(maximum)} x={69} y={159} anchor="end" size={11} color={muted} /><SceneText text={formatSceneNumber(minimum)} x={69} y={276} anchor="end" size={11} color={muted} />
    {paths.slice(1).map((point, index) => <path key={index} d={`M ${paths[index].x} ${paths[index].y} H ${point.x} V ${point.y}`} fill="none" stroke="var(--color-m)" strokeWidth="2.5" />)}
    {paths.map((point, index) => <g key={index}><motion.circle initial={false} animate={{ cx: point.x, cy: point.y, r: index === paths.length - 1 ? 5 : 3.5 }} transition={transition} fill={index === paths.length - 1 ? 'var(--color-n)' : 'var(--color-m)'} data-math-value={numeric(point.value)} />
      {(paths.length <= 9 || index === 0 || index === paths.length - 1) && <SceneText text={formatSceneNumber(point.value)} x={point.x} y={point.y - 12} anchor="middle" size={12} color={index === paths.length - 1 ? 'var(--color-n)' : muted} />}</g>)}
    <SceneText text={`start at ${identity}`} x={82} y={300} size={12} color={muted} /><SceneText text={`${included} included`} x={647} y={300} anchor="end" size={12} color={muted} />
    <rect x={48} y={319} width={624} height={36} rx="6" fill={surface} /><SceneText text={`Running ${scene.operation}: ${formatSceneNumber(scene.total)}`} x={360} y={344} anchor="middle" size={19} weight={600} color="var(--color-gcd)" />
  </SceneSvg>;
}
export function CurriculumScene({ scene, isPlaying = false, playbackSpeed = 1 }: { scene: LessonScene; isPlaying?: boolean; playbackSpeed?: number }) {
  const reducedMotion = useReducedMotion(), [units, setUnits] = useState(true);
  // Manual steps and pauses settle geometry immediately. No animation runs in a loop.
  const transition = { duration: isPlaying && !reducedMotion ? 0.42 / Math.max(0.25, playbackSpeed) : 0 };
  const caption = 'caption' in scene ? scene.caption : scene.kind === 'registers' ? scene.note : undefined, hasUnits = scene.kind === 'grid' || (scene.kind === 'division' && Math.max(scene.m, scene.n) <= 80) || (scene.kind === 'staircase' && (scene.values ? scene.values.every((value) => canDrawIndividualUnits(value, 16)) : (scene.base ?? 1) + scene.count <= 17)) || (scene.kind === 'growth' && scene.stages.every((stage) => canDrawIndividualUnits(stage.value)));
  let illustration: ReactNode;
  switch (scene.kind) {
    case 'division': illustration = <DivisionScene scene={scene} transition={transition} units={units} />; break;
    case 'registers': illustration = <RegistersScene scene={scene} transition={transition} />; break;
    case 'grid': illustration = <GridScene scene={scene} units={units} />; break;
    case 'number-line': illustration = <NumberLineScene scene={scene} transition={transition} />; break;
    case 'staircase': illustration = <StaircaseScene scene={scene} transition={transition} units={units} />; break;
    case 'graph': illustration = <GraphScene scene={scene} transition={transition} />; break;
    case 'balance': illustration = <BalanceScene scene={scene} transition={transition} />; break;
    case 'growth': illustration = <GrowthScene scene={scene} transition={transition} units={units} />; break;
    case 'accumulation': illustration = <AccumulationScene scene={scene} transition={transition} />; break;
  }
  return <figure className={`curriculum-scene curriculum-scene--${scene.kind}`} data-scene-kind={scene.kind}>
    <div className="curriculum-scene__tools"><span>Numbers connect to the explanation and code.</span>{hasUnits && <button type="button" aria-pressed={units} onClick={() => setUnits((value) => !value)}>{units ? 'Hide unit marks' : 'Show unit marks'}</button>}</div>
    <div className="curriculum-scene__viewport" data-reading-scroll tabIndex={0} role="region" aria-label="Interactive diagram. Scroll horizontally if the whole diagram does not fit.">{illustration}</div>
    {caption && <figcaption><MathematicalText text={caption} /></figcaption>}<p className="curriculum-scene__keyboard-note">Focus a number and press Enter to link matching values. Escape clears the selection.</p>
  </figure>;
}
