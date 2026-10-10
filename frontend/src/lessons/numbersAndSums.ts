import type { CurriculumLesson, LessonFrame, LessonInputs, LessonScene, LessonVariable, Prediction } from '../types/curriculum';

// All prose, examples, diagrams, and questions in this file are original.
// References locate the concepts in the supplied third-edition ebook; they do
// not reproduce its pages. PDF page numbers are one-based ebook page numbers.
const source = (section: string, pages: string, topic: string) => [{
  title: 'Donald E. Knuth, The Art of Computer Programming, Volume 1, third edition',
  section,
  note: `Concept reference: ${topic}. Supplied ebook PDF pages ${pages} (one-based, not printed pagination). Original explanation and exercises.`,
}];
const integer = (inputs: LessonInputs, name: string, fallback: number, min: number, max: number) =>
  Math.min(max, Math.max(min, Math.round(Number.isFinite(inputs[name]) ? inputs[name] : fallback)));
const v = (symbol: string, value: number | string, meaning: string): LessonVariable => ({ symbol, value, meaning });
const py = (lines: string[], activeLines?: number[]): LessonFrame['code'] => ({ language: 'python', lines, activeLines: activeLines ?? [lines.length] });
const sum = (values: number[]) => values.reduce((a, b) => a + b, 0);
const gcd = (a: number, b: number): number => b ? gcd(b, a % b) : Math.abs(a);
const fraction = (p: number, q: number) => {
  const d = gcd(p, q);
  return q / d === 1 ? String(p / d) : `${p / d}/${q / d}`;
};
const fracTex = (p: number, q: number) => {
  const d = gcd(p, q);
  return q / d === 1 ? String(p / d) : `\\frac{${p / d}}{${q / d}}`;
};
const listTex = (values: number[], joiner = '+') => values.length ? values.join(joiner) : '0';
const lineScene = (points: { value: number; label: string; active?: boolean }[], caption: string, min = 0, max = 1): LessonScene =>
  ({ kind: 'number-line', min, max, points, caption });
const growth = (base: number, exponents: number[], focus: number, caption: string): LessonScene => ({
  kind: 'growth', base, exponent: focus,
  stages: exponents.map(k => ({ label: `${base}^${k}`, value: base ** k, active: k === focus })), caption,
});
const ask = (prompt: string, answer: string, distractors: [string, string], explanation: string, hint: string): Prediction => {
  // Deterministic variation prevents “always choose the middle option” from
  // substituting for a mathematical prediction, without randomizing playback.
  const correctIndex = [...prompt].reduce((total, letter) => total + letter.charCodeAt(0), 0) % 3;
  const choices: string[] = [...distractors];
  choices.splice(correctIndex, 0, answer);
  return { prompt, choices, correctIndex, explanation, hint };
};
const decimalExpansion = (p: number, q: number) => {
  const whole = Math.floor(p / q);
  let remainder = p % q;
  const digits: number[] = [];
  const seen = new Map<number, number>();
  while (remainder && !seen.has(remainder)) {
    seen.set(remainder, digits.length);
    const scaled = 10 * remainder;
    digits.push(Math.floor(scaled / q));
    remainder = scaled % q;
  }
  if (!remainder) return `${whole}${digits.length ? `.${digits.join('')}` : ''}`;
  const start = seen.get(remainder)!;
  return `${whole}.${digits.slice(0, start).join('')}(${digits.slice(start).join('')})`;
};

const rationalNumbers: CurriculumLesson = {
  id: 'numbers-and-representations', order: 11,
  title: 'Numbers and their representations',
  subtitle: 'A number is a location. A fraction or decimal is a way to name it.',
  prerequisites: ['Integer arithmetic', 'Division with a remainder'],
  objectives: ['Distinguish integers, rational numbers, and representations.', 'Interpret a numerator and a nonzero denominator.', 'Explain why a recurring decimal can be exact.'],
  sources: source('§1.2.2 Numbers, Powers, and Logarithms', '59–60', 'integers, rationals, real-number representations'),
  parameters: [
    { id: 'p', label: 'Numerator p', min: 1, max: 7, initial: 3, description: 'How many equal pieces to take.' },
    { id: 'q', label: 'Denominator q', min: 2, max: 12, initial: 8, description: 'How many equal pieces make one whole.' },
  ],
  buildFrames(inputs) {
    const p = integer(inputs, 'p', 3, 1, 7), q = integer(inputs, 'q', 8, 2, 12);
    const x = p / q, rows = Math.ceil(x), expansion = decimalExpansion(p, q);
    const repeated = expansion.includes('(');
    const vars = [v('p', p, 'numerator: pieces taken'), v('q', q, 'denominator: pieces per whole'), v('x', fraction(p, q), 'the exact rational value')];
    return [
      {
        id: 'integers', title: 'Start with whole-number positions',
        intuition: 'Zero is an anchor. Each step right adds one; each step left subtracts one. Negative integers are positions too.',
        formal: 'The integers form the set $\\mathbb Z=\\{\\ldots,-2,-1,0,1,2,\\ldots\\}$. The dots indicate that there is no first or last integer. A drawing shows only a finite window of this infinite set.',
        formula: '\\mathbb Z=\\{\\ldots,-2,-1,0,1,2,\\ldots\\}',
        reading: 'Read ℤ as “the integers.” The braces enclose a set; the dots mean that the pattern continues in both directions.',
        variables: [v('selected integer', p, 'a whole-number position')],
        scene: lineScene(Array.from({ length: p + 3 }, (_, i) => ({ value: i - 2, label: String(i - 2), active: i - 2 === p })), 'Equal integer steps; the highlighted integer follows your numerator control.', -2, p),
        code: py([`p = ${p}`, 'positions = list(range(-2, p + 1))', 'assert p in positions', 'print(positions)'], [2, 3]),
      },
      {
        id: 'equal-pieces', title: 'Make smaller units',
        intuition: `Cut each whole into ${q} equal pieces. Keep ${p} pieces. Each little cell is worth 1/${q}, so the colored cells together are worth ${fraction(p, q)}.`,
        formal: 'A rational number is a ratio $p/q$ with integer $p$ and integer $q\\ne0$. We choose $q>0$ so that a negative sign, if needed, belongs in the numerator. The denominator specifies the unit size; it is not another quantity to add.',
        formula: `x=\\frac{${p}}{${q}}=${p}\\cdot\\frac1{${q}}`,
        reading: `Read “${p} divided by ${q},” or “${p} ${q}ths.” The numerator counts pieces; the denominator says how fine the partition is.`,
        variables: vars,
        scene: { kind: 'grid', rows, columns: q, cells: Array.from({ length: p }, (_, i) => ({ row: Math.floor(i / q), column: i % q, value: 1 / q, label: `1/${q}`, active: true })), caption: `${p} selected pieces; ${q} cells per whole. Every cell has value 1/${q}.` },
        code: py(['from fractions import Fraction', `p, q = ${p}, ${q}`, 'piece = Fraction(1, q)', 'x = sum([piece] * p)', 'assert x == Fraction(p, q)', 'print(x)'], [3, 4]),
        prediction: ask(`If every piece is cut in half, which fraction names the same amount as ${p}/${q}?`, `${2 * p}/${2 * q}`, [`${p}/${2 * q}`, `${2 * p}/${q}`], `There are twice as many selected pieces and twice as many pieces per whole. Thus (${2 * p})/(${2 * q}) = ${p}/${q}; neither the amount nor its position changes.`, 'Change both the piece count and the number of pieces per whole.'),
      },
      {
        id: 'same-location', title: 'Different names, one location',
        intuition: `The names ${p}/${q} and ${2 * p}/${2 * q} point to exactly the same spot. Cutting pieces smaller changes the labels, not the amount.`,
        formal: 'For a nonzero integer $c$, $(cp)/(cq)=p/q$, because multiplying numerator and denominator by the same nonzero factor cancels. The rational numbers are denoted by $\\mathbb Q$, and every integer is rational because $m=m/1$.',
        formula: `\\frac{${p}}{${q}}=\\frac{${2 * p}}{${2 * q}}=${fracTex(p, q)},\\qquad\\mathbb Z\\subset\\mathbb Q`,
        reading: 'Read the equality signs as “the same value as.” Read the subset sign as “is contained in”: every integer is also a rational number.',
        variables: vars,
        scene: lineScene([{ value: 0, label: '0' }, { value: x, label: `${p}/${q} = ${2 * p}/${2 * q}`, active: true }, { value: Math.ceil(x), label: String(Math.ceil(x)) }], 'Equivalent fractions share one position.', 0, Math.max(1, Math.ceil(x))),
        code: py(['from fractions import Fraction', `p, q = ${p}, ${q}`, 'x = Fraction(p, q)', 'renamed = Fraction(2 * p, 2 * q)', 'assert x == renamed', 'print(x, renamed)'], [3, 4, 5]),
      },
      {
        id: 'decimal-name', title: 'Division builds a decimal name',
        intuition: `Long division gives ${expansion}. ${repeated ? 'The digits in parentheses repeat forever: this is a pattern, not a request to finish writing infinitely many digits.' : 'The remainder eventually reaches zero, so this decimal stops exactly.'}`,
        formal: 'At each digit, divide ten times the current remainder by $q$. Only the remainders $0,1,\\ldots,q-1$ can occur. Reaching zero ends the expansion; revisiting a nonzero remainder repeats the same future digits. Thus a rational decimal terminates or is eventually periodic.',
        formula: `\\frac{${p}}{${q}}=${repeated ? expansion.replace(/\((.*)\)/, '\\overline{$1}') : expansion}`,
        reading: 'A bar over digits means repeat those digits indefinitely. A finite decimal can be exact; a recurring decimal with its repeat specified can also be exact.',
        variables: [...vars, v('decimal', expansion, 'parentheses mark the repeated block')],
        scene: { kind: 'registers', registers: [v('numerator', p, 'starting amount'), v('divisor', q, 'fixed divisor'), v('decimal', expansion, 'exact decimal pattern')], arrows: [{ from: 'numerator', to: 'decimal', label: `divide by ${q}` }], note: 'The exact fraction remains available even when the decimal repeats.' },
        code: py([`p, q = ${p}, ${q}`, 'whole, remainder = divmod(p, q)', 'digits, seen = [], {}', 'while remainder and remainder not in seen:', '    seen[remainder] = len(digits)', '    digit, remainder = divmod(10 * remainder, q)', '    digits.append(str(digit))', 'if remainder:', '    split = seen[remainder]', '    tail = "".join(digits[:split]) + "(" + "".join(digits[split:]) + ")"', 'else:', '    tail = "".join(digits)', 'print(str(whole) + ("." + tail if tail else ""))'], [4, 5, 6, 7]),
      },
      {
        id: 'thirds', title: 'Why one third never needs rounding',
        intuition: 'One third is an exact sharing instruction. Writing 0.333 uses only three decimal places and leaves a tiny gap; writing 0.333… with every digit equal to 3 describes the whole value.',
        formal: 'The fraction $1/3$ is rational even though its decimal does not terminate. For the first $d$ threes, the gap to $1/3$ is exactly $1/(3\\cdot10^d)$, which tends to zero. Irrational means “not a ratio of integers,” not merely “has many digits.”',
        formula: '\\frac13=0.\\overline3,\\qquad\\frac13-\\frac{333}{1000}=\\frac1{3000}>0',
        reading: 'Read the bar over 3 as “3 recurring.” The strict inequality says the finite decimal 0.333 is smaller than one third.',
        variables: [v('exact', '1/3', 'unrounded rational'), v('finite decimal', '333/1000', 'three-digit truncation'), v('gap', '1/3000', 'exact amount missing')],
        scene: { kind: 'balance', left: [{ label: '333/1000', value: 333 / 1000, exactValue: '333/1000' }, { label: '1/3000', value: 1 / 3000, exactValue: '1/3000' }], right: [{ label: '1/3', value: 1 / 3, exactValue: '1/3' }], caption: 'The finite decimal plus its missing piece equals one third.' },
        code: py(['from fractions import Fraction', 'exact = Fraction(1, 3)', 'truncated = Fraction(333, 1000)', 'gap = exact - truncated', 'assert gap == Fraction(1, 3000)', 'print(exact, truncated, gap)'], [3, 4, 5]),
        prediction: ask('Which statement about 1/3 is correct?', 'It is rational and its decimal repeats.', ['It is irrational because its decimal never stops.', 'It equals the finite decimal 0.333 exactly.'], 'The integers 1 and 3 already provide a ratio, so 1/3 is rational. Each finite run of threes is a little too small; the infinite recurring representation denotes the exact fraction.', 'Use the definition of rational, rather than the number of written digits.'),
      },
    ];
  },
};

