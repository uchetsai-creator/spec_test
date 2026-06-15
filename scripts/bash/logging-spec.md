# logging-spec.md

## Rules

- This file acts as the logging index and rule definition.
- Do not put module logging details in this file.
- Each module must have its own logging file named `log-<module-name>.md`.
- Each module logging file must follow the rules and format defined in this document.
- Direct print / console statements are NOT allowed. Always use the shared logger utility.

### Implementation Rules

- When implementing any module, automatically generate the matching `log-<module-name>.md` file.
- The log file must be generated before or alongside the implementation, not after.
- The log file must list every log point in the module in the order they are called.
- After implementation, if function names or file paths change, update the matching log file immediately.
- File paths must be relative to the project root.

---

## Logger Instantiation

Instantiate the logger at the top of each file using the module name:

```
logger = createLogger("MODULE")
```

---

## Log Output Destination

Logs must be written to both console and file simultaneously.

Each module writes to its own log file, named with the module name and the timestamp of when the session started:

```
logs/<module-name>_<YYYY-MM-DD_HH-mm-ss>.log
```

Examples:
```
logs/order_2026-06-12_10-23-01.log
logs/inventory_2026-06-12_10-23-01.log
logs/payment_2026-06-12_10-23-01.log
```

The timestamp is captured once at application startup and shared across all modules for that session, so all log files from the same run share the same timestamp.

The `logs/` directory must be created automatically at application startup if it does not exist.
Log files must be appended to within a session, never overwritten.
The shared logger utility is responsible for handling file writes — individual modules do not write to files directly.

---

## Log Output Format

```
[<ISO 8601 timestamp>] [<LEVEL>] [<MODULE>] <message>
  → <data as key=value or JSON if provided>
```

Example:

```
[2026-06-12T10:23:01.123Z] [INFO]  [ORDER]     建立訂單 — start
  → {"userId": "u_001", "itemCount": 3}

[2026-06-12T10:23:01.400Z] [INFO]  [INVENTORY] 扣除庫存 — start
  → {"productId": "p_099", "requested": 2}

[2026-06-12T10:23:01.456Z] [WARN]  [INVENTORY] 扣除庫存 — failed: 庫存不足
  → {"productId": "p_099", "current": 0, "requested": 2}

[2026-06-12T10:23:01.789Z] [ERROR] [PAYMENT]   金流 API 呼叫 — failed: Connection timeout
  → {"message": "Connection timeout", "stack": "..."}

[2026-06-12T10:23:01.800Z] [INFO]  [ORDER]     建立訂單 — end: success
  → {"orderId": "o_001", "userId": "u_001"}
```

---

## Message Format Rules

Every log message must follow this pattern:

```
<operation> — <state>
```

- `<operation>` is the action being performed (e.g. 建立訂單, 扣除庫存, 金流 API 呼叫)
- `<state>` describes where in the operation this log fires

| State | When to use |
|---|---|
| `start` | entering the function or operation |
| `end: success` | operation completed successfully |
| `end: <reason>` | operation completed with a non-error outcome (e.g. end: not found, end: skipped) |
| `failed: <reason>` | error or exception occurred |
| `warning: <reason>` | unexpected but non-fatal state |

This means every log line is self-describing. Reading the log alone tells you which module, which operation, and what happened at that point — without needing to read the source code.

---

## Module Naming Convention

Use a single short name in uppercase that matches the feature or layer.

```
ORDER          order management
INVENTORY      stock and inventory
PAYMENT        payment processing
AUTH           authentication and authorisation
USER           user management
DB             database transactions
HTTP           incoming requests and responses
QUEUE          message queue
CACHE          cache operations
CRON           scheduled jobs
STARTUP        application initialisation
```

Add new module names to this list as they are created.

---

## Log Levels

| Level | When to use |
|---|---|
| `info` | Normal flow — start, successful steps, end |
| `warn` | Unexpected but non-fatal — retry, fallback, rejected business rule |
| `error` | Failures that need attention — exceptions, rollbacks, external call errors |
| `debug` | Development only — gated by env flag, never on by default in production |

---

## Required Log Points

| Point | Level | Message pattern |
|---|---|---|
| Function entry | info | `<operation> — start` |
| Key decision (branch that changes outcome) | info / warn | `<operation> — warning: <reason>` |
| Before external call (DB, API, queue, cache) | info | `<operation> — start` |
| After external call (success) | info | `<operation> — end: success` |
| After external call (non-fatal failure) | warn | `<operation> — warning: <reason>` |
| Exception / error handler | error | `<operation> — failed: <reason>` |
| Function exit (success) | info | `<operation> — end: success` |
| Transaction start | info | `transaction — start` |
| Transaction commit | info | `transaction — end: success` |
| Transaction rollback | error | `transaction — failed: rollback` |
| Job start | info | `<job name> — start` |
| Job finish | info | `<job name> — end: success` |

---

## Data Field Rules

- Always include the IDs needed to trace this call across modules (e.g. userId, orderId, resourceId).
- NEVER log: passwords, tokens, API keys, credit card numbers, or any PII.
- `debug` level is for development only — never put critical information exclusively in debug logs.

---

## Module Log Files

| Module | Log File |
|---|---|
| _(add modules here as they are created)_ | |
