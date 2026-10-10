import katex, { type KatexOptions } from 'katex';

export interface LinkedNumberSegment {
  text: string;
  value?: string;
}

/** Exact decimal identity, without Number's rounding or expansive exponent allocation. */
export function normalizeMathValue(value: number | string): string | null {
  const match = String(value).trim().match(/^([+\-−]?)(?:(\d+)(?:\.(\d*))?|\.(\d+))(?:[eE]([+-]?\d+))?$/);
  if (!match) return null;
  const fraction = match[3] ?? match[4] ?? '';
  const significant = `${match[2] ?? ''}${fraction}`.replace(/^0+/, '');
  if (!significant) return '0';
  const digits = significant.replace(/0+$/, '');
  const power = BigInt(match[5] ?? '0') - BigInt(fraction.length) + BigInt(significant.length - digits.length);
  const sign = match[1] === '-' || match[1] === '−' ? '-' : '';
  const point = BigInt(digits.length) + power;
  if (power >= 0n && point <= 256n) return `${sign}${digits}${'0'.repeat(Number(power))}`;
  if (power < 0n && point > 0n && -power <= 256n) {
    const position = Number(point);
    return `${sign}${digits.slice(0, position)}.${digits.slice(position)}`;
  }
  if (point <= 0n && -point + BigInt(digits.length) <= 256n) {
    return `${sign}0.${'0'.repeat(Number(-point))}${digits}`;
  }
  const coefficient = digits.length === 1 ? digits : `${digits[0]}.${digits.slice(1)}`;
  return `${sign}${coefficient}e${point - 1n}`;
}

/** Numeric prose tokens, excluding identifiers such as E1, x2 and 50px. */
export function splitLinkedNumbers(text: string): LinkedNumberSegment[] {
  const segments: LinkedNumberSegment[] = [];
  const numeric = /(?<![\p{L}\p{N}_.])[+\-−]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?(?![\p{L}\p{N}_]|\.\d)/gu;
  let end = 0;
  for (const match of text.matchAll(numeric)) {
    if (match.index > end) segments.push({ text: text.slice(end, match.index) });
    segments.push({ text: match[0], value: normalizeMathValue(match[0]) ?? undefined });
    end = match.index + match[0].length;
  }
  if (end < text.length) segments.push({ text: text.slice(end) });
  return segments;
}

export function mathValuesFromAttributes(value: string | null, values: string | null): string[] {
  return [...new Set([...(value ? [value] : []), ...(values?.trim().split(/\s+/) ?? [])]
    .map(normalizeMathValue)
    .filter((key): key is string => key !== null))].sort();
}

interface HtmlNode {
  opening: string;
  closing: string;
  tag: string;
  classes: Set<string>;
  children: Array<HtmlNode | string>;
  value?: string;
}

// Only parse KaTeX's generated markup. Preserve original tags, attributes and MathML
// verbatim; reading numeric text leaves never reads digits from class/style attributes.
function parseGeneratedHtml(html: string): HtmlNode {
  const root: HtmlNode = { opening: '', closing: '', tag: '', classes: new Set(), children: [] };
  const stack = [root];
  for (const token of html.match(/<[^>]*>|[^<]+/g) ?? []) {
    const tag = token.match(/^<(\/)?([A-Za-z][\w:-]*)\b/);
    if (!tag) {
      stack.at(-1)!.children.push(token);
    } else if (tag[1]) {
      const node = stack.pop();
      if (node && node !== root) node.closing = token;
    } else {
      const node: HtmlNode = {
        opening: token,
        closing: '',
        tag: tag[2],
        classes: new Set(token.match(/\bclass="([^"]*)"/)?.[1].split(/\s+/) ?? []),
        children: [],
      };
      stack.at(-1)!.children.push(node);
      if (!/\/>$/.test(token) && !['img', 'br', 'hr', 'input', 'wbr'].includes(node.tag)) stack.push(node);
    }
  }
  return root;
}

interface NumericParts { text: string; leaves: HtmlNode[]; endsWithScript?: boolean }