const positivePowers: CurriculumLesson = {
  id: 'positive-powers', order: 12, title: 'Positive powers',
  subtitle: 'The exponent counts equal factors, not additions.',
  prerequisites: ['Multiplication', 'Integer indices'],
  objectives: ['Read a base and exponent.', 'Build a positive power one multiplication at a time.', 'Derive the addition and power-of-a-power laws.'],
  sources: source('§1.2.2 Numbers, Powers, and Logarithms', '60', 'definitions of integer powers and exponent laws'),
  parameters: [
    { id: 'base', label: 'Base b', min: 2, max: 5, initial: 3, description: 'Multiply by this same factor at each step.' },
    { id: 'exponent', label: 'Exponent n', min: 2, max: 5, initial: 4, description: 'How many copies of the base appear in the product.' },
  ],
  countingNote: 'This teaching loop starts at 1 and performs n multiplications. A loop initialized at b could compute the same positive power in n−1 multiplications; visual frames are not operations.',
  buildFrames(inputs) {
    const b = integer(inputs, 'base', 3, 2, 5), n = integer(inputs, 'exponent', 4, 2, 5);
    const frames: LessonFrame[] = [{
      id: 'factors', title: 'Read the compact instruction',
      intuition: `The small ${n} says “use ${n} copies of ${b} as factors.” It does not say “multiply ${b} by ${n}.”`,
      formal: 'For a positive integer $n$, $b^n$ is the product of $n$ copies of $b$. Multiplication is associative, so grouping the factors does not change the product.',
      formula: `${b}^{${n}}=\\underbrace{${Array(n).fill(b).join('\\cdot')}}_{${n}\\text{ factors}}=${b ** n}`,
      reading: `Read “${b} to the power ${n}.” The base is ${b}; the exponent is ${n}; the value of the whole expression is ${b ** n}.`,
      variables: [v('b', b, 'repeated factor'), v('n', n, 'number of factors'), v('value', b ** n, 'product, not base times exponent')],
      scene: { kind: 'accumulation', terms: Array(n).fill(b), active: -1, total: 1, operation: 'product', caption: 'Before taking any factors, the running product is 1.' },
      code: py(['from math import prod', `base, exponent = ${b}, ${n}`, 'factors = [base] * exponent', 'product = 1', 'target = prod(factors)', 'print(factors, product, target)'], [3, 4, 5]),
    }];
    for (let k = 1; k <= n; k++) {
      const value = b ** k;
      frames.push({
        id: `multiply-${k}`, title: `Multiply by ${b}: factor ${k} of ${n}`,
        intuition: `${b ** (k - 1)} becomes ${value} when every existing unit is replaced by ${b} units. Each new factor multiplies the entire amount.`,
        formal: `After $k=${k}$ iterations, the loop invariant is $\\text{value}=b^k=${value}$. It holds initially with value 1 and is preserved because multiplying by $b$ appends exactly one factor.`,
        formula: `${b}^{${k}}=${b ** (k - 1)}\\cdot${b}=${value}`,
        reading: 'The equality reads from a compact power to the previous product times one more base, then to its numerical value.',
        variables: [v('b', b, 'base'), v('k', k, 'factors used'), v('value', value, 'running product')],
        scene: growth(b, Array.from({ length: n + 1 }, (_, i) => i), k, `Focus: ${k} factors give ${value}. Stage 0 is the starting product 1.`),
        code: py([`base, k = ${b}, ${k}`, 'value = 1', 'for _ in range(k):', '    value *= base', `assert value == ${value}`, 'print(value)'], [3, 4]),
        counters: [{ label: 'Multiplications performed', value: k, unit: 'multiplications' }],
        ...(k === 1 ? { prediction: ask(`After one more factor of ${b}, what will ${value} become?`, String(value * b), [String(value * b - 1), String(value * b + 1)], `One more exponent step appends a factor: ${value} × ${b} = ${value * b}. Addition would model a different process.`, 'Multiply the whole current amount by the base.') } : {}),
      });
    }
    const r = Math.floor(n / 2), s = n - r;
    frames.push({
      id: 'join-products', title: 'Joining factors adds exponents',
      intuition: `A group of ${r} factors and a group of ${s} factors together contain ${n} factors. Nothing new happens to the base.`,
      formal: 'For positive integer exponents $r,s$, associativity gives $b^r b^s=b^{r+s}$. The law adds the exponents only because the bases are the same. It does not say that $b^r+b^s=b^{r+s}$.',
      formula: `${b}^{${r}}\\cdot${b}^{${s}}=${b}^{${r}+${s}}=${b}^{${n}}=${b ** n}`,
      reading: 'Read “a power times a power with the same base equals that base raised to the sum of the exponents.”',
      variables: [v('r', r, 'factors in first group'), v('s', s, 'factors in second group'), v('r+s', n, 'all factors')],
      scene: { kind: 'balance', left: [{ label: `${b}^${r} × ${b}^${s}`, value: (b ** r) * (b ** s) }], right: [{ label: `${b}^${n}`, value: b ** n }], caption: 'Regrouping the same factors preserves their product.' },
      code: py([`b, r, s = ${b}, ${r}, ${s}`, 'left = (b ** r) * (b ** s)', 'right = b ** (r + s)', 'assert left == right', 'print(left, right)'], [2, 3, 4]),
    }, {
      id: 'power-of-power', title: 'Groups of factors multiply exponents',
      intuition: `Now take ${n} groups, with 2 copies of ${b} in every group. Count the factors: 2 × ${n} = ${2 * n}.`,
      formal: 'For positive integers $r,s$, $(b^r)^s=b^{rs}$: there are $s$ groups and $r$ equal factors in each group. The parentheses matter; $(b^r)^s$ is generally different from $b^{(r^s)}$.',
      formula: `(${b}^2)^{${n}}=${b}^{2\\cdot${n}}=${b}^{${2 * n}}=${b ** (2 * n)}`,
      reading: 'Read the parentheses first: square the base, then raise that result to the outer exponent.',
      variables: [v('group size', 2, 'factors per group'), v('groups', n, 'copies of the square'), v('total factors', 2 * n, 'product of the two exponents')],
      scene: { kind: 'grid', rows: n, columns: 2, caption: `${n} groups × 2 factor positions. Cells count factors; each cell is a factor ${b}, not a unit of the final value.`, cells: Array.from({ length: 2 * n }, (_, i) => ({ row: Math.floor(i / 2), column: i % 2, value: b, group: Math.floor(i / 2), active: true })) },
      code: py([`b, groups = ${b}, ${n}`, 'left = (b ** 2) ** groups', 'right = b ** (2 * groups)', 'assert left == right', 'print(left, right)'], [2, 3, 4]),
      prediction: ask(`What is the exponent when (${b}²)^${n} is written as one power of ${b}?`, String(2 * n), [String(2 * n - 1), String(2 * n + 1)], `There are ${n} groups with 2 factors each, hence ${2 * n} factors. The outer exponent repeats the entire inner product.`, 'Count factors per group times the number of groups.'),
    });
    return frames;
  },
};

