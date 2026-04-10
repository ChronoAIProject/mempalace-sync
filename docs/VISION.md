# Vision

> *"我刚和 btw 聊了一下这个，但是不知道保存到哪里了."*
>
> — AlyciaBHZ, on the very thing this project is supposed to fix.

This document is the long-horizon vision for mempalace-sync. It is **not** a v0.2 spec. It is the answer to "what would make this matter beyond cross-machine sync?"

## The honest origin

The founder of this project just had a substantive conversation with another AI about how AI memory should evolve. **She does not know where that conversation was saved.** It might be in a Claude session, a ChatGPT thread, a Gemini chat, a Cursor sidebar, or nowhere. The thinking is lost until she stumbles across it again or rediscovers it from scratch.

If the founder of a memory tool can lose her own thinking about memory tools, the gap is real and the gap is everywhere. mempalace-sync v0.1 fixes the smallest version of this (sync the same files across machines). The vision is much bigger.

---

## Beyond sync: memory that evolves

v0.1 treats memory as **files to be backed up**. The vision is to treat memory as a **knowledge graph that grows continuously**, with three properties that today's AI memory systems do not have.

### 1. Continuous expansion

Today's AI memory is mostly write-once and read-as-search. Mining tools (MemPalace, claude-mem, Memory Bank, Mem0) capture things but rarely **promote** anything. Everything is equally weighted, semantic search picks the most similar slice, and the rest sits there forever as undifferentiated noise.

The vision is the opposite: memory should grow **monotonically with weighted importance**. Useful things should get more pull. Stale things should fade. Reused things should harden.

Concretely:

- Every memory gets a **usage score** — how often it gets retrieved, how often the agent acts on it, how often the user confirms it
- Memories that score above a threshold get **promoted** into a stable layer
- Promoted memories load with higher priority into agent context
- Memories that never get used drift to a cold tier (still searchable, not loaded by default)

This is the same shape as Karpathy's spaced repetition for human learning, applied to AI working memory. It is not novel as a concept. It is novel as a default in a memory system.

### 2. Core constraints — the Automath pattern

