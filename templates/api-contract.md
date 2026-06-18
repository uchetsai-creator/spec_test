# API Contract: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]` | **Date**: [DATE] | **Plan**: [link to plan.md]

**Base URL**: `[e.g., /api/v1]`

**認證方式**: [e.g., Bearer Token (JWT) / API Key / Session Cookie / 無]

**Content-Type**: `application/json`

---

## 總覽

| Method | Path | 說明 | 認證 | 對應 User Story |
|---|---|---|---|---|
| `POST` | `/[resource]` | [說明] | ✅ 需要 | US1 |
| `GET` | `/[resource]` | [說明] | ✅ 需要 | US1 |
| `GET` | `/[resource]/:id` | [說明] | ✅ 需要 | US2 |
| `PATCH` | `/[resource]/:id` | [說明] | ✅ 需要 | US2 |
| `DELETE` | `/[resource]/:id` | [說明] | ✅ 需要 | US3 |

---

## Endpoints

<!--
  每個 endpoint 填寫一個區塊。
  格式固定，讓 AI 實作時有明確依據，
  也讓前端開發者直接對照使用。
-->

---

### `POST /[resource]`

**說明**: [這個 endpoint 做什麼]

**對應 User Story**: US[N]

**認證**: ✅ 需要 / ❌ 不需要

**Rate Limit**: [e.g., 10 次/分鐘 / 無]

#### Request

**Path Parameters**: 無

**Query Parameters**: 無

**Request Body**:

```json
{
  "[field_name]": "string",          // 必填，[說明，最大長度、格式等]
  "[field_name]": 0,                 // 必填，[說明，範圍]
  "[field_name]": "string",          // 選填，[說明，預設值]
  "[nested_object]": {
    "[field]": "string"              // 必填
  }
}
```

**欄位驗證規則**:

| 欄位 | 必填 | 型別 | 規則 | 錯誤碼（失敗時） |
|---|---|---|---|---|
| `[field_name]` | ✅ | string | 長度 1–255 | `VALIDATION_FIELD_REQUIRED` / `VALIDATION_FIELD_TOO_LONG` |
| `[field_name]` | ✅ | integer | 範圍 1–1000 | `VALIDATION_FIELD_OUT_OF_RANGE` |
| `[field_name]` | ❌ | string | 格式：email | `VALIDATION_FIELD_FORMAT` |

#### Response

**成功 `201 Created`**:

```json
{
  "id": "uuid",
  "[field_name]": "string",
  "[field_name]": 0,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**錯誤回應**:

| HTTP | Error Code | 發生情境 |
|---|---|---|
| `400` | `VALIDATION_FIELD_REQUIRED` | 必填欄位缺失 |
| `400` | `VALIDATION_FIELD_FORMAT` | 欄位格式錯誤 |
| `401` | `AUTH_TOKEN_MISSING` | 未帶 Authorization header |
| `401` | `AUTH_TOKEN_EXPIRED` | Token 已過期 |
| `409` | `[ENTITY]_ALREADY_EXISTS` | 重複建立 |
| `429` | `RATE_LIMIT_EXCEEDED` | 超過頻率限制 |

**錯誤回應格式**（所有錯誤統一格式）:

```json
{
  "error": {
    "code": "VALIDATION_FIELD_REQUIRED",
    "message": "Field [field_name] is required",
    "user_message": "[欄位名稱] 為必填",
    "details": {                        // 選填，提供額外除錯資訊
      "field": "[field_name]"
    }
  }
}
```

---

### `GET /[resource]`

**說明**: [列表查詢，說明過濾、排序、分頁]

**對應 User Story**: US[N]

**認證**: ✅ 需要 / ❌ 不需要

**Rate Limit**: 無

#### Request

**Path Parameters**: 無

**Query Parameters**:

| 參數 | 型別 | 必填 | 預設值 | 說明 |
|---|---|---|---|---|
| `page` | integer | ❌ | `1` | 頁碼，從 1 開始 |
| `per_page` | integer | ❌ | `20` | 每頁筆數，最大 `100` |
| `sort` | string | ❌ | `created_at` | 排序欄位，允許值：`created_at`, `updated_at`, `[field]` |
| `order` | string | ❌ | `desc` | 排序方向，允許值：`asc`, `desc` |
| `[filter_field]` | string | ❌ | — | 過濾條件，[說明] |
| `status` | string | ❌ | — | 過濾狀態，允許值：`draft`, `active`, `completed` |

**Request Body**: 無

#### Response

**成功 `200 OK`**:

```json
{
  "data": [
    {
      "id": "uuid",
      "[field_name]": "string",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**錯誤回應**:

| HTTP | Error Code | 發生情境 |
|---|---|---|
| `400` | `VALIDATION_FIELD_OUT_OF_RANGE` | `per_page` 超過最大值 100 |
| `400` | `VALIDATION_ENUM_INVALID` | `status` 傳入不合法的值 |
| `401` | `AUTH_TOKEN_EXPIRED` | Token 已過期 |

---

### `GET /[resource]/:id`

**說明**: [取得單一資源]

**對應 User Story**: US[N]

**認證**: ✅ 需要 / ❌ 不需要

#### Request

**Path Parameters**:

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | UUID | 資源 ID |

**Query Parameters**: 無

**Request Body**: 無

#### Response

**成功 `200 OK`**:

```json
{
  "id": "uuid",
  "[field_name]": "string",
  "[nested_object]": {
    "[field]": "string"
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**錯誤回應**:

| HTTP | Error Code | 發生情境 |
|---|---|---|
| `401` | `AUTH_TOKEN_EXPIRED` | Token 已過期 |
| `403` | `AUTH_RESOURCE_NOT_OWNED` | 存取不屬於自己的資源 |
| `404` | `[ENTITY]_NOT_FOUND` | ID 不存在 |

---

### `PATCH /[resource]/:id`

**說明**: [部分更新資源，只傳要修改的欄位]

**對應 User Story**: US[N]

**認證**: ✅ 需要

#### Request

**Path Parameters**:

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | UUID | 資源 ID |

**Request Body**（所有欄位皆為選填，至少傳一個）:

```json
{
  "[field_name]": "string",     // 選填，更新時驗證規則同 POST
  "[field_name]": 0             // 選填
}
```

**欄位驗證規則**: 同 POST，但所有欄位改為選填

#### Response

**成功 `200 OK`**: 回傳更新後的完整資源（格式同 `GET /:id`）

**錯誤回應**:

| HTTP | Error Code | 發生情境 |
|---|---|---|
| `400` | `VALIDATION_FIELD_FORMAT` | 欄位格式錯誤 |
| `401` | `AUTH_TOKEN_EXPIRED` | Token 已過期 |
| `403` | `AUTH_RESOURCE_NOT_OWNED` | 修改不屬於自己的資源 |
| `404` | `[ENTITY]_NOT_FOUND` | ID 不存在 |
| `409` | `[ENTITY]_STATE_INVALID` | 當前狀態不允許此操作 |
| `409` | `[ENTITY]_CONCURRENT_UPDATE` | 樂觀鎖衝突 |

---

### `DELETE /[resource]/:id`

**說明**: [刪除資源，soft delete 或 hard delete]

**刪除方式**: [ ] Soft delete（設定 `deleted_at`）/ [ ] Hard delete（永久刪除）

**對應 User Story**: US[N]

**認證**: ✅ 需要

#### Request

**Path Parameters**:

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | UUID | 資源 ID |

**Request Body**: 無

#### Response

**成功 `204 No Content`**: 無 body

**錯誤回應**:

| HTTP | Error Code | 發生情境 |
|---|---|---|
| `401` | `AUTH_TOKEN_EXPIRED` | Token 已過期 |
| `403` | `AUTH_RESOURCE_NOT_OWNED` | 刪除不屬於自己的資源 |
| `404` | `[ENTITY]_NOT_FOUND` | ID 不存在 |
| `409` | `[ENTITY]_STATE_INVALID` | 當前狀態不允許刪除（如進行中的訂單） |

---

## 共用規格

### 認證 Header

```
Authorization: Bearer <access_token>
```

### 分頁規格

所有列表 endpoint 統一使用 page-based 分頁（非 cursor-based），回傳格式如上方 `GET /[resource]` 範例。

### 時間格式

所有時間欄位統一使用 **ISO 8601 UTC**：`2025-01-01T00:00:00Z`

### Idempotency

需要 idempotency 的操作（如 `POST` 建立資源）可帶入：

```
Idempotency-Key: <client-generated-uuid>
```

伺服器端保留此 key [N] 分鐘，重複請求回傳相同結果。

---

## 未解決的問題

- [ ] [NEEDS CLARIFICATION] [問題描述，如「DELETE 是 soft 還是 hard？」]
- [ ] [NEEDS CLARIFICATION] [問題描述]