const extendedPowers: CurriculumLesson = {
  id: 'zero-negative-rational-powers', order: 13, title: 'Zero, negative, and rational powers',
  subtitle: 'Keep the exponent laws consistent by undoing multiplication.',
  prerequisites: ['Positive powers', 'Fractions and reciprocals'],
  objectives: ['Explain a nonzero base to exponent zero.', 'Read a negative exponent as a reciprocal.', 'Interpret rational exponents using positive roots and respect domains.'],
  sources: source('§1.2.2 Numbers, Powers, and Logarithms', '60–61', 'zero and negative powers, positive roots, and rational exponents'),
  parameters: [
    { id: 'root', label: 'Positive root r', min: 2, max: 5, initial: 4, description: 'The base is chosen as r^q so its qth root is exact.' },
    { id: 'degree', label: 'Root degree q', min: 2, max: 3, initial: 2, description: 'Square root or cube root.' },
    { id: 'm', label: 'Numerator magnitude m', min: 1, max: 3, initial: 1, description: 'The target exponent is −m/q.' },
  ],
  buildFrames(inputs) {
    const r = integer(inputs, 'root', 4, 2, 5), q = integer(inputs, 'degree', 2, 2, 3), m = integer(inputs, 'm', 1, 1, 3), b = r ** q;
    const denom = r ** m;
    const domain = 'We use $b>0$, integer $m$, and positive integer $q$. These assumptions give a unique positive root and keep the usual exponent laws valid without branch choices.';
    return [
      {
        id: 'zero', title: 'Step backward to exponent zero',
        intuition: `Moving one exponent step forward multiplies by ${b}. Moving backward divides by ${b}. So the step before ${b} is 1.`,
        formal: `For nonzero $b$, consistency with $b^u/b^u=b^{u-u}$ forces $b^0=1$. A zero exponent is not multiplication by zero. ${domain}`,
        formula: `${b}^0=\\frac{${b}^1}{${b}}=1`,
        reading: 'Read “the base to exponent zero equals one.” The zero counts how many factors remain, not the size of the base.',
        variables: [v('b', b, 'positive base'), v('exponent', 0, 'no factors'), v('value', 1, 'multiplicative identity')],
        scene: growth(b, [2, 1, 0], 0, 'Descending exponent steps divide the value by the base.'),
        code: py([`base = ${b}`, 'value = base', 'value //= base', 'assert value == base ** 0 == 1', 'print(value)'], [3, 4]),
      },
      {
        id: 'negative', title: 'One more backward step makes a reciprocal',
        intuition: `Divide 1 by ${b}. The answer is a small positive fraction, 1/${b}; the negative sign in the exponent did not make the value negative.`,
        formal: `For a nonzero base and positive integer $n$, $b^{-n}=1/b^n$. The sign belongs to the exponent. In contrast, $-b^n$ negates the value, and $(-b)^n$ uses a negative base.`,
        formula: `${b}^{-1}=\\frac1{${b}},\\qquad ${b}^{-1}\\cdot${b}=1`,
        reading: 'Read “the base to minus one” as “the reciprocal of the base.” Do not read it as “minus the base.”',
        variables: [v('b', b, 'positive base'), v('exponent', -1, 'one inverse multiplication'), v('value', `1/${b}`, 'positive reciprocal')],
        scene: { kind: 'graph', directed: true, nodes: [{ id: 'a', label: String(b), value: b, x: 0.12, y: 0.5 }, { id: 'b', label: '1', value: 1, x: 0.5, y: 0.5 }, { id: 'c', label: `1/${b}`, value: 1 / b, x: 0.88, y: 0.5, active: true }], edges: [{ from: 'a', to: 'b', label: `÷ ${b}` }, { from: 'b', to: 'c', label: `÷ ${b}`, active: true }], caption: 'The same division rule continues past exponent zero.' },
        code: py(['from fractions import Fraction', `base = ${b}`, 'reciprocal = Fraction(1, base)', 'assert reciprocal * base == 1', 'print(reciprocal)'], [3, 4]),
        prediction: ask(`What sign does ${b}^(−1) have?`, 'Positive', ['Negative', 'Zero'], `It is 1/${b}. Both numerator and denominator are positive, so the reciprocal is positive. The minus sign tells us to undo multiplication.`, 'Rewrite the power as a fraction first.'),
      },
      {
        id: 'root', title: `A ${q}th root reverses a ${q}th power`,
        intuition: `Find the positive number that becomes ${b} after ${q} equal factors are multiplied. That number is ${r}.`,
        formal: `For $b>0$, the symbol $\\sqrt[q]{b}$ denotes the unique positive number $r$ satisfying $r^q=b$. For a square root, the symbol denotes the positive root even though the equation $z^2=b$ has both positive and negative solutions.`,
        formula: `${r}^{${q}}=${b}\\quad\\Longleftrightarrow\\quad\\sqrt[${q}]{${b}}=${b}^{1/${q}}=${r}`,
        reading: `Read the radical as “the ${q}th root of ${b}.” The exponent 1/${q} gives the same positive root.`,
        variables: [v('q', q, 'root degree'), v('b', b, 'value under the root'), v('r', r, 'unique positive root')],
        scene: { kind: 'graph', directed: true, nodes: [{ id: 'root', label: String(r), value: r, x: 0.2, y: 0.35, active: true }, { id: 'base', label: String(b), value: b, x: 0.8, y: 0.65 }], edges: [{ from: 'root', to: 'base', label: `power ${q}` }, { from: 'base', to: 'root', label: `${q}th root`, active: true }], caption: `Positive powers and positive roots undo each other: ${r}^${q} = ${b}.` },
        code: py([`base, degree = ${b}, ${q}`, 'root = next(k for k in range(1, base + 1) if k ** degree == base)', 'assert root > 0 and root ** degree == base', 'print(root)'], [2, 3]),
      },
      {
        id: 'rational', title: 'Root first, then use the numerator',
        intuition: `The denominator ${q} asks for a root. The numerator ${m} asks for ${m} copies of that root as factors.`,
        formal: `${domain} Define $b^{m/q}=(\\sqrt[q]{b})^m=\\sqrt[q]{b^m}$. Equivalent rational exponents give the same positive value; this is essential because an exponent such as $1/2$ also has the name $2/4$.`,
        formula: `${b}^{${m}/${q}}=(\\sqrt[${q}]{${b}})^{${m}}=${r}^{${m}}=${denom}`,
        reading: 'Read the exponent as one fraction. The denominator sets the root degree, and the numerator sets the power.',
        variables: [v('m', m, 'power numerator'), v('q', q, 'root denominator'), v('value', denom, 'positive rational power')],
        scene: { kind: 'graph', directed: true, nodes: [{ id: 'b', label: String(b), value: b, x: 0.12, y: 0.5 }, { id: 'r', label: String(r), value: r, x: 0.5, y: 0.5 }, { id: 'p', label: String(denom), value: denom, x: 0.88, y: 0.5, active: true }], edges: [{ from: 'b', to: 'r', label: `${q}th root` }, { from: 'r', to: 'p', label: `power ${m}`, active: true }], caption: 'Two instructions, in a safe order, using an exact integer root.' },
        code: py([`base, degree, m = ${b}, ${q}, ${m}`, 'root = next(k for k in range(1, base + 1) if k ** degree == base)', 'value = root ** m', 'assert value ** degree == base ** m', 'print(value)'], [2, 3, 4]),
      },
      {
        id: 'negative-rational', title: 'Now take the reciprocal',
        intuition: `The full instruction is: take the ${q}th root, raise it to ${m}, then turn it over. The final answer is 1/${denom}.`,
        formal: `Because the base is positive, $b^{-m/q}=1/b^{m/q}=1/(\\sqrt[q]{b})^m$. For the starting controls this is $16^{-1/2}=1/\\sqrt{16}=1/4$, not $-4$.`,
        formula: `${b}^{-${m}/${q}}=\\frac1{${b}^{${m}/${q}}}=\\frac1{${r}^{${m}}}=\\frac1{${denom}}`,
        reading: 'Read the minus sign as “take the reciprocal of the positive-exponent value.” Keep the entire fraction in the exponent.',
        variables: [v('b', b, 'base'), v('exponent', `−${m}/${q}`, 'negative rational exponent'), v('value', `1/${denom}`, 'exact reciprocal')],
        scene: { kind: 'balance', left: [{ label: `1/${denom} × ${denom}`, value: (1 / denom) * denom }], right: [{ label: '1', value: 1 }], caption: 'Multiplying by the positive-exponent value checks the reciprocal.' },
        code: py(['from fractions import Fraction', `root, m = ${r}, ${m}`, 'positive_power = root ** m', 'value = Fraction(1, positive_power)', 'assert value * positive_power == 1', 'print(value)'], [3, 4, 5]),
        prediction: ask(`What is ${b}^(−${m}/${q})?`, `1/${denom}`, [`−${denom}`, String(denom)], `The positive root is ${r}; raising it to ${m} gives ${denom}; the negative exponent then takes the reciprocal 1/${denom}.`, 'Process the root, the numerator, and the minus sign separately.'),
      },
      {
        id: 'domain', formulaBinding: 'none', title: 'Check the domain before using a law',
        intuition: 'A rule comes with a safe working area. Positive bases make all of these root and reciprocal moves unambiguous.',
        formal: 'Zero has no reciprocal, so $0^{-1}$ is undefined. A negative number has no real square root. Some negative bases do have real odd roots, but rational-exponent rewrites need extra care there. We make no general assignment to $0^0$ in this lesson; its treatment depends on context.',
        formula: `b>0,\\ q\\in\\mathbb Z_{>0}\\quad\\Longrightarrow\\quad b^{-m/q}=\\frac1{(\\sqrt[q]{b})^m}`,
        reading: 'The implication says that under the assumptions on the left, the identity on the right is valid. Assumptions are part of the mathematical statement.',
        variables: [v('b', b, 'positive: root and reciprocal are defined'), v('q', q, 'positive integer degree')],
        scene: { kind: 'registers', registers: [v('base', b, 'must be positive here'), v('degree', q, 'must be a positive integer'), v('result', `1/${denom}`, 'exact under these conditions')], arrows: [{ from: 'base', to: 'result', label: 'validated domain' }], note: 'Do not extend the displayed rule to forbidden inputs by guessing.' },
        code: py(['from fractions import Fraction', `base, degree, root, m = ${b}, ${q}, ${r}, ${m}`, 'assert base > 0 and degree >= 1', 'assert root > 0 and root ** degree == base', 'value = Fraction(1, root ** m)', 'print(value)'], [3, 4, 5]),
      },
    ];
  },
};

const logarithms: CurriculumLesson = {
  id: 'logarithms-as-inverses', order: 14, title: 'Logarithms undo powers',
  subtitle: 'A logarithm asks which exponent produced the number.',
  prerequisites: ['Positive powers', 'Zero and negative exponents'],
  objectives: ['Translate between exponential and logarithmic statements.', 'Find exact logarithms of powers.', 'State the allowed base and argument for a real logarithm.'],
  sources: source('§1.2.2 Numbers, Powers, and Logarithms', '61–62', 'logarithms as inverse powers and binary logarithm notation'),
  parameters: [
    { id: 'base', label: 'Base b', min: 2, max: 4, initial: 2, description: 'The repeated multiplication factor.' },
    { id: 'exponent', label: 'Hidden exponent n', min: 0, max: 6, initial: 5, description: 'Build a target b^n, then recover n with a logarithm.' },
  ],
  countingNote: 'The search loop counts multiplications by the base. It is an exact demonstration for the displayed targets b^n, not a general numerical logarithm routine.',
  buildFrames(inputs) {
    const b = integer(inputs, 'base', 2, 2, 4), n = integer(inputs, 'exponent', 5, 0, 6), target = b ** n;
    const frames: LessonFrame[] = [{
      id: 'question', title: 'Hide the exponent',
      intuition: `Start at 1 and multiply by ${b} until you reach ${target}. How many multiplication steps does that take? The answer is the logarithm.`,
      formal: 'For a real base $b>0$, $b\\ne1$, and argument $y>0$, $\\log_b y$ is the unique real exponent $x$ for which $b^x=y$. Our controls choose exact integer exponents so the first examples can be counted.',
      formula: `${b}^{x}=${target}\\quad\\Longleftrightarrow\\quad x=\\log_{${b}}${target}`,
      reading: `Read “logarithm to base ${b} of ${target}.” The little base belongs to the logarithm, and the argument ${target} is the result of a power.`,
      variables: [v('b', b, 'base'), v('y', target, 'target value'), v('x', '?', 'unknown exponent')],
      scene: { kind: 'registers', registers: [v('base', b, 'multiplier'), v('target', target, 'given value'), v('exponent', '?', 'value we seek')], arrows: [{ from: 'base', to: 'target', label: 'raise to unknown exponent' }], note: 'A logarithm returns an exponent, not the value of the power.' },
      code: py([`base, target = ${b}, ${target}`, 'value, steps = 1, 0', 'assert base > 0 and base != 1 and target > 0', 'print(value, steps)'], [2, 3]),
    }];
    for (let k = 0; k <= n; k++) {
      frames.push({
        id: `count-${k}`, title: k ? `${k} multiplication ${k === 1 ? 'step' : 'steps'}` : 'Before any multiplication',
        intuition: k === 0 ? `The starting value is 1. ${n === 0 ? 'It already equals the target, so the answer is zero.' : `No factors of ${b} have been used yet.`}` : `${k} factors of ${b} produce ${b ** k}. ${k === n ? `We have reached ${target}; the exponent has been found.` : `Keep going toward ${target}.`}`,
        formal: `The invariant is $\\text{value}=b^{\\text{steps}}$. Here $\\text{steps}=${k}$ and $\\text{value}=${b ** k}$. The complete search stops when its value equals the target; because $b>1$, the successive powers strictly increase. The displayed code deliberately pauses after the shown number of steps so this intermediate state can be inspected.`,
        formula: `${b}^{${k}}=${b ** k}${k === n ? `\\quad\\Longrightarrow\\quad\\log_{${b}}${target}=${n}` : ''}`,
        reading: 'The exponent is the number of multiplications from the starting value 1. At the target, read the same equation backward as a logarithm.',
        variables: [v('b', b, 'base'), v('steps', k, 'multiplications so far'), v('value', b ** k, 'current power'), v('target', target, 'stopping value')],
        scene: growth(b, Array.from({ length: n + 1 }, (_, i) => i), k, `Count exponent steps, not the sizes of the values: ${k} steps so far.`),
        code: py([`base, target, shown_steps = ${b}, ${target}, ${k}`, 'value, steps = 1, 0', 'while steps < shown_steps:', '    value *= base', '    steps += 1', 'assert value == base ** steps', 'print(value, steps)'], k === 0 ? [2] : [4, 5, 6]),
        counters: [{ label: 'Multiplications from 1', value: k, unit: 'multiplications' }],
      });
    }
    frames.push({
      id: 'inverse', title: 'Two ways to read one fact',
      intuition: `The power says where ${n} multiplication steps land. The logarithm says how many steps it took to land at ${target}.`,
      formal: 'The inverse identities are $\\log_b(b^x)=x$ for real $x$, and $b^{\\log_b y}=y$ for $y>0$, assuming $b>0$ and $b\\ne1$. Integer step-counting is an entry point; logarithms of other positive numbers may be fractional or irrational.',
      formula: `\\log_{${b}}${target}=${n},\\qquad ${b}^{\\log_{${b}}${target}}=${target}`,
      reading: `${b === 2 ? 'In Knuth’s notation, lg y means log base 2 of y.' : 'A base must be specified or established by convention; different bases generally give different logarithms.'} A logarithm is an exponent, so it can be zero or negative.`,
      variables: [v('b', b, 'base'), v('y', target, 'argument'), v('logarithm', n, 'recovered exponent')],
      scene: { kind: 'graph', directed: true, nodes: [{ id: 'exponent', label: `exponent ${n}`, value: n, x: 0.2, y: 0.4, active: true }, { id: 'power', label: `value ${target}`, value: target, x: 0.8, y: 0.6 }], edges: [{ from: 'exponent', to: 'power', label: `${b} to this power` }, { from: 'power', to: 'exponent', label: `log base ${b}`, active: true }], caption: 'The two operations go in opposite directions.' },
      code: py([`base, target = ${b}, ${target}`, 'value, exponent = 1, 0', 'while value < target:', '    value *= base', '    exponent += 1', 'assert value == target', 'print(exponent)'], [3, 4, 5, 6]),
      prediction: ask(`What is log base ${b} of ${target * b}?`, String(n + 1), [String(n), String(target * b)], `Multiplying the argument ${target} by ${b} appends one factor. The power becomes ${b}^${n + 1}, so the logarithm increases from ${n} to ${n + 1}.`, 'Count how many additional base factors are needed.'),
    }, {
      id: 'log-domain', formulaBinding: 'none', title: 'Which logarithms are allowed?',
      intuition: 'With a positive base, every power lands above zero. A real logarithm cannot ask how to reach zero or a negative number. A base of 1 gets stuck at 1 forever.',
      formal: 'For real logarithms, require $b>0$, $b\\ne1$, and $y>0$. Bases between 0 and 1 are allowed: their powers decrease as the exponent increases, but still give a unique inverse. For every valid base, $\\log_b1=0$ and $\\log_b(1/b)=-1$.',
      formula: `\\log_{${b}}1=0,\\qquad\\log_{${b}}\\frac1{${b}}=-1,\\qquad b>0,\\ b\\ne1,\\ y>0`,
      reading: 'Read each assumption before the identity. “The argument must be positive” does not mean “the logarithm must be positive.”',
      variables: [v('b', b, 'valid base'), v('argument', `1/${b}`, 'positive but below 1'), v('logarithm', -1, 'negative exponent')],
      scene: growth(b, [-1, 0, 1], -1, 'A positive argument below 1 has a negative logarithm when the base is greater than 1.'),
      code: py(['from fractions import Fraction', `base = ${b}`, 'argument = Fraction(1, base)', 'exponent = -1', 'assert Fraction(base) ** exponent == argument', 'print(argument, exponent)'], [3, 4, 5]),
      prediction: ask('Why is a real logarithm with base 1 excluded?', 'Powers of 1 cannot supply a unique inverse.', ['All powers of 1 are zero.', 'Only even exponents are allowed.'], 'Every real exponent gives 1^x = 1. There is no exponent producing another positive value, and infinitely many exponents produce 1, so a single-valued inverse logarithm cannot be defined.', 'Ask whether 1^x changes when x changes.'),
    });
    return frames;
  },
};

