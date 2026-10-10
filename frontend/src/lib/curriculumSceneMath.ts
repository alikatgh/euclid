/** Pure geometry models. Coordinates never change the quantity a picture represents. */
export function formatSceneNumber(value: number): string {
  if (Object.is(value, -0)) return '0';
  const raw = String(value);
  if (raw.length <= 12) return raw;
  const shorter = Number(value.toPrecision(8));
  return `${shorter === value ? '' : '≈'}${shorter}`;
}

export function divisionSegments(m: number, n: number): {
  quotient: number; remainder: number; scaleMaximum: number;
  groups: { start: number; length: number; copies: number }[];
} {
  if (!Number.isSafeInteger(m) || !Number.isSafeInteger(n) || m < 0 || n <= 0) {
    throw new RangeError('Division diagrams require a nonnegative integer and a positive integer.');
  }
  const quotient = Math.floor(m / n);
  const remainder = m % n;
  return {
    quotient, remainder, scaleMaximum: Math.max(m, n),
    groups: quotient <= 12
      ? Array.from({ length: quotient }, (_, index) => ({ start: index * n, length: n, copies: 1 }))
      : [{ start: 0, length: quotient * n, copies: quotient }],
  };
}

/** Include the focused item and both boundaries; null explicitly marks omitted items. */
export function visibleSceneIndices(count: number, focus = -1, limit = 12): (number | null)[] {
  const size = Math.max(0, Math.floor(count));
  if (size <= limit) return Array.from({ length: size }, (_, index) => index);
  const keep = new Set<number>([0, 1, 2, size - 3, size - 2, size - 1]);
  if (focus >= 0 && focus < size) {
    for (let index = Math.max(0, focus - 2); index <= Math.min(size - 1, focus + 2); index++) keep.add(index);
  } else {
    for (let index = 3; keep.size < limit && index < size - 3; index++) keep.add(index);
  }
  const sorted = [...keep].sort((left, right) => left - right);
  return sorted.flatMap((index, position) => position && index > sorted[position - 1] + 1 ? [null, index] : [index]);
}

export function axisPosition(value: number, min: number, max: number, logarithmic = false): number {
  if (!(max > min) || ![value, min, max].every(Number.isFinite)) throw new RangeError('An axis needs finite bounds with min < max.');
  if (logarithmic && (min <= 0 || value <= 0)) throw new RangeError('Logarithmic axes require positive numbers.');
  const transform = logarithmic ? Math.log : (number: number) => number;
  return (transform(value) - transform(min)) / (transform(max) - transform(min));
}

export function axisTicks(min: number, max: number, logarithmic = false): number[] {
  if (logarithmic) {
    if (min <= 0) throw new RangeError('Logarithmic axes require positive numbers.');
    const powerRange = Math.log10(max) - Math.log10(min);
    if (powerRange < 2) return [min, Math.sqrt(min * max), max];
    const stride = Math.max(1, Math.ceil(powerRange / 6));
    const values = [min];
    for (let power = Math.ceil(Math.log10(min)); power <= Math.floor(Math.log10(max)); power += stride) values.push(10 ** power);
    values.push(max);
    return [...new Set(values)].sort((left, right) => left - right);
  }
  const rough = (max - min) / 6;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 5, 10].find((factor) => factor * magnitude >= rough)! * magnitude;
  const result = [min];
  for (let multiple = Math.ceil(min / step); multiple * step < max; multiple++) {
    const tick = Number((multiple * step).toPrecision(12));
    if (tick > min) result.push(tick);
  }
  result.push(max);
  // Endpoints that are almost on a regular tick should not create overlapping labels.
  return [...new Set(result)].filter((value, index, values) => index === 0 || index === values.length - 1 ||
    (value - min > (max - min) * 0.06 && max - value > (max - min) * 0.06));
}

export function accumulationValues(terms: readonly number[], operation: 'sum' | 'product'): number[] {
  let total = operation === 'sum' ? 0 : 1;
  return terms.map((value) => {
    total = operation === 'sum' ? total + value : total * value;
    if (Object.is(total, -0)) total = 0;
    return total;
  });
}

export function contributionTotal(terms: readonly { value: number; coefficient?: number }[]): number {
  return terms.reduce((total, term) => total + term.value * (term.coefficient ?? 1), 0);
}

/** Adjacent dots are units, so only whole, reasonably sized quantities may use them. */
export function canDrawIndividualUnits(value: number, limit = 64): boolean {
  return Number.isSafeInteger(value) && value >= 0 && value <= limit;
}

interface Fraction { numerator: bigint; denominator: bigint }
type Contribution = { label?: string; value: number; coefficient?: number; exactValue?: string };
function fraction(numerator: bigint, denominator = 1n): Fraction {
  if (denominator === 0n) throw new RangeError('A fraction cannot have zero denominator.');
  if (denominator < 0n) { numerator = -numerator; denominator = -denominator; }
  let a = numerator < 0n ? -numerator : numerator, b = denominator;
  while (b) [a, b] = [b, a % b];
  return { numerator: numerator / a, denominator: denominator / a };
}
function decimalFraction(value: string): Fraction | null {
  const match = value.trim().replace('−', '-').match(/^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/);
  if (!match) return null;
  const digits = match[3] ?? '', power = Number(match[4] ?? 0) - digits.length;
  const numerator = BigInt(`${match[1]}${match[2]}${digits}`);
  return power >= 0 ? fraction(numerator * 10n ** BigInt(power)) : fraction(numerator, 10n ** BigInt(-power));
}
function valueFraction(term: Contribution): Fraction {
  if (term.exactValue !== undefined) {
    const literal = term.exactValue.trim().replace('−', '-');
    const match = literal.match(/^([+-]?\d+)\s*\/\s*([+-]?\d+)$/);
    const exact = match ? fraction(BigInt(match[1]), BigInt(match[2])) : decimalFraction(literal);
    if (!exact) throw new RangeError('Exact values must be integers, finite decimals, or fractions.');
    const approximate = Number(exact.numerator) / Number(exact.denominator);
    if (Math.abs(approximate - term.value) > Number.EPSILON * 8 * Math.max(1, Math.abs(term.value))) {
      throw new RangeError('The exact value must agree with the plotted numerical value.');
    }
    return exact;
  }
  return decimalFraction(String(term.value))!;
}
function termFraction(term: Contribution): Fraction {
  const value = valueFraction(term), coefficient = decimalFraction(String(term.coefficient ?? 1))!;
  return fraction(value.numerator * coefficient.numerator, value.denominator * coefficient.denominator);
}
function sumFractions(terms: readonly Contribution[]): Fraction {
  return terms.reduce((total, term) => {
    const value = termFraction(term);
    return fraction(total.numerator * value.denominator + value.numerator * total.denominator, total.denominator * value.denominator);
  }, fraction(0n));
}
function fractionLabel(value: Fraction): string {
  return value.denominator === 1n ? String(value.numerator) : `${value.numerator}/${value.denominator}`;
}
export function exactContributionLabel(term: Contribution): string { return fractionLabel(termFraction(term)); }
export function exactValueLabel(term: Contribution): string { return fractionLabel(valueFraction(term)); }
export function compareContributions(left: readonly Contribution[], right: readonly Contribution[]): {
  equal: boolean; leftLabel: string; rightLabel: string;
} {
  const leftTotal = sumFractions(left), rightTotal = sumFractions(right);
  return { equal: leftTotal.numerator === rightTotal.numerator && leftTotal.denominator === rightTotal.denominator,
    leftLabel: fractionLabel(leftTotal), rightLabel: fractionLabel(rightTotal) };
}
