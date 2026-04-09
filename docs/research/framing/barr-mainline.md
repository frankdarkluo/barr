# BARR Mainline Claim

## Related notes
- [Docs Index](../../index.md)
- [Current Pilot Scope](../../progress/current-pilot-scope.md)
- [EMNLP 2026 Storyline](emnlp-2026-storyline.md)
- [AWQ Age Selective Trigger Overview](../../experiments/results/age/awq-age-selective-trigger-overview.md)

## One-line thesis

Quantization amplifies fairness risk in reasoning models, and the key value of transition points is not a stronger redirect location but a detection signal for selective intervention.

## Current scientific focus

The pilot go/no-go question is:
Can Qwen3-8B transition-point internal states predict whether a BBQ ambiguous trajectory will end in a biased answer well enough to justify BARR?

## Core claim framing

The strongest paper framing is:
- Redirect is a high-impact but high-risk intervention.
- Blanket redirect fixes many biased cases but damages many already-correct unambiguous cases.
- BARR uses transition-time risk detection to decide whether to apply redirect.
- Therefore BARR can preserve most correction gains while sharply reducing collateral harm.

## Why this framing is stronger

It addresses the practical deployment question directly:
How do we correct biased trajectories without harming correct ones?

## Current evidence status

From held-out selective-trigger evaluation (strict-online protocol):
- text-level selective trigger remains strong on utility-harm tradeoff.
- It outperforms always-reflect on net benefit while keeping lower harm.
- This supports detection + selective intervention as the main method contribution.

## Protocol requirements for reviewer-safe claims

1. Trigger features must be online-available at intervention time.
2. Threshold selection must use train/dev only.
3. Final reporting must be held-out and sample-grouped.
4. End-to-end token accounting must be explicit.
5. Collateral harm on originally-correct disambiguated samples must be reported as a first-class metric.

## Immediate next priorities

1. Fix and freeze strict-online trigger protocol as default.
2. Keep same held-out comparison set for:
   - vanilla
   - blanket redirect
   - always-reflect
   - selective BARR
3. Expand from age slice to full BBQ English under the same protocol.
4. Replicate deployment story under quantized settings (AWQ-Int4 first).

## Success condition for the paper

BARR should approach redirect-level correction on risky samples, with harm closer to conservative baselines, and deliver better net utility under deployment constraints.