const logarithmLaws: CurriculumLesson = {
  id: 'log-laws-and-change-of-base', order: 15, title: 'Log laws and change of base',
  subtitle: 'Multiplication of values becomes addition of exponents.',
  prerequisites: ['Logarithms as inverse powers', 'Exponent laws'],
  objectives: ['Derive product, quotient, and power laws from exponents.', 'Change logarithm bases without changing the question.', 'Avoid applying the product law to a sum or to invalid domains.'],
  sources: source('§1.2.2 Numbers, Powers, and Logarithms', '61–62', 'product and power laws and change of base'),
  parameters: [
    { id: 'base', label: 'Base b', min: 2, max: 4, initial: 2, description: 'One common base for all logarithms in the identity.' },
    { id: 'u', label: 'First exponent u', min: 1, max: 3, initial: 3, description: 'The first argument is b^u.' },
    { id: 'v', label: 'Second exponent v', min: 1, max: 3, initial: 2, description: 'The second argument is b^v.' },
  ],
  buildFrames(inputs) {
    const b = integer(inputs, 'base', 2, 2, 4), u = integer(inputs, 'u', 3, 1, 3), w = integer(inputs, 'v', 2, 1, 3);
    const x = b ** u, y = b ** w, xy = x * y;
    const domain = 'Assume $b>0$, $b\\ne1$, and positive arguments $x,y>0$.';
    const variables = [v('b', b, 'common base'), v('x', x, 'first argument'), v('y', y, 'second argument'), v('u', u, 'logarithm of x'), v('v', w, 'logarithm of y')];
    return [
      {
        id: 'decode-two', title: 'Turn both values into exponents',
        intuition: `${x} needs ${u} factors of ${b}; ${y} needs ${w}. Keep those factor counts beside the values.`,
        formal: `${domain} Write $u=\\log_b x$ and $v=\\log_b y$. By the inverse definition, $x=b^u$ and $y=b^v$. This substitution is the whole engine behind the logarithm laws.`,
        formula: `${x}=${b}^{${u}},\\quad ${y}=${b}^{${w}}\\quad\\Longrightarrow\\quad\\log_{${b}}${x}=${u},\\quad\\log_{${b}}${y}=${w}`,
        reading: 'The logarithm returns a factor count in this integer-power example. A product of the original values will join their factor groups.',
        variables,
        scene: { kind: 'registers', registers: [v('x', x, 'first power'), v('log x', u, 'first exponent'), v('y', y, 'second power'), v('log y', w, 'second exponent')], arrows: [{ from: 'x', to: 'log x', label: `log base ${b}` }, { from: 'y', to: 'log y', label: `log base ${b}` }], note: 'Values and their logarithms are different quantities.' },
        code: py([`b, u, v = ${b}, ${u}, ${w}`, 'x, y = b ** u, b ** v', 'assert b > 0 and b != 1 and x > 0 and y > 0', 'print(x, u, y, v)'], [2, 3]),
      },
      {
        id: 'join-paths', title: 'Join the multiplication paths',
        intuition: `First take ${u} exponent steps to reach ${x}. Then take ${w} more steps, multiplying the current value by ${y}, to reach ${xy}.`,
        formal: `By the exponent law, $xy=b^u b^v=b^{u+v}$. Taking logarithms gives $\\log_b(xy)=u+v=\\log_bx+\\log_by$. The proof works for real exponents as well as these countable examples.`,
        formula: `\\log_{${b}}${x}+\\log_{${b}}${y}=${u}+${w}=${u + w}=\\log_{${b}}${xy}`,
        reading: 'Read “the log of a product is the sum of the logs,” provided all logarithms use the same valid base and their arguments are positive.',
        variables: [...variables, v('xy', xy, 'product argument'), v('u+v', u + w, 'combined exponent')],
        scene: { kind: 'number-line', min: 0, max: u + w, points: [{ value: 0, label: 'exponent 0' }, { value: u, label: `${u}: value ${x}` }, { value: u + w, label: `${u + w}: value ${xy}`, active: true }], jumps: [{ from: 0, to: u, label: `× ${x}` }, { from: u, to: u + w, label: `× ${y}` }], caption: 'The axis measures exponents. Equal exponent steps represent multiplication, not equal changes in the original values.' },
        code: py([`b, u, v = ${b}, ${u}, ${w}`, 'x, y = b ** u, b ** v', 'product = x * y', 'combined_exponent = u + v', 'assert product == b ** combined_exponent', 'print(product, combined_exponent)'], [3, 4, 5]),
        prediction: ask(`What is log base ${b} of the product ${x} × ${y}?`, String(u + w), [String(u + w + 1), String(xy)], `Write ${x} = ${b}^${u} and ${y} = ${b}^${w}. Their product is ${b}^(${u}+${w}), so its logarithm is ${u + w}.`, 'Join the exponents; do not multiply the logarithms.'),
      },
      {
        id: 'quotient', title: 'Undoing factors subtracts logarithms',
        intuition: `Dividing ${x} by ${y} removes ${w} exponent steps from ${u}. The result may be below 1, and its logarithm may be negative.`,
        formal: `${domain} Since $x/y=b^u/b^v=b^{u-v}$, $\\log_b(x/y)=\\log_bx-\\log_by$. Positive arguments are still required even when the result of the logarithm is negative.`,
        formula: `\\log_{${b}}\\left(\\frac{${x}}{${y}}\\right)=${u}-${w}=${u - w}`,
        reading: 'The fraction is the argument of the logarithm. Subtraction appears between logarithms because division subtracts exponents.',
        variables: [...variables, v('quotient', fraction(x, y), 'positive ratio'), v('u−v', u - w, 'possibly negative logarithm')],
        scene: { kind: 'graph', directed: true, nodes: [{ id: 'first', label: `exponent ${u}`, value: u, x: 0.2, y: 0.5 }, { id: 'result', label: `exponent ${u - w}`, value: u - w, x: 0.8, y: 0.5, active: true }], edges: [{ from: 'first', to: 'result', label: `subtract ${w}`, active: true }], caption: `The value is divided by ${y}; its exponent is decreased by ${w}.` },
        code: py(['from fractions import Fraction', `b, u, v = ${b}, ${u}, ${w}`, 'quotient = Fraction(b ** u, b ** v)', 'exponent = u - v', 'assert quotient == Fraction(b) ** exponent', 'print(quotient, exponent)'], [3, 4, 5]),
      },
      {
        id: 'power', title: 'A power stretches the exponent',
        intuition: `Squaring ${x} means joining two copies of its ${u}-factor group. The logarithm therefore doubles to ${2 * u}.`,
        formal: 'If $x>0$, the power law is $\\log_b(x^r)=r\\log_bx$ for real $r$ and a valid logarithm base. Indeed, writing $x=b^u$ yields $x^r=b^{ur}$, whose logarithm is $ur$.',
        formula: `\\log_{${b}}(${x}^2)=2\\log_{${b}}${x}=2\\cdot${u}=${2 * u}`,
        reading: 'The exponent on the argument becomes a multiplier of its logarithm. It does not become an exponent on the logarithm.',
        variables: [...variables, v('r', 2, 'power applied to the argument'), v('r u', 2 * u, 'new logarithm')],
        scene: growth(b, [0, u, 2 * u], 2 * u, `Doubling the exponent squares the argument: ${x}² = ${x * x}.`),
        code: py([`b, u = ${b}, ${u}`, 'x = b ** u', 'squared_argument = x ** 2', 'new_exponent = 2 * u', 'assert squared_argument == b ** new_exponent', 'print(squared_argument, new_exponent)'], [3, 4, 5]),
      },
      {
        id: 'change-base', title: 'Change the measuring unit of the exponent',
        intuition: 'A calculator may have a natural-log button but no button for your chosen base. Divide two natural logs to translate back to the exponent you wanted.',
        formal: 'For valid bases $b,c$ and $x>0$, let $z=\\log_bx$. From $x=b^z$, take logs to base $c$: $\\log_cx=z\\log_cb$. Since $b\\ne1$, $\\log_cb\\ne0$, so $\\log_bx=\\log_cx/\\log_cb$. The base in the denominator is the desired base, not the argument.',
        formula: `\\log_{${b}}${x}=\\frac{\\ln ${x}}{\\ln ${b}}=${u},\\qquad\\ln t=\\log_e t`,
        reading: 'Read “natural log of the argument divided by natural log of the desired base.” Both logarithms in the ratio use the same auxiliary base.',
        variables: [v('x', x, 'argument'), v('b', b, 'desired base'), v('logarithm', u, 'exact mathematical answer')],
        scene: { kind: 'balance', left: [{ label: `ln(${x}) / ln(${b})`, value: u, exactValue: String(u) }], right: [{ label: String(u), value: u }], caption: 'The identity is exact; a floating-point calculator evaluates the ratio approximately.' },
        code: py(['from math import log, isclose', `base, x = ${b}, ${x}`, 'computed = log(x) / log(base)', `assert isclose(computed, ${u}, rel_tol=1e-12)`, 'print(computed)'], [3, 4]),
        prediction: ask(`Which calculator expression gives log base ${b} of ${xy}?`, `ln(${xy}) / ln(${b})`, [`ln(${b}) / ln(${xy})`, `ln(${xy}) − ln(${b})`], `Change of base divides the log of the argument ${xy} by the log of the desired base ${b}. The result is ${u + w}; reversing the ratio would invert that number.`, 'The argument stays on top; the desired base goes underneath.'),
      },
      {
        id: 'not-a-sum', title: 'A product law is not a sum law',
        intuition: `Combining ${x} and ${y} by addition gives ${x + y}. Combining them by multiplication gives ${xy}. Those are different instructions, so do not swap them inside a logarithm.`,
        formal: `${domain} The universally valid identity is $\\log_b(xy)=\\log_bx+\\log_by$. There is no corresponding general rule $\\log_b(x+y)=\\log_bx+\\log_by$. Some specially chosen numbers can make these expressions coincide accidentally, which still does not prove a law.`,
        formula: `\\log_b(xy)=\\log_bx+\\log_by;\\qquad\\log_2(2+8)=\\log_2 10\\ne4=\\log_2 2+\\log_2 8`,
        reading: 'Parentheses tell you whether the argument is a product or a sum. A single counterexample disproves a claim that an identity holds for all positive arguments.',
        variables: [v('sum argument', 10, '2 + 8'), v('product argument', 16, '2 × 8'), v('product log', 4, 'log base 2 of 16')],
        scene: lineScene([{ value: 8, label: '2³ = 8' }, { value: 10, label: '2 + 8 = 10', active: true }, { value: 16, label: '2 × 8 = 16 = 2⁴' }], 'The sum 10 lies between 2³ and 2⁴, so its base-2 logarithm lies strictly between 3 and 4.', 8, 16),
        code: py(['from math import log2', 'sum_argument = 2 + 8', 'product_argument = 2 * 8', 'assert 3 < log2(sum_argument) < 4', 'assert log2(product_argument) == 4', 'print(log2(sum_argument), log2(product_argument))'], [3, 4, 5]),
      },
    ];
  },
};

