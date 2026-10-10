# Euclid

Learn to read algorithms through synchronized geometry, mathematical writing, and code.

[Open Euclid](https://euclid.aulenor.com) · [Source](https://github.com/alikatgh/euclid)

The review curriculum contains twenty lessons, from algorithms and proof to real-number notation and finite sums (Volume 1, §§1.1–1.2.3). It does not claim to cover the whole volume. The original reference player is lesson 1 and remains the default.

Euclid starts with the greatest common divisor: Algorithm E from Donald Knuth's
*The Art of Computer Programming*, Volume 1, §1.1. Its explanations are original
paraphrases, with mathematical notation rendered by KaTeX.

- Step through tape and area diagrams, or play the complete calculation.
- Follow the exact passage corresponding to the current execution step.
- Hover a number to reveal matching values across formulas, prose, diagrams,
  tables, and code. Click to keep the selection; Escape clears it.
- Compare the standard algorithm with the optional initial E0 exchange.
- Continue the same calculation in complete C and Python programs.
- Adjust the text size, theme, and explanation panels; text size persists between lessons.
- Choose a lesson from the course map, or use a shareable `#lesson=...` fragment.
- Change the new lessons' numeric parameters and see the geometry, formulas, current state, code, and prediction answers recompute together.
- Pause or step through a proof; autoplay pauses at prediction checkpoints. Respect the system's reduced-motion setting.
- Read original formal explanations alongside concrete intuition and notation-reading guidance.

The published application runs entirely in the browser. It needs no account,
API key, database, or server-side computation.

## Run locally

Use Node.js 24 or later and npm.

```sh
cd frontend
npm ci
npm run dev
```

Open the local address printed by Vite. Lesson content lives in
`content/lessons.json`; Vite includes it in the application build.

## Verify and build

```sh
cd frontend
npm test
npm run lint
npm run build
npm run preview
```

The tests run the generated Python examples and syntax-check C when their tools
are installed. Executing compiled C examples is optional: set
`CODE_WALKTHROUGH_SCRATCH` to a private writable scratch directory to enable that check.

The build produces `frontend/dist`. Serve that directory on a static host.
`frontend/public/_headers` provides security headers for Cloudflare static
hosting. Other hosts should apply equivalent response headers.

## Project structure

- `frontend/src/components/` — player, diagrams, reading, and code views.
- `frontend/src/lib/` — mathematical prose, code generation, and numeric links.
- `frontend/src/hooks/useAlgorithm.ts` — the bounded execution trace.
- `content/lessons.json` — the unchanged reference lesson's prose, formulas, and code templates.
- `frontend/src/lessons/` — original parameterized curriculum models, lessons 2–20.
- `frontend/src/types/curriculum.ts` — typed lesson, scene, code, and exercise contracts.
- `frontend/src/components/CurriculumPlayer.tsx` — shared accessible player and reading views.
- `frontend/src/components/CurriculumScene.tsx` — concept-specific SVG geometry.
- `frontend/src/lib/algorithmOperations.ts` — explicit operation counts, independent of animation frames.
- `server.py` — optional FastAPI static server and lesson JSON endpoint.

New mathematical prose should use `MathematicalText`; formulas use
`renderLinkedMath`. Both automatically identify numeric literals. Plain numeric
UI values use `LinkedNumber` or `LinkedText`. D3 scenes use
`observeSvgMathConnections`; semantic shapes declare `data-math-value` or
`data-math-values`. Keep these inside the `MathConnections` boundary so hover,
focus, and pinned selections remain shared.

## Optional Python server

After building the frontend:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python server.py
```

The server exposes `/health`, `/api/lessons`, and the built frontend on port 8000.
Run its path-containment regressions with `python3 -m unittest test_server`.
The public deployment uses static assets and does not run this server.

## Deployment

The Cloudflare configuration in `wrangler.jsonc` serves only static assets:
there is no Worker script, storage binding, scheduled task, or paid API.
After verifying and building, an authenticated Cloudflare account can deploy:

```sh
npx wrangler deploy
```

The custom domain is `euclid.aulenor.com`. Domain configuration belongs to the
site owner; forks should choose their own Worker name and domain. A release can
be recovered by redeploying the build from a previous Git commit.

## License and attribution

Original Euclid source and explanations are available under the [MIT License](LICENSE).
Third-party libraries and fonts retain their own licenses; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This project is an independent
teaching tool and is not affiliated with Donald Knuth or the book's publisher.

## Counting and correctness

The reference GCD function accepts finite integers from 1 through 9999 and rejects
unsupported inputs before computing a trace. A remainder division, a zero test,
an optional ordering test, an exchange, and a pair update are distinct abstract
operations. These are not processor-instruction counts or wall-clock timings.
The reference player combines each unsuccessful E2 test with the following E3
frame; counting frames therefore does not count operations. For example, `(84, 33)`
uses four remainder divisions. Reversing the inputs adds one zero-quotient division,
unless the optional E0 exchange is enabled.

## Authoring and verification

A new lesson defines a pure `buildFrames(inputs)` function. All visual quantities,
variables, equations, counters, and prediction answers must derive from those
inputs. Scene indices and compression rules are documented in the types and
renderer helpers. Preserve precise source-section references while writing new
explanations and examples; do not include book pages, scans, or private source links.

`npm test` includes mathematical boundary checks, generated Python execution,
KaTeX validation, and server-side SVG render smoke tests. Server-side rendering
checks markup and numeric geometry; it does not verify browser layout, actual
keyboard interaction, responsive layout, or animation. Those require a real
browser review in addition to a passing build.
