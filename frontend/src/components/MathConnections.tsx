import { createContext, Fragment, useContext, useEffect, useId, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { mathValuesFromAttributes, normalizeMathValue, splitLinkedNumbers } from '../lib/mathConnections';
import './MathConnections.css';

const NUMBER_SELECTOR = '[data-math-value], [data-math-values]';
const EDITABLE_SELECTOR = 'input, textarea, select, [contenteditable]:not([contenteditable="false"])';

interface ConnectionContext {
  pinned: string[];
  clear: () => void;
  helpId: string;
}

const MathConnectionContext = createContext<ConnectionContext | null>(null);

function elementValues(element: Element | null): string[] {
  return element ? mathValuesFromAttributes(element.getAttribute('data-math-value'), element.getAttribute('data-math-values')) : [];
}

function sameValues(left: string[], right: string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

interface MathConnectionsProps {
  children: ReactNode;
  resetKey?: string;
  className?: string;
  as?: 'main' | 'div';
}

/** A single event/observation boundary for React, KaTeX and dynamically inserted D3 nodes. */
export function MathConnections({ children, resetKey, className, as: Tag = 'div' }: MathConnectionsProps) {
  const rootRef = useRef<HTMLDivElement & HTMLElement>(null);
  const controllerRef = useRef<{ clear: () => void } | null>(null);
  const [pinned, setPinned] = useState<string[]>([]);
  const [active, setActive] = useState<string[]>([]);
  const helpId = useId();

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    let hovered: Element | null = null;
    let focused: Element | null = null;
    let kept: string[] = [];
    let selected: string[] = [];
    let disposed = false;
    let queued = false;
    const linked = new Set<Element>();

    const findNumber = (target: EventTarget | null): Element | null => {
      const element = target instanceof Element ? target.closest(NUMBER_SELECTOR) : null;
      return element && root.contains(element) ? element : null;
    };
    const apply = () => {
      const keys = new Set(selected);
      const next = new Set<Element>();
      if (keys.size) {
        for (const element of root.querySelectorAll(NUMBER_SELECTOR)) {
          if (elementValues(element).some((value) => keys.has(value))) {
            next.add(element);
            if (!linked.has(element)) element.setAttribute('data-math-linked', 'true');
          }
        }
      }
      for (const element of linked) if (!next.has(element)) element.removeAttribute('data-math-linked');
      linked.clear();
      for (const element of next) linked.add(element);
      if (selected.length) root.setAttribute('data-math-selection', selected.join(' '));
      else root.removeAttribute('data-math-selection');
    };
    const select = () => {
      if (hovered && !root.contains(hovered)) hovered = null;
      if (focused && !root.contains(focused)) focused = null;
      const hoverValues = elementValues(hovered);
      const focusValues = elementValues(focused);
      const next = hoverValues.length ? hoverValues : kept.length ? kept : focusValues;
      if (!sameValues(selected, next)) {
        selected = next;
        setActive(next);
      }
      apply();
    };
    const clear = () => {
      kept = [];
      hovered = null;
      focused = null;
      setPinned([]);
      select();
    };
    const toggle = (element: Element) => {
      const values = elementValues(element);
      if (!values.length) return;
      kept = sameValues(values, kept) ? [] : values;
      setPinned(kept);
      select();
    };
    const onPointerOver = (event: PointerEvent) => {
      const next = findNumber(event.target);
      if (next !== hovered) {
        hovered = next;
        select();
      }
    };
    const onPointerOut = (event: PointerEvent) => {
      const next = findNumber(event.relatedTarget);
      if (next !== hovered) {
        hovered = next;
        select();
      }
    };
    const onFocusIn = (event: FocusEvent) => {
      focused = findNumber(event.target);
      select();
    };
    const onFocusOut = (event: FocusEvent) => {
      focused = findNumber(event.relatedTarget);
      select();
    };
    const onClick = (event: MouseEvent) => {
      if (event.target instanceof Element && event.target.closest(EDITABLE_SELECTOR)) return;
      const element = findNumber(event.target);
      if (element) toggle(element);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.key === 'Enter' || event.key === ' ') && !event.repeat) {
        const element = findNumber(event.target);
        // Native buttons/inputs/links keep their native keyboard actions. Only
        // explicit standalone number tokens need a keyboard equivalent for click.
        if (element?.getAttribute('data-math-keyboard') === 'true' && event.target === element) {
          event.preventDefault();
          toggle(element);
        }
      }
    };
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') clear();
    };

    const observer = new MutationObserver(() => {
      if (queued) return;
      queued = true;
      queueMicrotask(() => {
        queued = false;
        if (!disposed) select();
      });
    });
    observer.observe(root, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-math-value', 'data-math-values'] });
    root.addEventListener('pointerover', onPointerOver);
    root.addEventListener('pointerout', onPointerOut);
    root.addEventListener('focusin', onFocusIn);
    root.addEventListener('focusout', onFocusOut);
    root.addEventListener('click', onClick);
    root.addEventListener('keydown', onKeyDown);
    root.ownerDocument.addEventListener('keydown', onEscape);
    controllerRef.current = { clear };
    setPinned([]);
    setActive([]);

    return () => {
      disposed = true;
      observer.disconnect();
      root.removeEventListener('pointerover', onPointerOver);
      root.removeEventListener('pointerout', onPointerOut);
      root.removeEventListener('focusin', onFocusIn);
      root.removeEventListener('focusout', onFocusOut);
      root.removeEventListener('click', onClick);
      root.removeEventListener('keydown', onKeyDown);
      root.ownerDocument.removeEventListener('keydown', onEscape);
      for (const element of linked) element.removeAttribute('data-math-linked');
      root.removeAttribute('data-math-selection');
      controllerRef.current = null;
    };
  }, [resetKey]);

  const context = useMemo<ConnectionContext>(() => ({
    pinned, helpId, clear: () => controllerRef.current?.clear(),
  }), [pinned, helpId]);

  return (
    <MathConnectionContext.Provider value={context}>
      <Tag ref={rootRef} className={['math-connections', className].filter(Boolean).join(' ')}>
        {children}
        <span className="math-connections-sr" id={helpId}>Select a number to keep matching values highlighted. Escape clears the selection.</span>
        <span className="math-connections-sr" role="status" aria-live="polite" aria-atomic="true">
          {active.length ? `Matching values highlighted: ${active.join(', ')}.` : ''}
        </span>
      </Tag>
    </MathConnectionContext.Provider>
  );
}