const roundedComputation: CurriculumLesson = {
  id: 'exact-and-rounded-computation', order: 16, title: 'Exact values, rounded calculations',
  subtitle: 'Small changes can accumulate when a rounded number is reused.',
  prerequisites: ['Rational representations', 'Powers of ten'],
  objectives: ['Distinguish an exact value from its decimal approximation.', 'Compare rounding each piece with rounding a final result.', 'Compute an exact error and a useful bound.'],
  sources: source('§1.2.2 Numbers, Powers, and Logarithms', '64–65', 'finite-accuracy computation and propagation of rounding error; the strip example here is original'),
  parameters: [
    { id: 'whole', label: 'Total length p', min: 1, max: 5, initial: 1, description: 'Exact total length, divided into equal pieces.' },
    { id: 'pieces', label: 'Equal pieces q', min: 3, max: 9, initial: 7, description: 'Each exact piece has length p/q.' },
    { id: 'digits', label: 'Decimal places d', min: 1, max: 3, initial: 2, description: 'Round each positive piece to nearest, with ties rounded upward.' },
  ],
  buildFrames(inputs) {
    const p = integer(inputs, 'whole', 1, 1, 5), q = integer(inputs, 'pieces', 7, 3, 9), d = integer(inputs, 'digits', 2, 1, 3);
    const scale = 10 ** d;
    // Positive round-half-up using integer arithmetic, not a binary float tie.
    const units = Math.floor((2 * p * scale + q) / (2 * q));
    const rounded = units / scale, totalUnits = q * units, approxTotal = totalUnits / scale;
    const deltaUnits = totalUnits - p * scale, errorUnits = Math.abs(deltaUnits);
    const display = (u: number) => (u / scale).toFixed(d);
    const direction = deltaUnits < 0 ? 'too short' : deltaUnits > 0 ? 'too long' : 'exact in this case';
    const baseCode = ['from fractions import Fraction', `p, q, digits = ${p}, ${q}, ${d}`, 'scale = 10 ** digits', 'piece = Fraction(p, q)', 'units = (2 * p * scale + q) // (2 * q)', 'rounded = Fraction(units, scale)'];
    return [
      {
        id: 'exact-plan', title: 'Keep the original amount exact',
        intuition: `A strip ${p} units long is shared into ${q} equal pieces. One piece is exactly ${fraction(p, q)} units, whether or not its decimal stops.`,
        formal: `The exact value is $x=p/q$. Rational arithmetic stores the integer numerator and denominator, so no rounding is required. This is a model of the chosen lengths; measurement uncertainty would be a separate issue.`,
        formula: `x=\\frac{${p}}{${q}},\\qquad ${q}x=${q}\\cdot\\frac{${p}}{${q}}=${p}`,
        reading: 'The equality sign means exactly equal. A fraction can remain exact even when a calculator shows only a finite decimal.',
        variables: [v('p', p, 'exact whole length'), v('q', q, 'equal pieces'), v('x', fraction(p, q), 'exact length per piece')],
        scene: { kind: 'accumulation', terms: Array(q).fill(p / q), active: q - 1, total: p, operation: 'sum', caption: `${q} exact pieces of ${fraction(p, q)} make ${p}. Decimal labels in a drawing do not replace this exact fraction.` },
        code: py(baseCode.slice(0, 4).concat(['exact_total = q * piece', 'assert exact_total == p', 'print(piece, exact_total)']), [4, 5, 6]),
      },
      {
        id: 'round-piece', title: 'Place the piece on a decimal grid',
        intuition: `With ${d} decimal places, the allowed labels are spaced by 1/${scale}. The nearest label for ${fraction(p, q)} is ${display(units)}.`,
        formal: `Let $\\widehat x$ be $x$ rounded to the nearest multiple of $10^{-d}$, with positive halfway cases rounded upward. Then $|\\widehat x-x|\\le\\tfrac12 10^{-d}$. The hat marks an approximation, not a new exact name for $x$ unless the rounding error happens to be zero.`,
        formula: `x=${fracTex(p, q)},\\qquad\\widehat x=${display(units)},\\qquad|\\widehat x-x|=${fracTex(Math.abs(units * q - p * scale), scale * q)}`,
        reading: 'Read x-hat as “the rounded version of x.” The vertical bars mean absolute value: the size of the difference regardless of direction.',
        variables: [v('x', fraction(p, q), 'exact piece'), v('x̂', display(units), 'rounded decimal piece'), v('d', d, 'decimal places')],
        scene: lineScene([{ value: p / q, label: `exact ${fraction(p, q)}`, active: true }, { value: rounded, label: `rounded ${display(units)}` }], 'A magnified interval around the piece length makes a small rounding gap visible.', Math.min(p / q, rounded) - 0.6 / scale, Math.max(p / q, rounded) + 0.6 / scale),
        code: py(baseCode.concat(['piece_error = abs(rounded - piece)', 'assert piece_error <= Fraction(1, 2 * scale)', 'print(rounded, piece_error)']), [5, 6, 7, 8]),
        prediction: ask(`If each of the ${q} pieces is recorded as ${display(units)}, what total will those records give?`, display(totalUnits), [display(totalUnits + 1), display(totalUnits + 2)], `The same rounded value is used ${q} times: ${q} × ${display(units)} = ${display(totalUnits)}. This calculation answers what the records sum to, not what the exact original strip measures.`, 'Multiply the rounded piece length by the number of pieces.'),
      },
      {
        id: 'reuse-rounded', title: 'Reuse the rounded value',
        intuition: `Add ${q} copies of the recorded piece ${display(units)}. Their total is ${display(totalUnits)}, which is ${direction}.`,
        formal: 'If every exact piece $x$ is replaced by the same rounded value $\\widehat x$, the resulting total is $q\\widehat x$. Its signed error is $q\\widehat x-qx=q(\\widehat x-x)$: in this example the individual errors have the same sign, so they reinforce each other.',
        formula: `\\widehat T=${q}\\widehat x=${q}\\cdot${display(units)}=${display(totalUnits)},\\qquad T=${p}`,
        reading: 'T-hat denotes the total built from rounded pieces. T denotes the exact total. Their difference is the accumulated error.',
        variables: [v('q', q, 'reused pieces'), v('T̂', display(totalUnits), 'sum of rounded pieces'), v('T', p, 'exact original length')],
        scene: { kind: 'accumulation', terms: Array(q).fill(rounded), active: q - 1, total: approxTotal, operation: 'sum', caption: `${q} recorded pieces accumulate to ${display(totalUnits)}; the exact total is ${p}.` },
        code: py(baseCode.concat(['rounded_total = sum([rounded] * q)', `assert rounded_total == Fraction(${totalUnits}, ${scale})`, 'print(rounded_total)']), [7, 8]),
      },
      {
        id: 'compare-routes', title: 'Compare two calculation routes',
        intuition: `Keeping the fraction until the pieces are combined gives ${p}. Rounding first gives ${display(totalUnits)}. ${errorUnits ? 'The order of these two actions matters.' : 'For these controls both routes agree; not every rounding operation creates an error.'}`,
        formal: 'In general, rounding a sum need not equal summing rounded terms. Retaining exact arithmetic, or carrying extra working precision and rounding at the end, avoids this particular repeated-rounding error. It does not eliminate every possible numerical error in every algorithm.',
        formula: `\\underbrace{${q}\\cdot\\frac{${p}}{${q}}}_{\\text{combine exactly}}=${p},\\qquad\\underbrace{${q}\\cdot${display(units)}}_{\\text{round each first}}=${display(totalUnits)}`,
        reading: 'The braces identify two procedures. A displayed decimal is an exact record of the rounded value, while its relation to the original value may be approximate.',
        variables: [v('exact route', p, 'combine before rounding'), v('rounded route', display(totalUnits), 'round every piece first'), v('difference', fraction(errorUnits, scale), 'absolute difference')],
        scene: { kind: 'balance', left: [{ label: `exact total ${p}`, value: p }], right: [{ label: `rounded total ${display(totalUnits)}`, value: approxTotal }], caption: errorUnits ? 'These totals are unequal: the difference comes from rounding the pieces before adding.' : 'The two routes agree for these chosen inputs.' },
        code: py(baseCode.concat(['exact_total = q * piece', 'rounded_total = q * rounded', 'error = abs(rounded_total - exact_total)', 'print(exact_total, rounded_total, error)']), [7, 8, 9]),
      },
      {
        id: 'error-bound', title: 'Measure the error and bound it',
        intuition: `Each piece can miss by at most half a decimal-grid step. Even if all ${q} errors lean the same way, the total miss is at most ${fraction(q, 2 * scale)}. The actual miss here is ${fraction(errorUnits, scale)}.`,
        formal: 'The triangle inequality gives $|\\sum_i e_i|\\le\\sum_i|e_i|$. With $q$ round-to-nearest errors each at most $1/(2\\cdot10^d)$, the total absolute error is at most $q/(2\\cdot10^d)$. This is a guaranteed bound, not a prediction that every calculation reaches it.',
        formula: `|\\widehat T-T|=${fracTex(errorUnits, scale)}\\le\\frac{${q}}{2\\cdot10^{${d}}}=${fracTex(q, 2 * scale)}`,
        reading: 'Read “the absolute total error is at most” the quantity on the right. A bound can be correct even when the actual error is much smaller or zero.',
        variables: [v('actual error', fraction(errorUnits, scale), 'computed exactly'), v('error bound', fraction(q, 2 * scale), 'guaranteed upper bound'), v('d', d, 'working decimal places')],
        scene: lineScene([{ value: 0, label: '0' }, { value: errorUnits / scale, label: `actual ${fraction(errorUnits, scale)}`, active: true }, { value: q / (2 * scale), label: `bound ${fraction(q, 2 * scale)}` }], 'The actual nonnegative error stays inside the guaranteed interval.', 0, q / (2 * scale)),
        code: py(baseCode.concat(['actual_error = abs(q * rounded - p)', 'bound = Fraction(q, 2 * scale)', 'assert actual_error <= bound', 'print(actual_error, bound)']), [7, 8, 9]),
        prediction: ask('What happens to this guaranteed error bound if you keep one more decimal place?', 'It becomes ten times smaller.', ['It always becomes zero.', 'It becomes ten times larger.'], 'The denominator of q/(2 × 10^d) grows by a factor of 10 when d increases by 1, so the bound is divided by 10. The actual error can behave differently and need not be nonzero.', 'Compare 10^(d+1) with 10^d.'),
      },
    ];
  },
};

