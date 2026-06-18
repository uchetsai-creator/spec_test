# Data Model: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]` | **Date**: [DATE] | **Plan**: [link to plan.md]

**Input**: Feature specification from `spec.md`, technical context from `plan.md`

---

## 總覽

[簡短說明此功能涉及哪些資料實體，以及它們之間的主要關係。2-4 句話。]

**Storage 技術**: [e.g., PostgreSQL 15 / MongoDB 7 / SQLite / Redis]

**ORM / Query Layer**: [e.g., Prisma / SQLAlchemy / GORM / 無]

---

## 實體定義（Entities）

<!--
  ACTION REQUIRED: 每個資料實體填寫一個區塊。
  欄位說明：
  - PK = Primary Key
  - FK = Foreign Key（標明參照哪個資料表）
  - INDEX = 建立索引
  - UNIQUE = 唯一約束
  - NOT NULL = 必填
  - DEFAULT = 預設值
  命名規則：資料表名用 snake_case 複數，欄位名用 snake_case。
-->

### [Entity 1 名稱] (`[table_name]`)

**用途**: [這個資料表代表什麼，存什麼資料]

| 欄位名 | 型別 | 約束 | 說明 |
|---|---|---|---|
| `id` | UUID / BIGSERIAL | PK, NOT NULL | 主鍵 |
| `[field_name]` | VARCHAR(255) | NOT NULL | [說明] |
| `[field_name]` | TEXT | | [說明，可為空] |
| `[field_name]` | INTEGER | NOT NULL, DEFAULT 0 | [說明] |
| `[field_name]` | BOOLEAN | NOT NULL, DEFAULT false | [說明] |
| `[fk_field]_id` | UUID | FK → `[other_table].id`, NOT NULL | [說明關聯] |
| `status` | ENUM | NOT NULL | 見下方狀態機 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 建立時間 |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 最後更新時間 |
| `deleted_at` | TIMESTAMPTZ | | Soft delete，NULL 表示未刪除 |

**索引**:

| 索引名 | 欄位 | 類型 | 用途 |
|---|---|---|---|
| `idx_[table]_[field]` | `[field_name]` | BTREE | [說明為何需要此索引，對應哪個查詢] |
| `idx_[table]_[field1]_[field2]` | `[field1], [field2]` | BTREE（複合） | [說明] |
| `idx_[table]_deleted_at` | `deleted_at` | BTREE（部分索引：WHERE deleted_at IS NULL） | 過濾軟刪除紀錄 |

**狀態機**（如有 status 欄位）:

```
[初始狀態] ──→ [狀態 A] ──→ [狀態 B] ──→ [終止狀態]
                    │
                    └──→ [狀態 C（異常路徑）]
```

| 狀態值 | 說明 | 可轉換到 |
|---|---|---|
| `draft` | [說明] | `active`, `cancelled` |
| `active` | [說明] | `completed`, `cancelled` |
| `completed` | [說明] | （終止，不可轉換） |
| `cancelled` | [說明] | （終止，不可轉換） |

---

### [Entity 2 名稱] (`[table_name]`)

**用途**: [說明]

| 欄位名 | 型別 | 約束 | 說明 |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | 主鍵 |
| `[fk_field]_id` | UUID | FK → `[other_table].id`, NOT NULL | [說明關聯] |
| `[field_name]` | VARCHAR(255) | NOT NULL | [說明] |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 建立時間 |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 最後更新時間 |

**索引**:

| 索引名 | 欄位 | 類型 | 用途 |
|---|---|---|---|
| `idx_[table]_[fk_field]_id` | `[fk_field]_id` | BTREE | 依外鍵查詢 |

---

[依需要新增更多實體區塊]

---

## Migration 計畫

<!--
  列出所有需要執行的 migration，並標明執行順序。
  對應 plan.md 的 Rollback Strategy 區塊。
-->

| 順序 | Migration 檔案名 | 操作類型 | 說明 | 可回滾 |
|---|---|---|---|---|
| 1 | `[timestamp]_create_[table]` | CREATE TABLE | 建立 [Entity 1] 資料表 | ✅ 是 |
| 2 | `[timestamp]_create_[table]` | CREATE TABLE | 建立 [Entity 2] 資料表 | ✅ 是 |
| 3 | `[timestamp]_add_index_[table]_[field]` | CREATE INDEX | 新增 [說明] 索引 | ✅ 是 |
| 4 | `[timestamp]_add_column_[col]_to_[table]` | ALTER TABLE | 新增欄位 [說明] | ✅ 是（欄位為空） |
| 5 | `[timestamp]_modify_[col]_in_[table]` | ALTER TABLE | 修改欄位 [說明] | ⚠️ 需確認資料 |

**執行前提**：[說明 migration 之間的依賴，如「Migration 2 必須在 Migration 1 之後執行」]

---

## 查詢模式（Query Patterns）

<!--
  列出此功能最常見的查詢，讓開發者知道索引設計的依據，
  也讓 AI 在實作時知道應該用哪種查詢方式。
-->

### 主要查詢

| 查詢 ID | 說明 | 條件 | 排序 | 對應索引 | 預期頻率 |
|---|---|---|---|---|---|
| QP-001 | [查詢描述，如「列出用戶所有訂單」] | `user_id = ?` AND `deleted_at IS NULL` | `created_at DESC` | `idx_orders_user_id` | 高（每頁載入） |
| QP-002 | [查詢描述] | `status = ?` | `updated_at DESC` | `idx_orders_status` | 中 |
| QP-003 | [查詢描述] | `id = ?` | — | PK | 高 |

### 寫入操作

| 操作 ID | 說明 | 涉及資料表 | 需要 Transaction | 備註 |
|---|---|---|---|---|
| WR-001 | [操作描述，如「建立訂單並扣庫存」] | `orders`, `inventory` | ✅ 是 | 需 atomic，失敗需全部 rollback |
| WR-002 | [操作描述] | `[table]` | ❌ 否 | [說明] |

---

## 資料保留與清理策略

<!--
  ACTION REQUIRED: 說明資料如何保留、清理、封存。
-->

| 資料表 | 保留策略 | 清理方式 | 清理頻率 | 備註 |
|---|---|---|---|---|
| `[table_name]` | Soft delete（`deleted_at` 標記） | [N] 天後硬刪除 / 永久保留 | [每日 / 每週 cron] | [說明] |
| `[table_name]` | 永久保留 | N/A | N/A | [說明為何需要永久保留] |
| `[table_name]` | 硬刪除 | 立即刪除 | 即時 | [說明] |

---

## 種子資料（Seed Data）

<!--
  如果功能需要初始資料（如預設角色、設定值、測試帳號），在此定義。
  不需要則標記 N/A。
-->

**是否需要種子資料**：[ ] 是 / [ ] 否（N/A）

```sql
-- [說明此種子資料的用途]
INSERT INTO [table_name] (id, [field], created_at)
VALUES
  ('[uuid]', '[value]', NOW()),
  ('[uuid]', '[value]', NOW());
```

---

## 未解決的問題

<!--
  填寫資料模型設計中仍有疑問或需要進一步討論的事項。
  解決後刪除對應條目。
-->

- [ ] [NEEDS CLARIFICATION] [問題描述，如「soft delete 的資料是否需要在 N 天後封存到 cold storage？」]
- [ ] [NEEDS CLARIFICATION] [問題描述]
