# Deployment recovery and integration provenance

The repository commit 1c8a95f did not contain the owner's screenshot version. The publicly deployed application at https://euclid.aulenor.com did.

Recovered on 2026-10-10:
- JS: /assets/index-CkW7wonR.js
- CSS: /assets/index-3JSYf9TI.css
- Embedded content: content/deployed-original.json (algorithm, algorithmFeatures, computationalMethods)

runtime.js preserves the deployed application dependencies, diagrams and lesson renderer. OriginalShell.js is the readable extracted shell. The mount was moved to main.tsx. Registry additions use its existing navigation and reading/demo panes. No rejected curriculum header/layout is imported.

The deployed stylesheet is preserved byte-for-byte as public/assets/original.css. KaTeX font files are restored from the installed KaTeX package with the same asset filenames. Six CMU WOFF files were unavailable from the deployment and were regenerated losslessly with fontTools from public npm computer-modern@0.1.3 TTFs (npm shasum 5a2bfdaf150ae57ac7d7df03cdc6c316a53e676b). These are the same CMU family/styles, not verified byte-identical deployment assets. License: public/assets/CMU-OFL.txt.

Baseline jsdom comparison before adding lessons: all three routes had exactly matching text and DOM tag/class fingerprints (3336 / 812 / 817 elements), with SVG measurement mocked equally in both versions. This is DOM verification, not screenshot/layout verification in a graphical browser.

Small intentional extensions to deployed behavior:
- Additional lesson registry/navigation in the existing sidebar.
- Optional next lesson from original lesson 3.
- Per-example comprehension check selection, allowing simpler-help checks.
- Explicit motion-pause state passed to added visual components; manual step changes animate and inactive routes freeze.
- Lesson 1 smaller help stays inside its existing diagram/current-reading region, preserving its main execution state.
- Formula-only new passage buttons receive an accessible name; retained lesson instances preserve their selection and answers.

Original textbook source is not changed or bundled. Added explanations, models and questions are original teaching material linked to textbook sections/notation.