const finiteSums: CurriculumLesson = {
  id: 'finite-sums', order: 17, title: 'Read and build a finite sum',
  subtitle: 'Sigma is a compact instruction: choose indices, make terms, add.',
  prerequisites: ['Integer indices', 'Simple expressions'],
  objectives: ['Read the index, bounds, and summand of a sigma expression.', 'Trace a running total without off-by-one errors.', 'Explain why an empty sum has value zero.'],
  sources: source('§1.2.3 Sums and Products', '68–69', 'finite sums, dummy indices, and the empty-sum convention'),
  parameters: [{ id: 'n', label: 'Upper limit n', min: 0, max: 6, initial: 4, description: 'Include every integer k from 1 through n; n = 0 gives no terms.' }],
  countingNote: 'The displayed loop starts from total = 0 and performs one addition per included term. With n terms it performs n accumulator additions; evaluating 2k+1 is separate work.',
  buildFrames(inputs) {
    const n = integer(inputs, 'n', 4, 0, 6), terms = Array.from({ length: n }, (_, i) => 2 * (i + 1) + 1), total = sum(terms);
    const vars = [v('n', n, 'inclusive upper limit'), v('terms', n, 'number of allowed indices'), v('S', total, 'completed total')];
    const frames: LessonFrame[] = [{
      id: 'read-sigma', title: 'Read the four parts of sigma',
      intuition: `The large sigma is an “add these” sign. Start the counter k at 1, stop at ${n}, and use each counter value in the recipe 2k + 1.`,
      formal: `In $\\sum_{k=1}^{n}(2k+1)$, $k$ is the index, 1 is the lower limit, $n$ is the upper limit, and $2k+1$ is the summand. Both endpoints are included when $n\\ge1$. When $n=0$, no integer satisfies $1\\le k\\le0$.`,
      formula: `S=\\sum_{k=1}^{${n}}(2k+1)=${listTex(terms)}=${total}`,
      reading: `Read “the sum, for k from 1 through ${n}, of two k plus one.” The index is a temporary input to the summand, not another term to add.`,
      variables: vars,
      scene: { kind: 'staircase', count: n, active: -1, base: 1, labels: terms.map((term, i) => `k=${i + 1}: ${term}`), caption: n ? `${n} allowed indices produce ${n} terms. The highest index is included.` : 'No allowed index: there are no stairs and no terms.' },
      code: py([`n = ${n}`, 'indices = list(range(1, n + 1))', 'terms = [2 * k + 1 for k in indices]', 'print(indices, terms)'], [2, 3]),
      prediction: ask(n ? `Which is the last term when k reaches ${n}?` : 'How many terms have indices from 1 through 0?', n ? String(2 * n + 1) : '0', n ? [String(2 * n), String(2 * n + 2)] : ['1', '2'], n ? `Substitute the included upper endpoint k = ${n} into the summand: 2 × ${n} + 1 = ${2 * n + 1}. The upper endpoint is not skipped.` : 'No integer is at least 1 and at most 0. Therefore the index set is empty and the loop visits no terms.', n ? 'Use the upper bound as the input to 2k + 1.' : 'Look for an integer that satisfies both bounds.'),
    }, {
      id: 'initialize-sum', title: 'Begin with nothing collected',
      intuition: 'An empty basket has total zero. That starting value lets every later step simply add its next term.',
      formal: 'The accumulator begins at the additive identity 0. Before the first iteration, it equals the sum over the empty set of already-visited indices. Adding zero to a number leaves that number unchanged.',
      formula: 'S_0=0',
      reading: 'Read S-sub-zero as “the running sum before any terms.” A subscript labels a state; it is not an exponent.',
      variables: [v('visited terms', 0, 'nothing added yet'), v('S₀', 0, 'initial accumulator')],
      scene: { kind: 'accumulation', terms, active: -1, total: 0, operation: 'sum', caption: 'All terms are waiting; the current total is 0.' },
      code: py([`n = ${n}`, 'total = 0', 'visited = 0', 'print(visited, total)'], [2, 3]),
      counters: [{ label: 'Accumulator additions', value: 0, unit: 'additions' }],
    }];
    let partial = 0;
    for (let k = 1; k <= n; k++) {
      const previous = partial, term = 2 * k + 1;
      partial += term;
      frames.push({
        id: `sum-term-${k}`, title: `Use k = ${k}, then add ${term}`,
        intuition: `The recipe turns ${k} into ${term}. Add that term to the old total ${previous}; the basket now contains ${partial}.`,
        formal: `After visiting index $k=${k}$, the invariant is $S_k=\\sum_{j=1}^{k}(2j+1)$. The update $S_k=S_{k-1}+(2k+1)$ preserves it by including exactly the next term once.`,
        formula: `S_{${k}}=S_{${k - 1}}+(2\\cdot${k}+1)=${previous}+${term}=${partial}`,
        reading: 'Separate the index k, the term 2k+1, and the running sum. They are three different values even when a coincidence makes two of them equal.',
        variables: [v('k', k, 'current index'), v('term', term, 'summand evaluated at k'), v('previous', previous, 'sum before this term'), v('total', partial, 'sum including this term')],
        scene: { kind: 'accumulation', terms, active: k - 1, total: partial, operation: 'sum', caption: `The first ${k} terms have been included exactly once.` },
        code: py([`shown_k = ${k}`, 'total = 0', 'for k in range(1, shown_k + 1):', '    term = 2 * k + 1', '    total += term', `assert total == ${partial}`, 'print(k, term, total)'], [4, 5]),
        counters: [{ label: 'Accumulator additions', value: k, unit: 'additions' }],
      });
    }
    frames.push({
      id: 'completed-sum', title: 'The total and its invariant agree',
      intuition: `Every allowed index has had its turn. The total is ${total}. The next index would make a new term, not change one already counted.`,
      formal: 'A useful closed form is $\\sum_{k=1}^{n}(2k+1)=n(n+2)$ for integer $n\\ge0$. A short induction verifies it: the base case is $0=0(0+2)$; adding the next term $2n+3$ to $n(n+2)$ gives $(n+1)(n+3)$.',
      formula: `\\sum_{k=1}^{${n}}(2k+1)=${n}(${n}+2)=${total}`,
      reading: 'A closed form gives the total directly from n. It does not change which terms the sigma originally specified.',
      variables: vars,
      scene: { kind: 'balance', left: terms.map((term, i) => ({ label: `term ${i + 1}: ${term}`, value: term })), right: [{ label: `${n}(${n}+2)`, value: n * (n + 2) }], caption: 'The term-by-term sum and the independently derived formula have equal values.' },
      code: py([`n = ${n}`, 'direct = sum(2 * k + 1 for k in range(1, n + 1))', 'closed = n * (n + 2)', 'assert direct == closed', 'print(direct, closed)'], [2, 3, 4]),
      prediction: ask(`If the upper limit grows from ${n} to ${n + 1}, how much must be added to ${total}?`, String(2 * (n + 1) + 1), [String(n + 1), String(2 * (n + 1))], `The newly included index is k = ${n + 1}. Its term is 2 × ${n + 1} + 1 = ${2 * (n + 1) + 1}; all previous terms stay unchanged.`, 'Evaluate the summand at the new index, rather than adding the index itself.'),
    }, {
      id: 'empty-sum', title: 'Why the empty sum is zero',
      intuition: 'If there are no terms to put in the basket, its total stays at the starting value. Nothing goes wrong; the loop simply does no work.',
      formal: 'The sum over an empty index set is defined to be 0. This convention preserves identities such as $\\sum_{k=1}^{n+1}a_k=\\sum_{k=1}^{n}a_k+a_{n+1}$ when $n=0$. It is not the same as adding a single term whose index happens to be zero.',
      formula: '\\sum_{k=1}^{0}(2k+1)=0,\\qquad\\sum_{k=0}^{0}(2k+1)=1',
      reading: 'The first sum has no admissible index; the second has one admissible index, k = 0. Read the bounds before substituting into the summand.',
      variables: [v('empty count', 0, 'indices from 1 through 0'), v('singleton count', 1, 'one index: k = 0')],
      scene: { kind: 'registers', registers: [v('empty indices', '[]', 'no terms'), v('empty total', 0, 'additive identity'), v('singleton indices', '[0]', 'one term'), v('singleton total', 1, '2 × 0 + 1')], arrows: [{ from: 'empty indices', to: 'empty total' }, { from: 'singleton indices', to: 'singleton total' }], note: 'An empty sum and a sum containing a zero index are different.' },
      code: py(['empty = sum(2 * k + 1 for k in range(1, 1))', 'singleton = sum(2 * k + 1 for k in range(0, 1))', 'assert empty == 0 and singleton == 1', 'print(empty, singleton)'], [1, 2, 3]),
    });
    return frames;
  },
};

const reindexing: CurriculumLesson = {
  id: 'reindexing-sums', order: 18, title: 'Reindex without changing the sum',
  subtitle: 'Change the labels and keep every term exactly once.',
  prerequisites: ['Finite sum notation', 'Substitution in expressions'],
  objectives: ['Distinguish renaming an index from changing its values.', 'Transform bounds and summands together.', 'Justify a reindexing by a one-to-one correspondence.'],
  sources: source('§1.2.3 Sums and Products', '68, 70–71', 'dummy indices and change of summation variable'),
  parameters: [
    { id: 'lower', label: 'First index a', min: 0, max: 4, initial: 2, description: 'The original indices begin at a.' },
    { id: 'count', label: 'Number of terms n', min: 1, max: 6, initial: 4, description: 'The last index is a+n−1.' },
  ],
  buildFrames(inputs) {
    const a = integer(inputs, 'lower', 2, 0, 4), n = integer(inputs, 'count', 4, 1, 6), last = a + n - 1;
    const terms = Array.from({ length: n }, (_, i) => a + i), total = sum(terms);
    const nodes = terms.flatMap((k, j) => [{ id: `old-${j}`, label: `k=${k}`, value: k, x: n === 1 ? 0.5 : 0.1 + j * 0.8 / (n - 1), y: 0.25 }, { id: `new-${j}`, label: `j=${j}`, value: j, x: n === 1 ? 0.5 : 0.1 + j * 0.8 / (n - 1), y: 0.75 }]);
    const vars = [v('a', a, 'original lower endpoint'), v('n', n, 'number of terms'), v('last', last, 'original upper endpoint'), v('S', total, 'unchanged total')];
    const lines = [`a, n = ${a}, ${n}`, 'old_indices = list(range(a, a + n))', 'new_indices = list(range(n))', 'old_terms = old_indices', 'new_terms = [j + a for j in new_indices]', 'assert old_terms == new_terms', 'print(old_terms, new_terms, sum(new_terms))'];
    return [
      {
        id: 'original', title: 'Lay out the actual terms',
        intuition: `The old labels run from ${a} to ${last}. Here the summand is just k, so the term values are ${terms.join(', ')}.`,
        formal: `The inclusive interval from $a$ to $a+n-1$ contains $(a+n-1)-a+1=n$ integers. Always count the endpoints before transforming a sum; a change of labels must not quietly add or remove a term.`,
        formula: `\\sum_{k=${a}}^{${last}}k=${listTex(terms)}=${total}`,
        reading: 'Read “sum k from the lower endpoint through the upper endpoint.” Here the index and the term happen to have the same value because the summand is k.',
        variables: vars,
        scene: { kind: 'accumulation', terms, indexStart: a, active: n - 1, total, operation: 'sum', caption: `${n} original terms, including both endpoints.` },
        code: py(lines, [2, 4]),
        prediction: ask(`How many terms are in the inclusive sum from k = ${a} through k = ${last}?`, String(n), [String(n - 1), String(n + 1)], `The count is last − first + 1 = ${last} − ${a} + 1 = ${n}. When the endpoints agree, this formula correctly counts one term.`, 'Include both the first and the last index.'),
      },
      {
        id: 'rename-only', title: 'A different letter is only a different label',
        intuition: 'Calling the counter j instead of k changes no number. The same labels visit the same terms in the same order.',
        formal: 'The index is a bound, or dummy, variable. Renaming every occurrence of that bound variable consistently leaves the sum unchanged. This does not permit renaming another variable whose value was fixed outside the sum.',
        formula: `\\sum_{k=${a}}^{${last}}k=\\sum_{j=${a}}^{${last}}j=${total}`,
        reading: 'Read either letter as the temporary counter. The letter itself has no numerical contribution to the answer.',
        variables: vars,
        scene: { kind: 'registers', registers: [v('old labels', terms.join(', '), 'called k'), v('renamed labels', terms.join(', '), 'called j'), v('total', total, 'same terms')], arrows: [{ from: 'old labels', to: 'renamed labels', label: 'rename only' }, { from: 'renamed labels', to: 'total', label: 'add' }], note: 'No shift has happened yet; only the counter name changed.' },
        code: py([`a, n = ${a}, ${n}`, 'with_k = sum(k for k in range(a, a + n))', 'with_j = sum(j for j in range(a, a + n))', 'assert with_k == with_j', 'print(with_k, with_j)'], [2, 3, 4]),
      },
      {
        id: 'shift-labels', title: 'Give the first term the new label zero',
        intuition: `Subtract ${a} from every old label: ${a} becomes 0 and ${last} becomes ${n - 1}. To recover a term from its new label, add ${a} back.`,
        formal: `Set $j=k-a$. Solving for the old index gives $k=j+a$. The bounds transform as $a\\le k\\le a+n-1$ if and only if $0\\le j\\le n-1$. Both the bounds and the summand must use the new variable.`,
        formula: `j=k-${a},\\qquad k=j+${a},\\qquad ${a}\\le k\\le${last}\\Longleftrightarrow0\\le j\\le${n - 1}`,
        reading: 'Read the two equations as conversion rules. The double arrow between inequalities says they describe exactly corresponding allowed indices.',
        variables: vars,
        scene: { kind: 'graph', nodes, edges: terms.map((_, j) => ({ from: `old-${j}`, to: `new-${j}`, label: `− ${a}`, active: true })), directed: true, caption: 'Each old label has exactly one new label. The term value is recovered by adding the shift back.' },
        code: py([`a, n = ${a}, ${n}`, 'mapping = [(k, k - a) for k in range(a, a + n)]', 'assert [j for k, j in mapping] == list(range(n))', 'assert all(k == j + a for k, j in mapping)', 'print(mapping)'], [2, 3, 4]),
      },
      {
        id: 'replace-summand', title: 'Change the summand with the bounds',
        intuition: `The new label j = 0 must still select the old value ${a}. That is why the new recipe is j + ${a}, rather than just j.`,
        formal: `Substitution yields $\\sum_{k=a}^{a+n-1}k=\\sum_{j=0}^{n-1}(j+a)$. This is justified by the bijection $j\\mapsto j+a$: every old term appears exactly once and no new term appears. The sum is finite, so reordering also preserves its value.`,
        formula: `\\sum_{k=${a}}^{${last}}k=\\sum_{j=0}^{${n - 1}}(j+${a})=${listTex(terms)}=${total}`,
        reading: 'The lower and upper bounds describe the new labels; the summand translates each new label back into the original term value.',
        variables: vars,
        scene: { kind: 'graph', nodes: nodes.map(node => node.id.startsWith('new') ? { ...node, label: `j=${node.value}: ${Number(node.value) + a}`, value: Number(node.value) + a, active: true } : node), edges: terms.map((_, j) => ({ from: `old-${j}`, to: `new-${j}`, label: 'same term' })), caption: 'Read a column: a new label, an unchanged term. Adding either row of term values gives the same total.' },
        code: py(lines, [5, 6, 7]),
        prediction: ask(`With j = 0 as the first new index, which summand preserves the old first value ${a}?`, `j + ${a}`, [`j + ${a + 1}`, `j + ${a + 2}`], `Substitute j = 0. The expression j + ${a} returns ${a}, exactly the first old term. The same conversion also sends j = ${n - 1} to ${last}.`, 'Check both the first and the last term after substitution.'),
      },
      {
        id: 'audit-map', title: 'Audit the correspondence, not just the total',
        intuition: 'A matching total is a useful check, but the stronger check matches every term. The conversion should work in both directions, without missing or duplicating anything.',
        formal: 'A bijection is a function that is one-to-one and onto. Here injectivity follows from $j_1+a=j_2+a\\Rightarrow j_1=j_2$; surjectivity follows because each allowed $k$ has the preimage $j=k-a$. This termwise argument proves the identity for every allowed input, not just the displayed example.',
        formula: `j\\mapsto j+${a},\\qquad k\\mapsto k-${a},\\qquad |\\{0,\\ldots,${n - 1}\\}|=${n}`,
        reading: 'The mapping arrow means “is sent to.” Vertical bars around a finite set mean its number of elements, not absolute value.',
        variables: [v('old count', n, 'original terms'), v('new count', n, 'reindexed terms'), v('total', total, 'same sum')],
        scene: { kind: 'balance', left: [{ label: `old sum: ${total}`, value: total }], right: [{ label: `reindexed sum: ${total}`, value: total }], caption: 'The equality follows from a term-by-term bijection, not from a lucky numerical match.' },
        code: py([`a, n = ${a}, ${n}`, 'old = list(range(a, a + n))', 'new = [j + a for j in range(n)]', 'assert len(set(new)) == n', 'assert new == old', 'print(len(old), len(new), sum(new))'], [4, 5]),
      },
    ];
  },
};

