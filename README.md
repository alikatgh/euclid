# Euclid

Learn to read algorithms through synchronized geometry, mathematical writing, and code.

[Open Euclid](https://euclid.aulenor.com) · [Source](https://github.com/alikatgh/euclid)

Euclid starts with the greatest common divisor: Algorithm E from Donald Knuth's
*The Art of Computer Programming*, Volume 1, §1.1. Its explanations are original
paraphrases, with mathematical notation rendered by KaTeX.

- Step through tape and area diagrams, or play the complete calculation.
- Follow the exact passage corresponding to the current execution step.
- Hover a number to reveal matching values across formulas, prose, diagrams,
  tables, and code. Click to keep the selection; Escape clears it.
- Compare the standard algorithm with the optional initial E0 exchange.
- Continue the same calculation in complete C and Python programs.
- Adjust the text size, theme, and explanation panels.

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
- `content/lessons.json` — lesson metadata, prose, formulas, and code templates.
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