function numericParts(node: HtmlNode): NumericParts | null {
  if (node.tag !== 'span' || [...node.classes].some((name) => (
    /^(?:mspace|mbin|mrel|mopen|mclose|mpunct|mfrac|msupsub|vlist(?:-.*)?|katex-strut|pstrut|frac-line)$/.test(name)
  ))) return null;
  if (node.children.length === 1 && typeof node.children[0] === 'string') {
    const text = node.children[0];
    return /^[+\-−\d.]+$/.test(text) ? { text, leaves: [node] } : null;
  }
  const parts: NumericParts = { text: '', leaves: [] };
  for (const [index, child] of node.children.entries()) {
    if (typeof child === 'string') return null;
    // KaTeX attaches scripts to the final digit of an unbraced number. Keep
    // that base digit in its adjacent numeric run, but never include script
    // digits or concatenate the number printed after a completed script.
    if (node.classes.has('mord') && child.classes.has('msupsub') && index === node.children.length - 1) {
      parts.endsWithScript = true;
      continue;
    }
    const part = numericParts(child);
    if (!part) return null;
    if (part.endsWithScript && index !== node.children.length - 1) return null;
    parts.text += part.text;
    parts.leaves.push(...part.leaves);
    parts.endsWithScript = part.endsWithScript;
  }
  return parts.text ? parts : null;
}

function annotateHtmlNumbers(node: HtmlNode): void {
  for (const child of node.children) {
    if (typeof child !== 'string') annotateHtmlNumbers(child);
  }

  // Consecutive numeric spans may be split by font/color commands. Treat their
  // printed number as one literal; fractions, script stacks and spacing break runs.
  let run: NumericParts = { text: '', leaves: [] };
  const finish = () => {
    const value = normalizeMathValue(run.text);
    if (value !== null) for (const leaf of run.leaves) leaf.value = value;
    run = { text: '', leaves: [] };
  };
  for (const child of node.children) {
    const part = typeof child === 'string' ? null : numericParts(child);
    if (!part) {
      finish();
    } else {
      run.text += part.text;
      run.leaves.push(...part.leaves);
      if (part.endsWithScript) finish();
    }
  }
  finish();

  if (node.children.length === 1 && typeof node.children[0] === 'string' && node.tag === 'span') {
    const text = node.children[0];
    if (normalizeMathValue(text) !== null) {
      node.value ??= normalizeMathValue(text) ?? undefined;
    } else if (node.classes.has('mord') && text.length > 1) {
      // \text{...} can contain prose and numbers in a single leaf.
      node.children = splitLinkedNumbers(text).map((segment) => segment.value === undefined ? segment.text : {
        opening: '<span>', closing: '</span>', tag: 'span', classes: new Set<string>(),
        children: [segment.text], value: segment.value,
      });
    }
  }
}

function serializeHtml(node: HtmlNode): string {
  const opening = node.value === undefined ? node.opening : node.opening.replace(/>$/, ` data-math-value="${node.value}">`);
  return opening + node.children.map((child) => typeof child === 'string' ? child : serializeHtml(child)).join('') + node.closing;
}

/** Public KaTeX rendering with root-scoped numeric HTML hooks and intact MathML. */
export function renderLinkedMath(tex: string, options: KatexOptions = {}, bindings: Record<string, number | string> = {}): string {
  const html = katex.renderToString(tex, { trust: false, output: 'htmlAndMathml', ...options });
  const root = parseGeneratedHtml(html);
  const annotate = (node: HtmlNode) => {
    if (node.classes.has('katex-html')) {
      annotateHtmlNumbers(node);
      const bindSymbols = (element: HtmlNode) => {
        // A decorated name is a different mathematical symbol: a_0 is not a,
        // a-prime is not a, and an approximation accent is not the exact value.
        // Numeric literals were already annotated above and remain linked.
        const decorated = element.classes.has('msupsub') || element.classes.has('katex-accent') || element.classes.has('accent')
          || element.children.some((child) => typeof child !== 'string' && child.classes.has('msupsub'));
        if (decorated) return;
        if (element.classes.has('mathnormal') && element.children.length === 1 && typeof element.children[0] === 'string') {
          const symbol = element.children[0];
          if (Object.hasOwn(bindings, symbol)) element.value = normalizeMathValue(bindings[symbol]) ?? undefined;
        }
        for (const [index, child] of element.children.entries()) if (typeof child !== 'string') {
          const next = element.children[index + 1];
          const hasUnicodePrime = typeof next !== 'string' && next?.children.length === 1 && /^[′″‴]$/.test(String(next.children[0]));
          if (!hasUnicodePrime) bindSymbols(child);
        }
      };
      bindSymbols(node);
    }
    else for (const child of node.children) if (typeof child !== 'string') annotate(child);
  };
  annotate(root);
  return serializeHtml(root);
}