const arithmeticSums: CurriculumLesson = {
  id: 'arithmetic-sum-pairing', order: 19, title: 'Pair an arithmetic sum',
  subtitle: 'Reverse a second copy so every pair has the same total.',
  prerequisites: ['Finite sums', 'Reindexing'],
  objectives: ['Recognize a constant difference.', 'Derive the arithmetic-sum formula by reversed pairing.', 'Count terms correctly and handle an odd middle term.'],
  sources: source('§1.2.3 Sums and Products', '75–76', 'arithmetic progressions and derivation by reversing a finite sum'),
  parameters: [
    { id: 'first', label: 'First term a', min: 1, max: 6, initial: 4, description: 'The value at index 0.' },
    { id: 'difference', label: 'Common difference d', min: 0, max: 4, initial: 3, description: 'Add this amount to make the next term.' },
    { id: 'count', label: 'Number of terms n', min: 1, max: 6, initial: 5, description: 'Indices run from 0 through n−1.' },
  ],
  buildFrames(inputs) {
    const a = integer(inputs, 'first', 4, 1, 6), d = integer(inputs, 'difference', 3, 0, 4), n = integer(inputs, 'count', 5, 1, 6);
    const terms = Array.from({ length: n }, (_, i) => a + i * d), reverse = [...terms].reverse(), last = terms[n - 1], total = sum(terms), pair = a + last;
    const common = [v('a', a, 'first term'), v('d', d, 'common difference'), v('n', n, 'number of terms'), v('last', last, 'a+(n−1)d')];
    const nodes = terms.flatMap((term, i) => [{ id: `forward-${i}`, label: String(term), value: term, x: n === 1 ? 0.5 : 0.1 + i * 0.8 / (n - 1), y: 0.25 }, { id: `reverse-${i}`, label: String(reverse[i]), value: reverse[i], x: n === 1 ? 0.5 : 0.1 + i * 0.8 / (n - 1), y: 0.75 }]);
    const code = [`a, d, n = ${a}, ${d}, ${n}`, 'forward = [a + i * d for i in range(n)]', 'backward = list(reversed(forward))', 'pairs = [x + y for x, y in zip(forward, backward)]'];
    return [
      {
        id: 'constant-difference', title: 'Find the repeated difference',
        intuition: `Start at ${a} and add ${d} between neighboring terms. After ${n - 1} such gaps, the last term is ${last}.`,
        formal: 'An arithmetic progression has terms $a_i=a+id$ for $i=0,\\ldots,n-1$, where $d$ is the common difference. With $n$ terms there are $n-1$ gaps, so the last term is $a+(n-1)d$, not $a+nd$.',
        formula: `S=\\sum_{i=0}^{${n - 1}}(${a}+${d}i)=${listTex(terms)}=${total}`,
        reading: 'The subscript i labels a term; d is the same difference between every pair of neighboring terms. Starting at index 0 does not add an extra term.',
        variables: common,
        scene: { kind: 'staircase', count: n, active: n - 1, base: 0, values: terms, labels: terms.map((term, i) => `i=${i}: ${term}`), caption: `${n} terms, ${n - 1} gaps, common difference ${d}. Column heights and labels show the actual term values.` },
        code: py(code.concat(['assert forward[-1] == a + (n - 1) * d', 'print(forward, sum(forward))']), [2, 5]),
        prediction: ask(`What value comes immediately after the displayed last term ${last}?`, String(last + d), [String(last + d + 1), String(last + d + 2)], `An arithmetic progression adds the same difference ${d} each time. The next term would be ${last} + ${d} = ${last + d}; it is not part of the current ${n}-term sum.`, 'Use the common difference, even if that difference is zero.'),
      },
      {
        id: 'reverse-copy', title: 'Write a second copy backward',
        intuition: 'Make a second row with the same terms in reverse order. Both rows have the same total because rearranging a finite collection does not change its sum.',
        formal: 'The substitution $j=n-1-i$ reverses the finite index set bijectively. Thus $S=\\sum_{i=0}^{n-1}(a+id)=\\sum_{i=0}^{n-1}(a+(n-1-i)d)$. We have written two copies of S, not split one copy into pairs yet.',
        formula: `S=${listTex(terms)},\\qquad S=${listTex(reverse)}`,
        reading: 'Read each row as an entire copy of the sum. Their combined total will be 2S.',
        variables: [...common, v('row total', total, 'each row sums to S')],
        scene: { kind: 'graph', nodes, edges: [], caption: `Top: forward order. Bottom: reverse order. Each row totals ${total}.` },
        code: py(code.concat(['assert sum(forward) == sum(backward)', 'print(forward, backward)']), [3, 5]),
      },
      {
        id: 'pair-columns', title: 'Every vertical pair balances to the same value',
        intuition: `The first and last terms make ${pair}. Move inward: one term gains ${d} while the other loses ${d}, so their sum stays ${pair}.`,
        formal: 'At index $i$, the pair is $(a+id)+(a+(n-1-i)d)=2a+(n-1)d$. The $+id$ and $-id$ cancel, so the pair total does not depend on $i$. This explains why all columns agree.',
        formula: `(${a}+${d}i)+(${a}+(${n}-1-i)${d})=2\\cdot${a}+(${n}-1)${d}=${pair}`,
        reading: 'The letter i disappears after simplification. That is the algebraic signal that every column has the same total.',
        variables: [...common, v('pair', pair, 'first plus last; same in every column')],
        scene: { kind: 'graph', directed: false, nodes: nodes.map(node => ({ ...node, active: true })), edges: terms.map((_, i) => ({ from: `forward-${i}`, to: `reverse-${i}`, label: `sum ${pair}`, active: true })), caption: `${n} vertical columns; each column contributes ${pair} across the two rows.` },
        code: py(code.concat(['assert all(pair == 2 * a + (n - 1) * d for pair in pairs)', 'print(pairs)']), [4, 5]),
      },
      {
        id: 'two-copies', title: 'Count the pairs across two complete copies',
        intuition: `There are ${n} columns, each worth ${pair}. That makes ${n * pair}, but it is the total of two rows, so it equals 2S.`,
        formal: 'Adding the forward and reversed sums term by term gives $2S=n(2a+(n-1)d)$. There are n pairs because we used two full copies. If n is odd, the middle value appears once in each copy, so its column legitimately contains it twice.',
        formula: `2S=${n}\\cdot${pair}=${2 * total}`,
        reading: 'The 2 on the left multiplies the entire unknown sum. Do not forget it when solving for S.',
        variables: [v('n', n, 'number of columns'), v('pair', pair, 'total of each column'), v('2S', 2 * total, 'two copies combined')],
        scene: { kind: 'balance', left: [{ label: `S = ${total}`, value: total, coefficient: 2 }], right: [{ label: `pair total ${pair}`, value: pair, coefficient: n }], caption: 'Two copies of the original sum equal n identical column totals.' },
        code: py(code.concat(['double_total = sum(forward) + sum(backward)', 'paired_total = n * (forward[0] + forward[-1])', 'assert double_total == paired_total', 'print(double_total, paired_total)']), [5, 6, 7]),
        prediction: ask(`The ${n} pair-columns total ${2 * total}. What is the original sum S?`, String(total), [String(2 * total), String(2 * total + 1)], `Those columns included two complete copies of S. Divide ${2 * total} by 2 to recover ${total}. With an odd number of terms the middle term was correctly counted in both copies.`, 'Ask how many complete copies of the original sum are in the picture.'),
      },
      {
        id: 'divide-two', title: 'Take half to recover the original sum',
        intuition: `Half of ${2 * total} is ${total}. Equivalently, the average of the first and last values is ${pair / 2}, and there are ${n} terms.`,
        formal: 'Dividing by 2 gives $S=\\tfrac n2(2a+(n-1)d)=n(a+\\text{last})/2$. This is “number of terms times the average of the endpoints.” The pairing proof explains why the endpoint average is also the average of all terms.',
        formula: `S=\\frac{${n}(${a}+${last})}{2}=\\frac{${n}\\cdot${pair}}2=${total}`,
        reading: 'The fraction bar divides the whole numerator by 2. The n is a term count, while n−1 counts the gaps.',
        variables: [...common, v('endpoint average', pair / 2, 'mean value of the progression'), v('S', total, 'one copy of the sum')],
        scene: { kind: 'balance', left: [{ label: `sum of ${n} terms`, value: total }], right: [{ label: `average ${pair / 2}`, value: pair / 2, coefficient: n }], caption: `${n} times the endpoint average gives the original sum ${total}.` },
        code: py(['from fractions import Fraction', ...code, 'formula = Fraction(n * (2 * a + (n - 1) * d), 2)', 'assert formula == sum(forward)', 'print(formula)'], [6, 7]),
      },
      {
        id: 'boundary-checks', title: 'Check one term and a flat progression',
        intuition: 'With one term, the sum must be that term. With zero difference, all terms are equal. A trustworthy formula should keep both simple cases simple.',
        formal: 'For $n=1$, the formula gives $[2a+0d]/2=a$. For $d=0$, it gives $n(2a)/2=na$. Defining an empty arithmetic sum as zero also extends the formula to $n=0$. The derivation used finite sums, so it does not justify summing an infinite progression.',
        formula: `S_1=a,\\qquad S_n\\big|_{d=0}=na,\\qquad S_0=0`,
        reading: 'The vertical bar with d = 0 means “evaluate this expression in the special case d = 0.” Subscripts distinguish sums with different term counts.',
        variables: [v('a', a, 'fixed first term'), v('one-term total', a, 'n = 1'), v('flat total', n * a, 'same n, but d = 0')],
        scene: { kind: 'registers', registers: [v('one term', a, 'only a'), v('flat progression', n * a, `${n} copies of ${a}`), v('empty progression', 0, 'no terms')], arrows: [], note: 'Boundary cases check the meaning of the formula, not just its arithmetic.' },
        code: py([`a, d, n = ${a}, ${d}, ${n}`, 'def arithmetic_sum(a, d, count):', '    return count * (2 * a + (count - 1) * d) // 2', 'assert arithmetic_sum(a, d, 1) == a', 'assert arithmetic_sum(a, 0, n) == n * a', 'assert arithmetic_sum(a, d, 0) == 0', 'print(a, n * a, 0)'], [4, 5, 6]),
      },
    ];
  },
};

