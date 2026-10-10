# Linked mathematical reading

The recovered player retains its original DOM layout and deployed stylesheet. The shared connection controller extends its existing `data-math-linked` highlighting to mathematical letters, numbers, compound indexed terms, and operators. A compact, transient tooltip explains the selected role.

## Interaction

- Hover a token to highlight identified uses within the current passage and worked example.
- Focus a standalone formula token or SVG label for the same result. Enter/Space pins it.
- Within an existing reading-passage button, focus the button and use Left/Right to explore its tokens. Enter retains the original passage-selection action. Tokens do not become nested interactive controls.
- Tap a token to pin/unpin. Escape, an outside pointer press, or changing frame, passage, example, or lesson clears the selection.
- Interactive SVGs become labeled groups at runtime; their title/description and KaTeX's complete MathML remain available.

## Identity contract

`frontend/src/lib/symbolConnections.js` tokenizes React-owned label output before React renders it, annotates generated KaTeX HTML using its MathML structure, and delegates interaction at the original player boundary. It never splits React-owned text nodes after rendering.

- `data-math-token`: the visible mathematical token.
- `data-math-keys`: optional authored selection identities.
- `data-math-memberships`: passive memberships. A summation operator can select all included terms through `operation:sum`; selecting one term does not select every other term.
- `data-math-role`, `data-math-description`: accessible explanation of an authored correspondence.
- `data-math-script`, `data-math-bound`, `data-math-index-symbol`: script/bound context from generated MathML.
- `data-math-resolved`, `data-math-linked`: runtime diagnostics/highlight state.

Binding modules return `{keys, memberships?, role, description}`. Local keys receive a current lesson/passage/example scope automatically. Binding priority is original Euclid roles, authored full-book families, early-book families, explicit attributes, then a conservative fallback.

Known index addresses, summand values, accumulators, coefficients, byte positions, object IDs, addresses, sizes, and quotient/remainder roles are distinct. Numerical equality is not an entity ID. In particular, a selected address 2 is distinct from a term with value 2, and q=1 is distinct from r=1. The original generic first-three numeric memberships remain supported where no more-specific role is available.

Otherwise-unidentified new numerical occurrences use a separately named same-displayed-value fallback. Its tooltip explicitly says those numbers may have different mathematical roles; it does not borrow authored position, value, address, size or other entity keys. Known ambiguous original quantities and scripts retain occurrence-local or role-specific identities. Repeated named symbols receive an explicitly worded same-symbol fallback within the example. Operator explanations remain useful even if that model has no authored physical target.

## Checks

The test suite covers token boundaries, prose articles, operator aliases, collected-term identity, index/value distinction, script/bound distinctions, blank passage formulas, and the pre-existing mathematical/motion contracts. jsdom acceptance checks exercise real pointer/focus/key/tap events and frame/route cleanup. A graphical browser remains unavailable in this environment; DOM and SVG checks are not screenshot acceptance.

Authored numeral text can participate passively in the written-value fallback. Its own selection remains semantic: selecting byte position 2 does not select byte value 2. Selecting an otherwise-unbound printed 2 may show both printed numerals, with the explicit lexical explanation, without asserting that their objects or quantities are the same.
