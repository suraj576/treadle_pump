# Validation

This file records the two required local checks: the oracle solution scoring 1.000, and the no-op (NOP) baseline scoring 0.000.

Both were run from the repository root with:

```
harbor run -p tasks/multibody-dynamics -a oracle
harbor run -p tasks/multibody-dynamics -a nop
```

## Oracle run

```
  1/1 Mean: 1.000 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:04:15 0:00:00

adhoc • oracle
┏━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┓
┃ Trials ┃ Exceptions ┃  Mean ┃
┡━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━┩
│      1 │          0 │ 1.000 │
└────────┴────────────┴───────┘

┏━━━━━━━━┳━━━━━━━┓
┃ Reward ┃ Count ┃
┡━━━━━━━━╇━━━━━━━┩
│ 1.0    │     1 │
└────────┴───────┘

Job Info
Total runtime: 4m 15s
Results written to jobs/2026-08-08__09-49-53/result.json
Inspect results by running `harbor view jobs`
Share results by running `harbor upload jobs/2026-08-08__09-49-53`
```

Result: mean = 1.000

## NOP run

```
1/1 Mean: 0.000 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:18 0:00:00

adhoc • nop
┏━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┓
┃ Trials ┃ Exceptions ┃  Mean ┃
┡━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━┩
│      1 │          0 │ 0.000 │
└────────┴────────────┴───────┘

┏━━━━━━━━┳━━━━━━━┓
┃ Reward ┃ Count ┃
┡━━━━━━━━╇━━━━━━━┩
│ 0.0    │     1 │
└────────┴───────┘

Job Info
Total runtime: 18s
Results written to jobs/2026-08-08__11-40-43/result.json
Inspect results by running `harbor view jobs`
Share results by running `harbor upload jobs/2026-08-08__11-40-43`
```

Result: mean = 0.000