const geometricSums: CurriculumLesson = {
  id: 'geometric-sum-cancellation', order: 20, title: 'Cancel a geometric sum',
  subtitle: 'Multiply by the ratio, shift the terms, and watch the middle disappear.',
  prerequisites: ['Powers', 'Finite sums', 'Reindexing'],
  objectives: ['Recognize a constant ratio.', 'Derive a finite geometric sum by aligned cancellation.', 'Handle ratio 1 and zero terms before dividing.'],
  sources: source('§1.2.3 Sums and Products', '74–75', 'finite geometric progressions and derivation by shifting and cancellation'),
  parameters: [
    { id: 'ratio', label: 'Common ratio r', min: 1, max: 4, initial: 3, description: 'Multiply by r to get the next term; r = 1 is a separate case.' },
    { id: 'count', label: 'Number of terms n', min: 0, max: 6, initial: 4, description: 'Use powers r^0 through r^(n−1); zero terms gives an empty sum.' },
  ],
  buildFrames(inputs) {
    const r = integer(inputs, 'ratio', 3, 1, 4), n = integer(inputs, 'count', 4, 0, 6);
    const terms = Array.from({ length: n }, (_, i) => r ** i), shifted = terms.map(t => r * t), total = sum(terms), end = r ** n;
    const vars = [v('r', r, 'common ratio'), v('n', n, 'number of terms'), v('S', total, 'original total'), v('rⁿ', end, 'first power just beyond the sum')];
    const baseCode = [`r, n = ${r}, ${n}`, 'terms = [r ** i for i in range(n)]', 'shifted = [r * term for term in terms]', 'S = sum(terms)'];
    const nodes = terms.flatMap((term, i) => [{ id: `original-${i}`, label: `r^${i}=${term}`, value: term, x: 0.08 + i * 0.84 / Math.max(1, n), y: 0.7, active: i === 0 }, { id: `shifted-${i}`, label: `r^${i + 1}=${shifted[i]}`, value: shifted[i], x: 0.08 + (i + 1) * 0.84 / Math.max(1, n), y: 0.3, active: i === n - 1 }]);
    return [
      {
        id: 'constant-ratio', title: 'Make each term by multiplying',
        intuition: n ? `Begin with 1, then multiply by ${r} each time. The ${n} terms are ${terms.join(', ')}.` : 'The selected sum has zero terms. Its value is zero before any multiplication or addition happens.',
        formal: 'A geometric progression has a constant ratio between successive terms. Starting at 1, the n-term sum is $S=\\sum_{i=0}^{n-1}r^i$, with integer $n\\ge0$. There are n terms, even though the last exponent is n−1. We use positive ratios here.',
        formula: `S=\\sum_{i=0}^{${n - 1}}${r}^i=${listTex(terms)}=${total}`,
        reading: 'Read “sum r to the i, for i from zero through n minus one.” The zero exponent contributes the first term 1 when the sum is nonempty.',
        variables: vars,
        scene: { kind: 'accumulation', terms, indexStart: 0, active: n - 1, total, operation: 'sum', caption: n ? `${n} terms with ratio ${r}; last included exponent ${n - 1}.` : 'Empty index set: no terms, total 0.' },
        code: py(baseCode.concat(['print(terms, S)']), [2, 4]),
        prediction: ask(n ? `What term would come next, just beyond these ${n} terms?` : 'What would the first term be if we changed from zero terms to one?', String(end), [String(end + 1), String(end + 2)], n ? `The last included exponent is ${n - 1}. The next exponent is ${n}, giving ${r}^${n} = ${end}. This next term is not yet part of S.` : `The first exponent is 0, so the first term is ${r}^0 = 1. An empty sum contains no copy of that term.`, 'Find the next exponent before evaluating the power.'),
      },
      {
        id: 'multiply-shift', title: 'Multiply the whole sum by its ratio',
        intuition: `Multiplying every term by ${r} advances every exponent by one. ${n ? `The new row is ${shifted.join(', ')}.` : 'The empty row remains empty.'}`,
        formal: 'Distributivity gives $rS=\\sum_{i=0}^{n-1}r^{i+1}$. For n≥1, the original exponents are 0 through n−1 and the shifted exponents are 1 through n. This one-position shift is what makes matching terms cancel.',
        formula: `rS=${r}\\cdot${total}=${listTex(shifted)}=${r * total}`,
        reading: 'rS means r times the entire sum. Multiplying only the last term would not distribute correctly.',
        variables: [...vars, v('rS', r * total, 'total of the shifted row')],
        scene: { kind: 'balance', left: terms.map((term, i) => ({ label: `${r} × r^${i}`, value: term, coefficient: r })), right: [{ label: `rS = ${r * total}`, value: r * total }], caption: 'Every term is multiplied by the ratio; the shifted row totals rS.' },
        code: py(baseCode.concat(['assert sum(shifted) == r * S', 'print(shifted, sum(shifted))']), [3, 5]),
      },
      {
        id: 'align-cancel', title: 'Align equal powers and subtract',
        intuition: n > 1 ? `Place equal exponents in the same column. The powers from 1 through ${n - 1} occur in both rows and cancel. The shifted row keeps ${end}; subtracting the original row leaves a minus 1.` : n === 1 ? `There are no interior powers to cancel. The shifted row contains just ${r}; subtracting the original term 1 leaves ${r - 1}.` : 'Both sums are empty, so their difference is zero. The endpoint expression also gives r^0 − 1 = 0.',
        formal: 'For n≥1, subtracting S from rS cancels every shared interior power. The unmatched endpoints give $rS-S=r^n-1$, hence $(r-1)S=r^n-1$. With n=0 the same identity holds because both sides are zero.',
        formula: `rS-S=(${r}-1)S=${r * total}-${total}=${end}-1=${end - 1}`,
        reading: 'The minus sign applies to the whole original sum. Each shared positive term is paired with its negative copy, leaving only two boundary terms.',
        variables: [...vars, v('difference', end - 1, 'shifted total minus original total')],
        scene: n ? { kind: 'graph', directed: false, nodes, edges: Array.from({ length: Math.max(0, n - 1) }, (_, j) => ({ from: `shifted-${j}`, to: `original-${j + 1}`, label: 'cancel', active: true })), caption: 'Top row: rS. Bottom row: S, which is subtracted. Matching interior powers cancel; colored endpoints remain.' } : { kind: 'balance', left: [], right: [{ label: 'r⁰', value: 1 }, { label: '1', value: 1, coefficient: -1 }], caption: 'Zero terms: the empty difference equals 1 − 1 = 0.' },
        code: py(baseCode.concat(['difference = sum(shifted) - sum(terms)', 'assert difference == r ** n - 1', 'assert difference == (r - 1) * S', 'print(difference)']), [5, 6, 7]),
      },
      {
        id: 'solve', title: r === 1 ? 'Do not divide by zero' : 'Divide by the nonzero leftover factor',
        intuition: r === 1 ? `Every term is 1, so the sum is simply ${n}. The cancellation equation says 0 = 0 and cannot reveal the sum by division.` : `We have ${r - 1} copies of S totaling ${end - 1}. Divide by ${r - 1} to obtain S = ${total}.`,
        formal: 'When $r\\ne1$, division by $r-1$ yields $S=(r^n-1)/(r-1)$. When $r=1$, that quotient is undefined, but the original sum is perfectly well-defined: it contains n copies of 1 and equals n. Check the condition before using the formula.',
        formula: r === 1 ? `S=\\sum_{i=0}^{${n - 1}}1^i=${n},\\qquad(r-1)S=0=1^{${n}}-1` : `S=\\frac{r^n-1}{r-1}=\\frac{${r}^{${n}}-1}{${r}-1}=\\frac{${end - 1}}{${r - 1}}=${total}`,
        reading: r === 1 ? 'The sum has a value even though the quotient formula has a zero denominator. Return to the meaning of the original sum.' : 'Read “r to the n, minus one, divided by r minus one.” Both numerator and denominator are whole grouped expressions.',
        variables: vars,
        scene: { kind: 'balance', left: [{ label: `direct sum ${total}`, value: total }], right: [{ label: r === 1 ? `${n} copies of 1` : `(${end} − 1)/(${r} − 1)`, value: r === 1 ? n : (end - 1) / (r - 1) }], caption: r === 1 ? 'For ratio 1, count the terms directly.' : 'Cancellation turns a many-term sum into a quotient.' },
        code: py(baseCode.concat(['if r == 1:', '    formula = n', 'else:', '    formula = (r ** n - 1) // (r - 1)', 'assert formula == S', 'print(formula)']), r === 1 ? [5, 6, 9] : [7, 8, 9]),
        prediction: ask('What is the sum of n terms when the common ratio is 1?', 'n', ['0 because cancellation gives zero.', 'Undefined because the quotient has denominator zero.'], 'The original sum is 1 + 1 + ⋯ + 1 with n terms, so its value is n. Only the quotient formula is unavailable at r = 1; the finite sum itself is defined, including the empty case n = 0.', 'Return to the actual terms rather than dividing 0 by 0.'),
      },
      {
        id: 'general-first-term', title: 'Scale the first term without changing the argument',
        intuition: `If every term in the current sum is doubled, the total doubles to ${2 * total}. The pattern of cancellation is unchanged.`,
        formal: 'For first term a and n terms, $\\sum_{i=0}^{n-1}ar^i=a(r^n-1)/(r-1)$ when $r\\ne1$, and $an$ when $r=1$. The first term is a, the last included term is $ar^{n-1}$ for n≥1, and the first excluded term is $ar^n$.',
        formula: `\\sum_{i=0}^{${n - 1}}2\\cdot${r}^i=2S=2\\cdot${total}=${2 * total}`,
        reading: 'The factor a scales every term. The exponent n in the closed form comes from the first excluded power, while the last included exponent is n−1.',
        variables: [v('a', 2, 'new first term for a nonempty sum'), ...vars, v('scaled total', 2 * total, 'twice the original sum')],
        scene: { kind: 'accumulation', terms: terms.map(t => 2 * t), indexStart: 0, active: n - 1, total: 2 * total, operation: 'sum', caption: n ? 'Every term and the final total are scaled by 2.' : 'Scaling an empty sum still gives 0.' },
        code: py(baseCode.concat(['a = 2', 'scaled_terms = [a * term for term in terms]', 'assert sum(scaled_terms) == a * S', 'print(scaled_terms, sum(scaled_terms))']), [5, 6, 7]),
      },
      {
        id: 'finite-boundary', title: 'Check the boundaries, then stop at the finite result',
        intuition: 'Zero terms give zero. One term gives one. The formula is a shortcut for exactly the requested finite list, not permission to keep adding forever.',
        formal: 'For n=0, $(r^0-1)/(r-1)=0$ when r≠1, matching the empty sum. For n=1, $(r-1)/(r-1)=1$. Infinite geometric series require a separate limiting argument and a convergence condition; nothing in this finite derivation allows an infinite sum with ratio 3.',
        formula: `S_0=0,\\qquad S_1=1,\\qquad S_{${n}}=${total}`,
        reading: 'The subscript tells how many terms belong to that sum. Always keep the number of terms visible when using a finite-series formula.',
        variables: [v('empty sum', 0, 'n = 0'), v('one-term sum', 1, 'n = 1'), v('current sum', total, `${n} terms`)],
        scene: { kind: 'registers', registers: [v('zero terms', 0, 'empty sum'), v('one term', 1, 'the first power'), v('chosen terms', total, `${n} terms at ratio ${r}`)], arrows: [], note: 'Finite sum, explicit term count, and ratio-1 branch: all three checks matter.' },
        code: py([`r = ${r}`, 'def geometric_sum(r, count):', '    if r == 1:', '        return count', '    return (r ** count - 1) // (r - 1)', 'assert geometric_sum(r, 0) == 0', 'assert geometric_sum(r, 1) == 1', `assert geometric_sum(r, ${n}) == ${total}`, `print(geometric_sum(r, ${n}))`], [6, 7, 8]),
      },
    ];
  },
};

export const numbersAndSumsLessons: CurriculumLesson[] = [
  rationalNumbers, positivePowers, extendedPowers, logarithms, logarithmLaws,
  roundedComputation, finiteSums, reindexing, arithmeticSums, geometricSums,
];
