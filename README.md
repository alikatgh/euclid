# Euclid: first twenty lessons

A textbook reading companion: original explanations, selectable mathematical passages, worked demonstrations, and comprehension checks.

This branch retains the deployed three-lesson app’s sidebar, reading column, demonstration panel, playback controls, theme, and text sizing. Lessons 4–20 extend that same interface. Each passage has an “I still don’t understand” worked example in the existing demonstration panel.

The sequence covers Algorithm E and algorithm requirements; computational methods; assignment and state; induction and counterexamples; two-predecessor induction; loop assertions; linear combinations and extended Euclid; numbers, powers, logarithms, floors, and ceilings; sums, products, reindexing, and finite series. These are the opening twenty lessons, not complete coverage of the volume.

References locate concepts in Donald E. Knuth, *The Art of Computer Programming*, Volume 1, third edition, §§1.1–1.2.3. Added prose, examples, questions, and diagrams are original. PDF page references are explicitly distinguished from printed page numbers. The textbook itself is not changed or bundled.

## Preserved baseline

The screenshot-matching app was recovered from [the existing deployment](https://euclid.aulenor.com/):
- JavaScript `/assets/index-CkW7wonR.js`, SHA-256 `6ee436a6e3390c2bf820579e1fb7f7cf931b6207d5d0c0321a5c0a0943d8611a`
- CSS `/assets/index-3JSYf9TI.css`, SHA-256 `95e5efb5447ac993d591dec42af4ccf65ac74f5a54df71d44c373e8b7ad9d0ca`

The CSS is retained byte-for-byte. Source recovery details and limited renderer extensions are documented in `frontend/src/recovered/RECOVERY.md`. The readable shell, lesson adapter, source content, and new SVG renderers are separate from the recovered runtime. The original repository commit alone did not contain the deployed three-lesson version.

Baseline DOM text and tag/class fingerprints were compared against the deployed JavaScript for all three original routes before extension. A graphical Chromium run is unavailable in the current environment; DOM and mathematical tests do not establish screenshot-level layout or perceptual animation quality. Automated accessibility checks identify a pre-existing duplicate named landmark in Algorithm E; this was also present in the deployed baseline.

## Run locally

Use Node.js 24 or later and npm.

```sh
cd frontend
npm ci
npm run dev
```

Open the local address printed by Vite. Lesson content lives in `content/deployed-original.json` and `content/first20/`; Vite includes it in the application build.

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

- `frontend/src/recovered/OriginalShell.js` — extracted original sidebar and workspace, with the additional lesson registry.
- `frontend/src/recovered/runtime.js` — preserved deployed runtime, diagrams, mathematical text, and generic lesson player.
- `frontend/src/recovered/adaptLessons.js` — maps authored content into the original passage/demo/check slots.
- `frontend/src/components/*Demo.tsx` — added SVG demonstrations; their controllers preserve object identity through motion and pause.
- `content/deployed-original.json` — unchanged recovered first-three content snapshot.
- `content/first20/` — added lessons 4–20 and append-only help for the originals.
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
