# recon

Prototype auditor implementing the anchor architecture.

## Anchor Architecture

1. **Seed input**: Start from a single manifest listing N code files. For each listed file, call the agent with a fixed prefixed prompt template.
2. **Produce findings (no fluff)**: Treat each agent response as a finding (the claim, referenced files, and agent evidence). Persist each finding as a file under `findings/`.
3. **Orchestrate per finding**: Feed each stored finding to the Orchestrator. The finding contains the bug claim and the subset of related files that matter for the claim.
4. **Generate conditions from finding**: The Orchestrator deterministically derives a minimal set of conditions that must be true for the bug to be real or exploitable. Conditions are concrete, checkable assertions tied to the claim and the provided files.
5. **Evidence/task loop**: For each condition, the Orchestrator generates tasks for agents to fetch precise context (code slices, call graphs, configs, versions, sinks/sources, etc.). Agents run the tasks and return new context. Based on this context, the Orchestrator decides whether the condition is satisfied, failed, or still uncertain—creating narrower sub-conditions when necessary.
6. **Iterate until resolved**: Repeat the task/sub-condition cycle until each condition is decided or depth/resource limits are reached. Decisions rely solely on retrieved evidence; no random behavior or heuristic guessing.
7. **Outputs**: Persist updated finding artifacts (condition states, evidence trails) back into `findings/`. Results are production-grade objects and files only—no decorative fields or extraneous text.

## Random demo mode

Run with pseudo-random branching and live streaming:

```
python3 main.py --random --findings 3 --max-depth 3 --max-fanout 3 --seed 42
```