[Automath](https://github.com/the-omega-institute/automath) (Chrono's mathematical discovery engine) demonstrates a clean pattern: **verified theorems become axioms for new theorems**. The system grows knowledge by formal validation, and validated knowledge becomes the foundation for the next round.

mempalace-sync should adopt this pattern for AI memory:

- A memory can be tagged "validated" — by the user explicitly, by repeated agent use, or by being referenced by other validated memories
- Validated memories form a **core constraint layer**: they get loaded into every agent context as background truth, regardless of semantic relevance to the current query
- New raw memories cannot contradict the core layer without an explicit override step (where the user reviews and decides)
- Agents reading the memory bank know which pieces are "this is just something the user said once" vs. "this is verified core knowledge"

Concretely, the storage tiers would look like:

```
┌────────────────────────────────────┐
│  Tier 0: Identity                  │   "I am Lexa, founder of Dayou,
│  Hardcoded, never decays           │    Chrono researcher, ..."
└────────────────────────────────────┘
              ↑ promote
┌────────────────────────────────────┐
│  Tier 1: Core constraints          │   "Use Stripe over Alipay because
│  Validated, always loaded          │    Alipay rejects metaphysics"
└────────────────────────────────────┘
              ↑ promote
┌────────────────────────────────────┐
│  Tier 2: Working memory            │   "We're building knowledge module
│  Recently used, often loaded       │    for mysterious. Codex did
│                                    │    research."
└────────────────────────────────────┘
              ↑ promote
┌────────────────────────────────────┐
│  Tier 3: Cold archive              │   Everything ever captured.
│  Searchable, not auto-loaded       │   Searched only on demand.
└────────────────────────────────────┘
```

Promotion is not magic. It happens through explicit signals:

- User says "remember this" → instant promotion to Tier 1
- A memory gets retrieved 5+ times in 30 days → promotion to Tier 2
- A memory in Tier 2 gets retrieved 20+ times in 90 days → promotion to Tier 1
- User says "this isn't true anymore" → demotion or deletion
- A memory contradicts a Tier 1 entry → user is asked to resolve before write

### 3. Memory personas as colleagues

Today's AI memory is a single global context per user. The vision is to let one user have **multiple memory personas**, each addressed as if it were a different colleague.

The use case is real:

- "Designer-me" knows your taste preferences, color palettes, brand guidelines, design heroes
- "Engineer-me" knows your codebases, past architecture decisions, what you've ruled out and why
- "Founder-me" knows your customers, pricing experiments, team dynamics, runway state
- "Researcher-me" knows your reading list, papers you've ranked, open questions

Each persona has its own Tier 1 / Tier 2 / Tier 3 stack. They share Tier 0 (identity).

When you ask the agent a question, you can address it to a specific persona:

```
ask designer-me: "what palette did we land on for the social funnel?"
ask engineer-me: "why did we kill the websocket approach last quarter?"
ask founder-me: "what did Auric say about NyxID two days ago?"
```

The agent loads only that persona's tiers. The answers are tighter, less polluted by irrelevant context, and feel like consulting a focused colleague rather than a generic assistant.

This is conceptually similar to multi-character RAG (e.g., Character.AI's persona system) but inverted: the personas aren't fictional characters with invented backstories — they are **disciplined slices of your own real knowledge**, each addressable on demand.

---

## What this means for the roadmap

The vision is not v0.2. v0.2 is still NyxID + remote MCP server (per Auric). The vision lives in **v1.0+** and beyond.

| Version | Theme | What it adds |
|---------|-------|--------------|
| v0.1 | Git sync | Files travel between machines |
| v0.2 | NyxID gateway | Single host, real-time multi-device, no client install |
| v0.3 | Hybrid sync | Git fallback when host is offline |
| v0.4 | Team RBAC | Multiple humans, scoped access |
| **v1.0** | **Tiered memory** | Promotion logic, Tier 0/1/2/3 storage, user override flows |
| **v1.1** | **Personas** | Multiple memory namespaces addressable as roles |
| **v1.2** | **Validation loop** | Agent + user co-verify which memories are trustworthy |
| **v1.3** | **Cross-persona inference** | Agent can flag "founder-me said X but engineer-me said Y, you should reconcile" |

v0.1 ships today. v0.2 unblocks when NyxID integration is testable. The vision items are deliberately downstream — they require the infrastructure of v0.2 (single source of truth) to even make sense. You cannot have evolving tiered memory across 5 git copies that drift independently.

---

## Why this matters more than "sync"

If we only ship cross-machine file sync, we're a small utility. There are seven of us in this space already, the Anthropic team will eventually ship native sync, and we get absorbed.

If we ship **memory that evolves with use, hardens what's verified, and lets you address different facets of your own thinking as different colleagues**, we are building something none of those tools are building. We are also building something that actually solves the real problem AI memory has today — not "I lost my files" but "**I lost my thinking, and I don't even know where it went**".

The git sync is the first 5%. The vision is the rest.

---

## What we are NOT going to claim

To stay honest, none of this is in v0.1. v0.1 is `git push` and `git pull` wrapped in a CLI. Anyone reading this doc should walk away with:

1. **Today**, mempalace-sync is a sync tool. Use it for sync.
2. **Soon**, it will be a multi-machine memory server (Mode B / NyxID).
3. **Eventually**, it wants to be the substrate for evolving, validated, persona-aware memory.

We will not ship marketing copy that promises Tier 1 promotion logic before the code exists. We will not write blog posts that pretend personas are working before they are. The vision goes in this doc, where contributors and future self can find it. Production claims go in the README.

---

## Acknowledgments

- This vision was developed in a conversation between AlyciaBHZ and another AI tool. **The original conversation is lost.** This document is a reconstruction from memory of the key ideas: continuous expansion, core constraints (Automath pattern), and memory personas as colleagues.
- The Automath analogy is from the [the-omega-institute/automath](https://github.com/the-omega-institute/automath) project. Verified theorems → core constraints is a direct lift.
- Karpathy's spaced repetition writing inspired the promotion-by-usage model.
- [MemPalace](https://github.com/milla-jovovich/mempalace), [claude-mem](https://github.com/thedotmack/claude-mem), [Memory Bank](https://github.com/cline/memory-bank), and [Mem0](https://github.com/mem0ai/mem0) are the existing memory systems in 2026. None of them implement tiered promotion or addressable personas. That's the gap.
