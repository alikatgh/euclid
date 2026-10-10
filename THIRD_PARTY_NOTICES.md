# Third-party notices

Euclid's original code and explanations use the MIT license. Dependencies retain
their own copyright notices and license terms.

The frontend uses React, D3, Motion, and KaTeX. A build includes
`THIRD_PARTY_LICENSES.txt`, generated from the exact installed runtime dependency
versions and their license files. The source lockfile records dependency versions
and integrity hashes. Build tools have their own licenses in their packages.

KaTeX's bundled fonts are covered by the KaTeX font project's MIT license,
included in `frontend/public/KATEX_FONT_LICENSE.txt` and the deployed assets.
Upstream: https://github.com/KaTeX/katex-fonts/blob/master/LICENSE

The initial lesson follows Algorithm E in Donald E. Knuth, *The Art of Computer
Programming*, Volume 1, §1.1. The algorithm and mathematical example are credited
to that source. Explanations in this repository are independently written
paraphrases, not a reproduction of the book. The MIT license does not license
the book, its scans, or other third-party publications.

## Computer Modern Unicode fonts

The preserved interface uses CMU Serif and CMU Typewriter Text. Six font files
were reconstructed as WOFF from the same family/styles in the public
`computer-modern@0.1.3` package (package SHA-1
`5a2bfdaf150ae57ac7d7df03cdc6c316a53e676b`). Its SIL Open Font License 1.1
and copyright notice are included in `frontend/public/assets/CMU-OFL.txt`.
The conversion preserves font data; the files are not asserted to be byte-identical
to the unavailable deployed WOFF assets.

## Recovered deployed runtime

The preserved deployed JavaScript embeds React/React DOM version 19.3.0 and
KaTeX 0.19.0 (their embedded version strings). The source toolchain lockfile
may contain a different React build; it does not fully describe the recovered
bundle. Retained upstream license comments in that bundle and the included
MIT license texts remain applicable. New JSX-only diagram components do not
instantiate a second hook runtime.
