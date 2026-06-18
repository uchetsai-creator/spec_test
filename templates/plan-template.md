# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `__SPECKIT_COMMAND_PLAN__` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (__SPECKIT_COMMAND_PLAN__ command output)
├── research.md          # Phase 0 output (__SPECKIT_COMMAND_PLAN__ command)
├── data-model.md        # Phase 1 output (__SPECKIT_COMMAND_PLAN__ command)
├── quickstart.md        # Phase 1 output (__SPECKIT_COMMAND_PLAN__ command)
├── error-codes.md       # Phase 1 output — 所有錯誤碼定義（見下方）
├── rollback.md          # Phase 1 output — 部署與資料回滾策略（見下方）
├── contracts/           # Phase 1 output (__SPECKIT_COMMAND_PLAN__ command)
└── tasks.md             # Phase 2 output (__SPECKIT_COMMAND_TASKS__ command)
```

### Source Code (repository root)

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [Document the selected structure and reference the real directories]

---

## Error Code Catalogue

<!--
  ACTION REQUIRED: 定義此功能所有可能的錯誤碼。
  格式統一，讓前端、文件、監控系統都能對應。

  命名規則建議：[DOMAIN]_[ENTITY]_[REASON]
  HTTP 對應：讓每個 Error Code 明確對應 HTTP Status，避免歧義。
-->

### 錯誤碼格式

| 欄位 | 說明 |
|---|---|
| Code | 機器可讀的唯一代碼，全大寫底線分隔，如 `AUTH_TOKEN_EXPIRED` |
| HTTP Status | 對應的 HTTP 狀態碼 |
| Message | 給開發者看的英文說明（不對終端用戶顯示） |
| User Message | 給終端用戶看的說明（可本地化），若 N/A 表示不對外顯示 |
| Retryable | 用戶或系統是否可以重試（Y/N） |
| Category | `AUTH` / `VALIDATION` / `NOT_FOUND` / `CONFLICT` / `EXTERNAL` / `INTERNAL` |

### 認證與授權（AUTH）

| Code | HTTP | Message | User Message | Retryable | Category |
|---|---|---|---|---|---|
| `AUTH_TOKEN_MISSING` | 401 | Authorization header is missing | 請先登入 | N | AUTH |
| `AUTH_TOKEN_EXPIRED` | 401 | Access token has expired | 登入已過期，請重新登入 | N（需重新登入） | AUTH |
| `AUTH_TOKEN_INVALID` | 401 | Token signature verification failed | 認證失敗，請重新登入 | N | AUTH |
| `AUTH_PERMISSION_DENIED` | 403 | User lacks required permission: [permission] | 您沒有執行此操作的權限 | N | AUTH |
| `AUTH_RESOURCE_NOT_OWNED` | 403 | User does not own this resource | 您沒有存取此資源的權限 | N | AUTH |

### 輸入驗證（VALIDATION）

| Code | HTTP | Message | User Message | Retryable | Category |
|---|---|---|---|---|---|
| `VALIDATION_FIELD_REQUIRED` | 400 | Field [field_name] is required | [欄位名稱] 為必填 | Y（修正後重試） | VALIDATION |
| `VALIDATION_FIELD_FORMAT` | 400 | Field [field_name] has invalid format | [欄位名稱] 格式不正確 | Y | VALIDATION |
| `VALIDATION_FIELD_TOO_LONG` | 400 | Field [field_name] exceeds max length [N] | [欄位名稱] 不可超過 [N] 個字元 | Y | VALIDATION |
| `VALIDATION_FIELD_OUT_OF_RANGE` | 400 | Field [field_name] value [v] is out of range [min, max] | 數值超出允許範圍 | Y | VALIDATION |
| `VALIDATION_ENUM_INVALID` | 400 | Field [field_name] must be one of: [allowed_values] | 請選擇有效的選項 | Y | VALIDATION |

### 資源不存在（NOT_FOUND）

| Code | HTTP | Message | User Message | Retryable | Category |
|---|---|---|---|---|---|
| `[ENTITY]_NOT_FOUND` | 404 | [Entity] with id [id] not found | 找不到指定的 [資源名稱] | N | NOT_FOUND |
| `[ENTITY]_DELETED` | 410 | [Entity] has been permanently deleted | 此 [資源名稱] 已被刪除 | N | NOT_FOUND |

### 衝突與狀態（CONFLICT）

| Code | HTTP | Message | User Message | Retryable | Category |
|---|---|---|---|---|---|
| `[ENTITY]_ALREADY_EXISTS` | 409 | [Entity] with [field] [value] already exists | [資源名稱] 已存在 | N | CONFLICT |
| `[ENTITY]_STATE_INVALID` | 409 | Cannot perform [action] on [entity] in state [state] | 目前狀態無法執行此操作 | N（需確認狀態） | CONFLICT |
| `[ENTITY]_CONCURRENT_UPDATE` | 409 | Optimistic lock conflict: resource was modified by another request | 資料已被其他操作修改，請重新整理後再試 | Y | CONFLICT |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests. Retry after [N] seconds | 請求過於頻繁，請稍後再試 | Y（等待後重試） | CONFLICT |

### 外部依賴（EXTERNAL）

| Code | HTTP | Message | User Message | Retryable | Category |
|---|---|---|---|---|---|
| `EXTERNAL_[SERVICE]_TIMEOUT` | 504 | Upstream [service] did not respond within [N]ms | 服務暫時無法使用，請稍後再試 | Y | EXTERNAL |
| `EXTERNAL_[SERVICE]_UNAVAILABLE` | 503 | Upstream [service] returned [status] | 部分功能暫時無法使用 | Y | EXTERNAL |
| `EXTERNAL_[SERVICE]_BAD_RESPONSE` | 502 | Upstream [service] returned unexpected response format | 服務回應異常，請聯繫支援 | N | EXTERNAL |

### 系統內部（INTERNAL）

| Code | HTTP | Message | User Message | Retryable | Category |
|---|---|---|---|---|---|
| `INTERNAL_DATABASE_ERROR` | 500 | Database operation failed: [details] | 系統發生錯誤，請稍後再試 | Y | INTERNAL |
| `INTERNAL_UNEXPECTED` | 500 | An unexpected error occurred | 系統發生錯誤，請稍後再試 | Y | INTERNAL |

<!--
  INSTRUCTIONS FOR AI:
  1. 根據 spec.md 的功能範圍，新增或移除上表的列。
  2. [ENTITY] 請替換為實際的資源名稱（如 USER、ORDER、PRODUCT）。
  3. [SERVICE] 請替換為實際的外部服務名稱（如 STRIPE、SENDGRID、S3）。
  4. 所有 Code 必須在整個專案內唯一，不可重複。
  5. 確保每個 spec.md 裡的 Edge Case 都有對應的 Error Code。
-->

---

## Rollback Strategy

<!--
  ACTION REQUIRED: 定義每個部署階段的回滾策略。
  目標：讓任何人在發現問題時，都能在 30 分鐘內完成回滾，不需要臨場決策。
-->

### 部署分類

**此功能的部署類型**（選擇適用的）：

- [ ] Schema 變更（新增/修改/刪除資料表或欄位）
- [ ] 新增 API endpoint
- [ ] 修改既有 API（可能破壞向後相容）
- [ ] 新增背景工作（cron job / queue worker）
- [ ] 外部服務整合（新的第三方 API）
- [ ] 設定或環境變數變更
- [ ] Feature flag 控制的功能

---

### 資料庫回滾

<!--
  ACTION REQUIRED: 每個 migration 都必須有對應的 rollback 計畫。
-->

| Migration | 描述 | Rollback 指令 / 步驟 | 資料損失風險 |
|---|---|---|---|
| `[timestamp]_add_[table]` | [說明此 migration 做了什麼] | `[rollback 指令]` | 無（只刪空資料表） |
| `[timestamp]_add_column_[col]_to_[table]` | [說明] | `[rollback 指令]` | 無（欄位為空） |
| `[timestamp]_modify_[col]_in_[table]` | [說明] | ⚠️ 需手動確認，可能有資料損失 | 高（需先備份） |
| `[timestamp]_drop_[table]` | [說明] | ❌ 無法自動回滾，需從備份還原 | 極高 |

**不可逆 Migration 的處理原則**：
- 刪除欄位 / 資料表前，必須先確認程式碼已不使用該欄位至少一個 release 週期。
- 執行前必須做資料備份，並記錄備份位置：`[備份路徑或方式]`

---

### API 回滾

| 情境 | 回滾方式 | 預計時間 |
|---|---|---|
| 新 endpoint 出現 bug | 透過 feature flag 關閉，或 deploy 上一個 image tag | < 10 分鐘 |
| 既有 endpoint 改壞 | `[具體回滾指令，如 kubectl rollout undo / railway rollback]` | < 15 分鐘 |
| 破壞向後相容的變更 | 需同時 rollback client + server，見下方協調步驟 | < 30 分鐘 |

**破壞向後相容的協調步驟**（如適用）：
1. [步驟 1：先 rollback 哪一端]
2. [步驟 2：驗證方式]
3. [步驟 3：通知相關團隊]

---

### Feature Flag 策略

<!--
  如果此功能使用 feature flag，填寫以下內容；否則標記 N/A。
-->

**是否使用 Feature Flag**：[ ] 是 / [ ] 否

| Flag 名稱 | 預設值 | 控制範圍 | 緊急關閉方式 |
|---|---|---|---|
| `[flag_name]` | `false`（預設關閉，逐步開放） | [說明此 flag 控制哪些功能] | `[關閉指令或設定方式]` |

---

### 回滾決策標準

<!--
  明確定義什麼情況下應該觸發回滾，避免線上事故時猶豫不決。
-->

**自動觸發回滾**（符合任一條件即應立即回滾）：

- [ ] 錯誤率超過 **[N]%**（在 [時間窗口] 內）
- [ ] P95 回應時間超過 **[N] ms**（連續 [N] 分鐘）
- [ ] 關鍵功能（[列出哪些功能]）完全無法使用
- [ ] 資料庫連線錯誤率超過 **[N]%**

**需要評估再決定**：

- [ ] 個別非關鍵功能出現錯誤
- [ ] 效能下降但未超過閾值
- [ ] 單一用戶反映問題（可能是用戶端問題）

---

### 回滾執行清單

**執行順序**（發生需回滾的事件時，依序執行）：

1. **確認問題**：查看 [監控工具/Dashboard URL]，確認是此次部署引起
2. **通知**：通知 [誰] 開始回滾，預計影響範圍 [說明]
3. **備份資料**（如涉及不可逆 migration）：`[備份指令]`
4. **執行 app 回滾**：`[具體指令]`
5. **執行 migration 回滾**（如需要）：`[具體指令]`
6. **驗證**：執行 [quickstart.md 裡的驗證步驟] 確認系統恢復正常
7. **事後記錄**：在 [問題追蹤系統] 記錄回滾原因與影響

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
