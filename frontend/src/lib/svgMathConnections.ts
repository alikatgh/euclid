import { splitLinkedNumbers } from './mathConnections';

const linkedSelector = '[data-math-value], [data-math-values]';

/** Adapt only D3-owned labels. React and KaTeX annotate their own output. */
export function observeSvgMathConnections(svg: SVGSVGElement): () => void {
  const annotate = (root: Node) => {
    if (!svg.contains(root) && root !== svg) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const textNodes: Text[] = [];
    if (root.nodeType === Node.TEXT_NODE) textNodes.push(root as Text);
    else while (walker.nextNode()) textNodes.push(walker.currentNode as Text);

    for (const node of textNodes) {
      const parent = node.parentElement;
      if (!parent || parent.closest(linkedSelector)) continue;
      const isSvgText = Boolean(parent.closest('text'));
      if (!isSvgText && !parent.closest('foreignObject')) continue;
      const tokens = splitLinkedNumbers(node.data);
      if (!tokens.some((token) => token.value !== undefined)) continue;

      const fragment = document.createDocumentFragment();
      for (const token of tokens) {
        if (token.value === undefined) fragment.append(document.createTextNode(token.text));
        else {
          const element = isSvgText
            ? document.createElementNS('http://www.w3.org/2000/svg', 'tspan')
            : document.createElement('span');
          element.setAttribute('data-math-value', token.value);
          element.textContent = token.text;
          fragment.append(element);
        }
      }
      node.replaceWith(fragment);
    }
  };

  // Animations can replace label text after their final frame. Only observe text
  // changes, never frame-by-frame geometry/styles or our own annotation writes.
  const options = { childList: true, characterData: true, subtree: true };
  const observer = new MutationObserver((records) => {
    observer.disconnect();
    const changed = new Set<Node>();
    for (const record of records) {
      if (record.type === 'characterData') changed.add(record.target);
      else for (const node of record.addedNodes) changed.add(node);
    }
    for (const node of changed) annotate(node);
    observer.observe(svg, options);
  });
  annotate(svg);
  observer.observe(svg, options);
  return () => observer.disconnect();
}
