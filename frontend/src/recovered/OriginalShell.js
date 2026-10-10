import { OriginalAlgorithmVisual } from './mainVisualAdapters.js';
// Recovered from the owner’s deployed first-three-lesson app; original DOM and classes retained.
import { React as _, JSX as C, x, Lw, b, go, RC, UC, KC, tw, bo, w, Pw, Iw } from "./runtime.js";
import { additionalLessons, AdditionalVisual, OriginalFeatureVisual, OriginalMethodVisual, AlgorithmHelpVisual, algorithmHelp } from "./registry.js";
function Rw() { const id = window.location.hash.slice(1); return [
    "algorithm-e", "algorithm-features", "computational-methods", ...additionalLessons.map(entry => entry.id)
].includes(id) ? id : "algorithm-e"; }
export function OriginalShell() {
    let { theme: e, toggleTheme: t } = x(), n = Lw, r = Lw.algorithmFeatures, i = Lw.computationalMethods, [a, o] = (0, _.useState)(() => window.matchMedia(`(max-width: 959px)`).matches), [s, c] = (0, _.useState)(() => {
        try {
            let e = window.localStorage.getItem(`euclid.sidebar.open`);
            if (e !== null)
                return e === `true`;
        }
        catch { }
        return window.matchMedia(`(min-width: 960px)`).matches;
    }), [l, u] = (0, _.useState)(null), d = (0, _.useRef)(null), f = (0, _.useCallback)(() => { c(!1), d.current?.focus(); }, []), p = () => { a && f(); };
    (0, _.useEffect)(() => { let e = window.matchMedia(`(max-width: 959px)`), t = () => o(e.matches); return e.addEventListener(`change`, t), () => e.removeEventListener(`change`, t); }, []), (0, _.useEffect)(() => {
        try {
            window.localStorage.setItem(`euclid.sidebar.open`, String(s));
        }
        catch { }
        if (!s)
            return;
        let e = e => { e.key === `Escape` && f(); };
        return window.addEventListener(`keydown`, e), () => window.removeEventListener(`keydown`, e);
    }, [s, f]);
    const [algorithmHelpOpen, setAlgorithmHelpOpen] = _.useState(false), [algorithmHelpFrame, setAlgorithmHelpFrame] = _.useState(0), [algorithmHelpAnswer, setAlgorithmHelpAnswer] = _.useState(null);
    let [m, h] = (0, _.useState)(Rw), [g, v] = (0, _.useState)(119), [y, S] = (0, _.useState)(544), [T, E] = (0, _.useState)(!1), [D, ee] = (0, _.useState)(`tape`), [te, O] = (0, _.useState)(0), [ne, re] = (0, _.useState)(!1), [ie, ae] = (0, _.useState)(1), [oe, se] = (0, _.useState)(`explanation`), [ce, le] = (0, _.useState)({
        formula: !0, steps: !0, example: !0
    }), [k, ue] = (0, _.useState)(!1);
    (0, _.useEffect)(() => { let e = () => { re(!1), h(Rw()); }; return window.addEventListener(`hashchange`, e), () => window.removeEventListener(`hashchange`, e); }, []);
    let de = e => { re(!1), h(e), window.location.hash = e, p(); }, A = b(g, y, T, n);
    (0, _.useEffect)(() => {
        if (m !== `algorithm-e` || !ne || te >= A.length - 1)
            return;
        let e = window.setTimeout(() => { let e = Math.min(te + 1, A.length - 1); e === A.length - 1 && re(!1), O(e); }, Math.round(1600 / ie));
        return () => window.clearTimeout(e);
    }, [
        m, ne, te, A.length, ie
    ]);
    let fe = (0, _.useCallback)(e => { re(!1), O(Math.max(0, Math.min(e, A.length - 1))); }, [A.length]), pe = (0, _.useCallback)(() => { re(!1), O(e => Math.min(e + 1, A.length - 1)); }, [A.length]), me = (0, _.useCallback)(() => { re(!1), O(e => Math.max(e - 1, 0)); }, []), he = (0, _.useCallback)(() => { re(!1), O(0); }, []), ge = e => { e !== g && (he(), v(e)); }, _e = e => { e !== y && (he(), S(e)); }, ve = e => { e !== T && (he(), E(e)); }, ye = (0, _.useCallback)(() => { A.length !== 0 && (te >= A.length - 1 ? (O(0), re(!0)) : re(e => !e)); }, [te, A.length]);
    (0, _.useEffect)(() => {
        if (m !== `algorithm-e` || algorithmHelpOpen || a && s)
            return;
        let e = e => {
            if (e.defaultPrevented || e.isComposing || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey)
                return;
            let t = e.target;
            t instanceof HTMLElement && (t.isContentEditable || t.closest(`input, textarea, select, button, a[href], [data-reading-scroll], [role="button"], [role="slider"], [role="spinbutton"], [role="textbox"]`)) || (e.key === `ArrowRight` ? (e.preventDefault(), pe()) : e.key === `ArrowLeft` ? (e.preventDefault(), me()) : e.key === ` ` && (e.preventDefault(), e.repeat || ye()));
        };
        return window.addEventListener(`keydown`, e), () => window.removeEventListener(`keydown`, e);
    }, [
        m, algorithmHelpOpen, a, s, pe, me, ye
    ]);
    let [j, M] = (0, _.useState)(1);
    (0, _.useEffect)(() => { document.documentElement.style.fontSize = `${j * 100}%`, document.documentElement.style.setProperty(`--app-font-scale`, j.toString()); }, [j]);
    const visitedLessons = _.useRef(new Set());
    visitedLessons.current.add(m);
    let be = () => { M(e => Math.min(1.35, +(e + .1).toFixed(2))); }, xe = () => { M(e => Math.max(.85, +(e - .1).toFixed(2))); }, Se = () => { M(1); }, N = A[te] || A[0], Ce = (0, _.useRef)(null);
    (0, _.useEffect)(() => { Ce.current && (Ce.current.scrollTop = 0); }, [N]);
    let we = n?.algorithm.codeWalkthrough || Lw.algorithm.codeWalkthrough, Te = n?.algorithm.mathematicalReading || Lw.algorithm.mathematicalReading, Ee = additionalLessons.find(entry => entry.id === m) || (m === `computational-methods` ? i : m === `algorithm-features` ? r : n.algorithm);
    return (0, C.jsxs)(`div`, {
        className: `lesson-shell bg-page text-main font-sans`, "data-sidebar-open": s, children: [
            (0, C.jsx)(`div`, {
                className: `lesson-shell-rail`, children: (0, C.jsx)(`button`, {
                    ref: d, type: `button`, className: `lesson-sidebar-toggle`, "aria-label": s ? `Hide sidebar` : `Show sidebar`, title: s ? `Hide sidebar` : `Show sidebar`, "aria-expanded": s, "aria-controls": `lesson-navigation-sidebar`, onClick: () => c(e => !e), children: (0, C.jsxs)(`svg`, {
                        viewBox: `0 0 24 24`, width: `20`, height: `20`, fill: `none`, stroke: `currentColor`, strokeWidth: `1.6`, "aria-hidden": `true`, children: [
                            (0, C.jsx)(`rect`, {
                                x: `3`, y: `4`, width: `18`, height: `16`
                            }), (0, C.jsx)(`path`, {
                                d: `M 9 4 V 20`
                            }), (0, C.jsx)(`path`, {
                                d: s ? `m 16 9 -3 3 3 3` : `m 13 9 3 3 -3 3`
                            })
                        ]
                    })
                })
            }), (0, C.jsxs)(`aside`, {
                id: `lesson-navigation-sidebar`, className: `lesson-navigation-sidebar`, "aria-label": `Lessons and settings`, hidden: !s, children: [
                    (0, C.jsx)(w, {
                        applicationName: n?.application?.name || Lw.application.name, title: Ee.title, subtitle: Ee.subtitle, showAlgorithmOptions: m === `algorithm-e`, withE0: T, onToggleE0: ve, theme: e, onToggleTheme: t, fontScale: j, onIncreaseFontSize: be, onDecreaseFontSize: xe, onResetFontSize: Se
                    }), (0, C.jsx)(`nav`, {
                        "aria-label": `Lessons`, className: `lesson-navigation-links`, style: additionalLessons.length > 30 ? {maxHeight: `32vh`, overflowY: `auto`, overscrollBehavior: `contain`} : undefined, children: [
                            `algorithm-e`, `algorithm-features`, `computational-methods`, ...additionalLessons.map(entry => entry.id)
                        ].map(e => (0, C.jsx)(`a`, {
                            href: `#${e}`, onClick: p, "aria-current": m === e ? `page` : void 0, className: `py-1 focus-visible:outline-2 focus-visible:outline-blue-600 ${m === e ? `text-main font-semibold underline underline-offset-4` : `text-muted hover:text-main`}`, children: e === `algorithm-e` ? r.previousLessonLabel : e === `algorithm-features` ? r.navigationLabel : e === `computational-methods` ? i.navigationLabel : additionalLessons.find(entry => entry.id === e).navigationLabel
                        }, e))
                    }), (0, C.jsx)(`div`, {
                        ref: u, className: `lesson-section-navigation`
                    })
                ]
            }), s && a && (0, C.jsx)(`button`, {
                type: `button`, className: `lesson-sidebar-backdrop`, "aria-label": `Close sidebar`, onClick: f
            }), (0, C.jsxs)(`div`, {
                className: `lesson-workspace`, inert: a && s, children: [
                    (0, C.jsx)(`div`, {
                        className: m === `algorithm-features` ? `flex flex-1 min-h-0` : `hidden`, children: (0, C.jsx)(Pw, {
                            content: r, active: m === `algorithm-features`, navigationContainer: l, onNavigate: p, onPreviousLesson: () => de(`algorithm-e`), onNextLesson: () => de(`computational-methods`), nextLessonLabel: i.navigationLabel, Visual: OriginalFeatureVisual
                        })
                    }), (0, C.jsx)(`div`, {
                        className: m === `computational-methods` ? `flex flex-1 min-h-0` : `hidden`, children: (0, C.jsx)(Pw, {
                            content: i, active: m === `computational-methods`, navigationContainer: l, onNavigate: p, onPreviousLesson: () => de(`algorithm-features`), Visual: OriginalMethodVisual, onNextLesson: additionalLessons.length ? () => de(additionalLessons[0].id) : undefined, nextLessonLabel: additionalLessons[0]?.navigationLabel
                        })
                    }), ...additionalLessons.map((entry, index) => visitedLessons.current.has(entry.id) ? C.jsx(`div`, {
                        className: m === entry.id ? `flex flex-1 min-h-0` : `hidden`, children: C.jsx(Pw, {
                            content: entry, active: m === entry.id, navigationContainer: l, onNavigate: p, onPreviousLesson: () => de(index ? additionalLessons[index - 1].id : `computational-methods`), onNextLesson: index + 1 < additionalLessons.length ? () => de(additionalLessons[index + 1].id) : undefined, nextLessonLabel: additionalLessons[index + 1]?.navigationLabel, Visual: AdditionalVisual
                        }, entry.id)
                    }, entry.id) : null), m === `algorithm-e` && N && (0, C.jsxs)(go, {
                        as: `main`, className: `lesson-layout`, resetKey: `${g}:${y}:${T}:${te}:${algorithmHelpOpen}:${algorithmHelpFrame}`, connectionContext: algorithmHelpOpen ? undefined : {originalStep: N}, children: [
                            (0, C.jsxs)(`div`, {
                                className: `visual-reading-column`, children: [(0, C.jsx)(`div`, {
                                        className: `visual-reading-diagram`, children: algorithmHelpOpen ? C.jsx(AlgorithmHelpVisual, {
                                            exampleId: algorithmHelp.id, frameIndex: algorithmHelpFrame, frame: algorithmHelp.frames[algorithmHelpFrame], visual: algorithmHelp.frames[algorithmHelpFrame].visual, paused: false
                                        }) : (0, C.jsx)(OriginalAlgorithmVisual, {
                                            step: N, viewType: D, playbackSpeed: ie, labels: n?.algorithm.visualization || Lw.algorithm.visualization
                                        })
                                    }), (0, C.jsxs)(`section`, {
                                        ref: Ce, className: `current-reading`, "aria-labelledby": `current-reading-title`, tabIndex: 0, "data-reading-scroll": !0, children: [
                                            (0, C.jsx)(`h2`, {
                                                id: `current-reading-title`, children: algorithmHelpOpen ? `Smaller worked example · original run paused` : Te.currentStepTitle
                                            }), (0, C.jsx)(`p`, {
                                                className: `mathematical-prose`, children: (0, C.jsx)(RC, {
                                                    text: algorithmHelpOpen ? algorithmHelp.frames[algorithmHelpFrame].explanation : UC(N, Te)
                                                })
                                            }), C.jsxs(`div`, {
                                                className: `flex flex-wrap gap-1 pt-2`, children: [
                                                    C.jsx(`button`, {
                                                        type: `button`, className: `features-control`, onClick: () => { re(false); setAlgorithmHelpOpen(!algorithmHelpOpen); }, children: algorithmHelpOpen ? `Back to the original explanation` : `I still don’t understand`
                                                    }), algorithmHelpOpen && C.jsxs(C.Fragment, {
                                                        children: [
                                                            C.jsx(`button`, {
                                                                type: `button`, className: `features-control`, disabled: algorithmHelpFrame === 0, onClick: () => setAlgorithmHelpFrame(Math.max(0, algorithmHelpFrame - 1)), children: `Previous`
                                                            }), C.jsx(`button`, {
                                                                type: `button`, className: `features-control`, onClick: () => setAlgorithmHelpFrame(0), children: `Replay`
                                                            }), C.jsx(`button`, {
                                                                type: `button`, className: `features-control`, disabled: algorithmHelpFrame === algorithmHelp.frames.length - 1, onClick: () => setAlgorithmHelpFrame(Math.min(algorithmHelp.frames.length - 1, algorithmHelpFrame + 1)), children: `Next`
                                                            })
                                                        ]
                                                    }), algorithmHelpOpen && algorithmHelpFrame === algorithmHelp.frames.length - 1 && C.jsxs(`section`, {
                                                        className: `features-check`, children: [
                                                            C.jsx(`p`, {
                                                                children: algorithmHelp.check.prompt
                                                            }), ...algorithmHelp.check.options.map(option => C.jsx(`button`, {
                                                                type: `button`, className: `features-answer`, "aria-pressed":algorithmHelpAnswer===option.id, onClick: () => setAlgorithmHelpAnswer(option.id), children: option.text
                                                            }, option.id)), algorithmHelpAnswer && C.jsx(`p`, {
                                                                role: `status`, children: `${algorithmHelp.check.options.find(option => option.id === algorithmHelpAnswer)?.correct ? "Correct. " : "Try again. "}${algorithmHelp.check.options.find(option => option.id === algorithmHelpAnswer)?.feedback}`
                                                            })
                                                        ]
                                                    })
                                                ]
                                            })
                                        ]
                                    })]
                            }), (0, C.jsxs)(`div`, {
                                className: `lesson-reading-column flex flex-col gap-2.5 min-h-0 min-w-0 overflow-hidden`, children: [(0, C.jsxs)(`div`, {
                                        className: `shrink-0 flex flex-wrap items-center gap-x-3 gap-y-1.5`, children: [(0, C.jsx)(`span`, {
                                                className: `text-xs font-mono text-dim`, children: we.continueLabel
                                            }), (0, C.jsx)(`div`, {
                                                role: `group`, "aria-label": we.continueLabel, className: `flex border border-border bg-surface`, children: [
                                                    `explanation`, `c`, `python`
                                                ].map(e => (0, C.jsx)(`button`, {
                                                    type: `button`, "aria-pressed": oe === e, onClick: () => se(e), className: `px-2.5 py-1.5 text-xs font-mono focus-visible:outline-2 focus-visible:outline-blue-600 ${oe === e ? `bg-blue-600 text-white font-bold` : `text-main hover:bg-border`}`, children: e === `explanation` ? we.explanationTabLabel : we.languageLabels[e]
                                                }, e))
                                            })]
                                    }), (0, C.jsx)(`div`, {
                                        className: `flex-1 min-h-0`, children: oe === `explanation` ? (0, C.jsx)(KC, {
                                            step: N, steps: A, stepsDefinitions: n?.algorithm.steps_definition || Lw.algorithm.steps_definition, content: Te, withE0: T, panels: ce, onTogglePanel: e => le(t => ({
                                                ...t, [e]: !t[e]
                                            }))
                                        }) : (0, C.jsx)(tw, {
                                            step: N, language: oe, withE0: T, content: we
                                        }, oe)
                                    })]
                            }), (0, C.jsxs)(`div`, {
                                className: `lesson-controls-column flex min-h-0 flex-col gap-2.5 max-lg:shrink-0 max-lg:h-[40rem]`, children: [(0, C.jsx)(bo, {
                                        m: g, n: y, onMChange: ge, onNChange: _e, presets: n?.algorithm.presets || [], viewType: D, onViewTypeChange: ee, isPlaying: ne, onTogglePlay: () => { setAlgorithmHelpOpen(false); ye(); }, onNext: () => { setAlgorithmHelpOpen(false); pe(); }, onPrev: () => { setAlgorithmHelpOpen(false); me(); }, onReset: () => { setAlgorithmHelpOpen(false); he(); }, canNext: te < A.length - 1, canPrev: te > 0, currentStep: te, totalSteps: A.length, steps: A, onSeekStep: fe, playbackSpeed: ie, onPlaybackSpeedChange: ae, isStepListOpen: k, onToggleStepList: () => ue(e => !e)
                                    }), (0, C.jsxs)(`a`, {
                                        href: `#algorithm-features`, className: `shrink-0 border border-border bg-surface px-3 py-2 text-sm text-main hover:bg-border focus-visible:outline-2 focus-visible:outline-blue-600`, children: [r.nextLessonLabel, ` →`]
                                    })]
                            })
                        ]
                    })
                ]
            })
        ]
    });
}