export function LinkedNumber({ value, className, interactive = true }: {
  value: number | string;
  className?: string;
  interactive?: boolean;
}) {
  const context = useContext(MathConnectionContext);
  const key = normalizeMathValue(value);
  const isInteractive = interactive && key !== null;
  return (
    <span
      className={['linked-number', className].filter(Boolean).join(' ')}
      data-math-value={key ?? undefined}
      data-math-keyboard={isInteractive ? 'true' : undefined}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      aria-label={isInteractive ? `${value}, highlight matching values` : undefined}
      aria-describedby={isInteractive ? context?.helpId : undefined}
      aria-pressed={isInteractive ? context?.pinned.includes(key!) ?? false : undefined}
    >{value}</span>
  );
}

export function LinkedText({ text, className, interactive = true }: {
  text: string;
  className?: string;
  interactive?: boolean;
}) {
  const segments = useMemo(() => splitLinkedNumbers(text), [text]);
  return (
    <span className={className}>
      {segments.map((segment, index) => segment.value === undefined
        ? <Fragment key={index}>{segment.text}</Fragment>
        : <LinkedNumber key={index} value={segment.text} interactive={interactive} />)}
    </span>
  );
}

/** Optional inline control; its reserved line keeps Playback from jumping on pin. */
export function MathConnectionStatus({ className }: { className?: string }) {
  const context = useContext(MathConnectionContext);
  return (
    <div className={['math-connection-status', className].filter(Boolean).join(' ')}>
      {context && context.pinned.length > 0 && <>
        <span>Linked: <strong>{context.pinned.join(', ')}</strong></span>
        <button type="button" onClick={context.clear}>Clear selection</button>
      </>}
    </div>
  );
}

/** A symbolic name linked to its current numeric binding, without hiding its meaning. */
export function LinkedSymbol({ symbol, value }: { symbol: string; value: number | string }) {
  const context = useContext(MathConnectionContext);
  const key = normalizeMathValue(value);
  return <span className="linked-number linked-symbol" data-symbol={symbol} data-math-value={key ?? undefined}
    data-math-keyboard={key !== null ? 'true' : undefined} tabIndex={key !== null ? 0 : undefined}
    role={key !== null ? 'button' : undefined} aria-label={`${symbol} currently equals ${value}`}
    aria-describedby={context?.helpId} aria-pressed={key !== null ? context?.pinned.includes(key) ?? false : undefined}>
    {symbol}
  </span>;
}
