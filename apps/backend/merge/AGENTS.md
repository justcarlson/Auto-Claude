# MERGE SYSTEM AGENTS.md

AI-powered intent-aware merge system for parallel agent work.

## OVERVIEW

Three-stage merge: Rule-based detection → Deterministic auto-merge → Minimal-context AI resolution.

## STRUCTURE

```
merge/
├── orchestrator.py        # Main coordinator
├── semantic_analyzer.py   # AST-based change classification (tree-sitter)
├── conflict_detector.py   # Rule-based overlap detection
├── compatibility_rules.py # ChangeType pair compatibility matrix
├── auto_merger.py         # Deterministic merge strategies
├── ai_resolver/           # LLM conflict resolution (last resort)
│   └── resolver.py
├── file_tracker.py        # FileEvolutionTracker
└── types.py               # ChangeType, ConflictSeverity enums
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add compatibility rule | `compatibility_rules.py` |
| Add change type | `types.py` + `semantic_analyzer.py` |
| Modify AI prompt | `ai_resolver/resolver.py` |
| Add merge strategy | `auto_merger.py` |

## MERGE PIPELINE

```
1. SemanticAnalyzer: Extract changes as ChangeType enums
   (ADD_HOOK_CALL, MODIFY_FUNCTION, ADD_IMPORT, etc.)

2. ConflictDetector: Check overlap against compatibility matrix
   - COMPATIBLE → AutoMerger
   - INCOMPATIBLE → AIResolver

3. AutoMerger strategies:
   - HOOKS_FIRST: React hooks at function top
   - COMBINE_IMPORTS: Deduplicate imports
   - HOOKS_THEN_WRAP: Hook + JSX provider pattern

4. AIResolver (if needed):
   - Sends only: conflict region + task intents + semantic descriptions
   - 4000 token limit → flags for human review if exceeded
```

## CONVENTIONS

- Semantic analysis uses tree-sitter (regex fallback)
- Changes associated with locations (`function:App`, `class:User`)
- Conflict severity: LOW → MEDIUM → HIGH → CRITICAL
- AI resolver batches multiple conflicts per file

## ANTI-PATTERNS

- **Never** send full files to AI (minimal context only)
- **Never** skip semantic analysis for text-only diff
