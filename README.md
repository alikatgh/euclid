# Euclid: Fundamental Algorithms, visual reading companion

A textbook reading companion: original explanations, selectable mathematical passages, worked demonstrations, and comprehension checks.

This branch retains the deployed three-lesson app’s sidebar, reading column, demonstration panel, playback controls, theme, and text sizing. Lessons 4–144 use that same interface. The first twenty retain their topics and reading structure, with corrected demonstrations, clearer notation bridges, and independently aligned smaller examples. The longer lesson list scrolls inside its existing sidebar so the current lesson contents remain reachable. Each passage has an “I still don’t understand” worked example in the existing demonstration panel.

The 144-lesson sequence covers the instructional sections of Donald E. Knuth's *The Art of Computer Programming*, Volume 1: *Fundamental Algorithms*, third edition: algorithms and discrete mathematics; generating functions and asymptotic analysis; MIX and programming techniques; linear structures; trees; multilinked structures; and dynamic storage allocation.

This is an original companion to the source, not a reproduction of every page, exercise, answer, historical note, or numerical table. Each new lesson connects formal statements to computed examples, spatial demonstrations, smaller explanations, and original transfer questions. Source locators distinguish one-based ebook PDF pages from printed page numbers. The textbook is unchanged and is not bundled. See [the curriculum and source map](docs/CURRICULUM.md) and [model scope](docs/MODEL-SCOPE.md).

Finite experiments verify implementations and illustrate claims; they are not proofs of infinite mathematical statements. The reading explains the required domains, invariants, quantifiers, and proof conditions. Advanced derivations and executable models state their limits explicitly.

## Preserved baseline

The screenshot-matching app was recovered from [the existing deployment](https://euclid.aulenor.com/):
- JavaScript `/assets/index-CkW7wonR.js`, SHA-256 `6ee436a6e3390c2bf820579e1fb7f7cf931b6207d5d0c0321a5c0a0943d8611a`
- CSS `/assets/index-3JSYf9TI.css`, SHA-256 `95e5efb5447ac993d591dec42af4ccf65ac74f5a54df71d44c373e8b7ad9d0ca`

The CSS is retained byte-for-byte. Source recovery details and limited renderer extensions are documented in `frontend/src/recovered/RECOVERY.md`. The readable shell, lesson adapter, source content, and new SVG renderers are separate from the recovered runtime. The original repository commit alone did not contain the deployed three-lesson version.

Baseline DOM text and tag/class fingerprints were compared against the deployed JavaScript for all three original routes before extension. A graphical Chromium run is unavailable in the current environment; DOM and mathematical tests do not establish screenshot-level layout or perceptual animation quality. Automated accessibility checks identify a pre-existing duplicate named landmark in Algorithm E; this was also present in the deployed baseline.

## Follow a symbol through an explanation

Hover a mathematical number, letter, or operator to inspect its matching uses in the active reading and visible demonstration. Authored bindings distinguish roles such as an index, a term value, a register, or a tree-node identity. Where only the written value or symbol is known, the explanation identifies that narrower match rather than claiming that two different objects are the same.

Click or tap a token to keep its links highlighted; Escape clears them. Keyboard users can focus diagram tokens, or focus a reading button and use Left/Right to inspect its mathematical tokens. Highlighting clears when the active example, frame, or lesson changes. The original reading layout is retained.

## Run locally

Use Node.js 24 or later and npm. Python 3 is also required for the reproducible mathematical models and their tests.

```sh
cd frontend
npm ci
npm run dev
```

Open the local address printed by Vite. Lesson content lives in `content/deployed-original.json`, `content/first20/`, and `content/fullbook/`; Vite includes it in the application build.

## Verify and build

```sh
cd frontend
FULLBOOK_COMPLETE=1 npm test
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

- `frontend/src/recovered/OriginalShell.js` — extracted original sidebar and workspace, with the additional lesson registry.
- `frontend/src/recovered/runtime.js` — preserved deployed runtime, diagrams, mathematical text, and generic lesson player.
- `frontend/src/recovered/adaptLessons.js` — maps authored content into the original passage/demo/check slots.
- `frontend/src/components/*Demo.tsx` — added SVG demonstrations; their controllers preserve object identity through motion and pause.
- `content/deployed-original.json` — unchanged recovered first-three content snapshot.
- `content/first20/` — lessons 4–20 with revised teaching scenes, plus supplemental help for the original three.
- `content/fullbook/batch-A.json` through `batch-F.json` — lessons 21–144 with computed main and smaller-example states.
- `content/fullbook/source-plan-*.json` — portable source locators and learning objectives used by the generators.
- `scripts/fullbook-batch-*.py` — readable deterministic authoring/model code; generated JSON can be reproduced without obtaining or shipping the textbook.
- `frontend/src/components/FullBookScene.tsx` — draws topic-authored spatial objects; it does not substitute a generic graph for each concept.
- `frontend/src/components/fullBookMotion.ts` — stable identity, directed-edge interpolation, staged operations, truthful result timing, and idle pause.
- `frontend/public/assets/original.css` — exact deployed stylesheet and its local font assets.
- `frontend/src/lib/*.test.mjs` — math, content, rendering, animation, and original algorithm regression tests.
- `server.py` — optional static server; its historical `/api/lessons` endpoint still returns the original single-lesson JSON. The current app bundles its full content and does not depend on that endpoint.

The original source components and calculation libraries are retained for provenance and regression tests. The active entry point mounts the recovered shell. Added content is rendered through the original mathematical prose and numerical-linking machinery, rather than a separate curriculum layout.

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

## Verification scope

`npm test` includes original algorithm checks and added content/diagram/motion regressions. Set `CODE_WALKTHROUGH_SCRATCH` to a private writable directory to include compiled C execution. DOM route/control sweeps supplement these checks; they do not replace a graphical-browser review. `npm run lint` reports inherited warnings in the recovered minified runtime and extracted shell, with no lint errors in the verified snapshot.

## Reproduce the new lessons

Each batch's standard-library Python script regenerates its checked-in JSON.

```sh
for batch in A B C D E F; do
  python3 "scripts/fullbook-batch-$batch.py"
done
cd frontend
FULLBOOK_COMPLETE=1 CODE_WALKTHROUGH_SCRATCH=/tmp/euclid-c-tests npm test
```

The course is static and local to the browser. No book PDF, credentials, paid API, or external inference service is needed to play its demonstrations.
