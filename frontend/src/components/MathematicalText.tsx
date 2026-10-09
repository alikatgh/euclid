import { useMemo } from 'react';
import { renderLinkedMath } from '../lib/mathConnections';
import { LinkedText } from './MathConnections';

interface MathematicalTextProps {
  text: string;
  className?: string;
  interactive?: boolean;
}

/** Ordinary prose interspersed with inline TeX, delimited by single dollar signs. */
export function MathematicalText({ text, className, interactive = true }: MathematicalTextProps) {
  const segments = useMemo(() => {
    const result: Array<{ text: string; html?: string }> = [];
    const math = /\$([^$]+)\$/g;
    let end = 0;
    for (const match of text.matchAll(math)) {
      if (match.index > end) result.push({ text: text.slice(end, match.index) });
      result.push({
        text: match[1],
        html: renderLinkedMath(match[1], {
          displayMode: false,
          throwOnError: false,
          trust: false,
          output: 'htmlAndMathml',
        }),
      });
      end = match.index + match[0].length;
    }
    if (end < text.length) result.push({ text: text.slice(end) });
    return result;
  }, [text]);

  return (
    <span className={className}>
      {segments.map((segment, index) => (
        segment.html === undefined
          ? <LinkedText key={index} text={segment.text} interactive={interactive} />
          : <span key={index} dangerouslySetInnerHTML={{ __html: segment.html }} />
      ))}
    </span>
  );
}

export default MathematicalText;
