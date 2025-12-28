# Prime

Gather project context using the prime subagent for context-efficient exploration.

## Execute

Run the following command to gather project context:

```bash
jc prime --raw
```

The prime subagent will:
1. Explore the codebase structure using Haiku (fast and cheap)
2. Identify tech stack, entry points, and testing setup
3. Return a condensed ~500 word summary

This keeps file exploration out of your main context window.
