# barr

BARR is a fairness-oriented reasoning intervention workflow built around one practical idea:
use transition-point signals to decide when strong redirection should be applied.

## Storyline (Current Mainline)

1. Quantization can increase fairness risk in reasoning QA, especially on ambiguous settings.
2. Redirect-style intervention is powerful but high-risk when applied to all samples.
3. The value of transition points is mainly detection, not a magical injection location.
4. BARR uses selective triggering:
	detect high-risk trajectories at transition time, redirect only those samples.
5. Target outcome:
	keep most bias-correction gains while minimizing collateral harm on originally correct samples.

## What Current Evidence Supports

- Blanket redirect is strongest on correction, but causes large collateral harm.
- Always-reflect is safer than blanket redirect, but still has notable harm and cost.
- Selective BARR under strict-online protocol shows the best utility-harm balance in held-out evaluation.

Recent held-out strict-online snapshot (AWQ age slice):
- selective text-level trigger: correction `70.0%`, harm `1.39%`, net benefit `+30`
- always-reflect: correction `88.0%`, harm `7.76%`, net benefit `+16`
- blanket redirect: correction `100.0%`, harm `43.2%`, net benefit `-106`

## Project Doc Hub

Use [docs/index.md](docs/index.md) as the main entry for:
- workflow rules
- plans and progress
- storyline and result summaries

## Active Focus

- Freeze strict-online selective-trigger protocol.
- Expand from pilot slices to broader BBQ English evaluation under the same protocol.
- Keep reporting centered on correction, harm, trigger rate, and net benefit.