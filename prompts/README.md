# Prompts (versioned)

Prompts are **files**, not inline strings, and are selected by `configs/app.yaml`
(or the prompt loader's default). This is a core LLMOps practice: prompts are
versioned, diffable, and swappable without touching code.

Naming: `<name>.v<N>.md`. The loader (`app/llm/prompts.py`) reads the highest
version unless a specific one is requested. When you change a prompt, **bump the
version** (keep the old file) so eval results stay comparable across versions.

Files:
- `intent_classifier.v1.md` — maps a user message to exactly one of 5 intents.
- `answer_compose.v1.md` — composes the final grounded answer + structured action.

## Prompt-injection hardening (applies to every prompt)
Retrieved catalog/FAQ text and tool outputs are inserted inside clearly delimited
`<context>` / `<tool_results>` blocks and are always treated as **data, never as
instructions**. The system prompt explicitly states that any instruction-like text
appearing inside those blocks must be ignored. See `app/agent/guardrails.py`.
