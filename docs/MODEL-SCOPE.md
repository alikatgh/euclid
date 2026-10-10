# What the models establish

These lessons connect notation to a concrete, inspectable state. Each demonstration has an executable deterministic authoring model, and its displayed values are checked against exact identities, independent reference calculations, or exhaustive small instances where appropriate. Generated frames are played in the browser; playing a frame does not secretly run a remote program or use an AI service.

## How a visual should teach

Introduce the concrete objects and their quantities before translating them into compressed notation. Name each new symbol beside its local use, distinguish a position or index from the value stored there, and show how the operands produce the next state. A final correct equation is not enough to explain an operation. Preserve the objects or prior values needed to understand what changed.

Smaller examples must have their own aligned objects, values, formulas, and reasoning; an unrelated main-example formula must not appear beside them. An intentionally empty formula is respected until that step introduces one. The adapter displays explicitly reviewed `teachingExplanation` text, not animation-author transition instructions. Transition metadata remains available to the renderer without becoming teaching prose.

These are authoring and review criteria, not a claim that test counts measure human understanding. Learner feedback remains necessary.

## Mathematics

Integers and rational values use exact arithmetic in the authoring models. Decimal and asymptotic scenes identify approximation, truncation, domains, and error bounds. Generating functions are explicitly distinguished as formal series versus analytic functions. A finite picture cannot establish convergence, infinite branching, universal termination, or asymptotic big-O quantifiers.

Euler–Maclaurin, Bernoulli, Stirling, and incomplete-gamma examples teach the stated hypotheses and displayed derivation steps. A numerically checked residual is an implementation check, not a proof of a uniform estimate. When the course gives only a justified lower-order route, it does not advertise that route as deriving all higher coefficients in the source.

## MIX and programming

The executable MIX model implements the declared integer, non-I/O subset needed by the original programs and semantic edge tests. The assembler implements the documented subset of MIXAL used by those programs. Device, buffering, tracing, coroutine, and interpretive models are explicit teaching models, not a claim that a complete historical MIX system is emulated in the browser. Unsupported operations and undefined cases are named rather than silently assigned invented semantics.

The visible program listings are original to this course. Their memory words, fetch/execute states, side effects, execution counts, and timing are produced by the included models. Source-line links distinguish executable instructions from assembly directives and data words.

## Data structures

Identity, address, value, ownership, and reachability are distinct. Linked structures expose which invariant holds at stable boundaries and which temporary inconsistency is protected during an update. Auxiliary arrays, marks, parent fields, stacks, and restart scans are disclosed; no model claims constant workspace while hiding a bookkeeping table.

Canonical polynomial and tree representations state their conventions. Where a source algorithm's full general implementation is outside a small demonstration, the lesson distinguishes the bounded executed mechanism from the broader algorithm. A reference dictionary is an independent correctness oracle, not a replacement proof of pointer invariants.

## Storage management

Allocator models use finite, explicit arenas and requests. Every committed operation checks live/free partition and relevant alignment/link/tag invariants. Workload comparisons apply only to the declared sizes and operation sequence; they do not establish one universally optimal allocation policy. Teaching allocators are not production memory managers.

## Verification limits

Unit and semantic tests, DOM interaction sweeps, and isolated SVG geometry/raster checks complement one another. They do not establish full-browser responsive layout, measured contrast, assistive-technology behavior, or perceptual animation quality. These still require graphical-browser review. The inherited Algorithm E landmark warning is documented separately from new-route checks.
