# Permissions: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]` | **Date**: [DATE] | **Plan**: [link to plan.md]

**Input**: Feature specification from `spec.md`, API contracts from `contracts/api-contract.md`

**存取控制模型**: [ ] RBAC（角色權限）/ [ ] ABAC（屬性權限）/ [ ] 混合

---

## 角色定義（Roles）

<!--
  ACTION REQUIRED: 列出系統中所有角色。
  每個角色說明它代表誰、有什麼限制。
-->

| 角色 ID | 角色名稱 | 說明 | 繼承自 |
|---|---|---|---|
| `ROLE_GUEST` | 訪客 | 未登入用戶，只能存取公開資源 | — |
| `ROLE_USER` | 一般用戶 | 已登入用戶，只能操作自己的資源 | `ROLE_GUEST` |
| `ROLE_ADMIN` | 管理員 | 可操作所有用戶的資源 | `ROLE_USER` |
| `[ROLE_ID]` | [名稱] | [說明] | [繼承自哪個角色，沒有則填 —] |

---

## 權限定義（Permissions）

<!--
  ACTION REQUIRED: 列出所有細粒度權限。
  命名規則：[resource]:[action]
  action 常見值：read / create / update / delete / manage（包含所有操作）
-->

| 權限 ID | 說明 |
|---|---|
| `[resource]:read` | 讀取 [資源名稱] |
| `[resource]:create` | 建立 [資源名稱] |
| `[resource]:update` | 更新 [資源名稱]（僅限自己的） |
| `[resource]:update:any` | 更新任何人的 [資源名稱] |
| `[resource]:delete` | 刪除 [資源名稱]（僅限自己的） |
| `[resource]:delete:any` | 刪除任何人的 [資源名稱] |
| `[resource]:manage` | 完整管理 [資源名稱]（含所有操作） |

---

## 角色權限矩陣（RBAC Matrix）

<!--
  ACTION REQUIRED: 每個角色對每個權限的存取狀況。
  ✅ = 允許
  ❌ = 拒絕
  🔶 = 條件允許（見下方備註）
-->

| 權限 | ROLE_GUEST | ROLE_USER | ROLE_ADMIN | [其他角色] |
|---|---|---|---|---|
| `[resource]:read` | ✅ | ✅ | ✅ | |
| `[resource]:create` | ❌ | ✅ | ✅ | |
| `[resource]:update` | ❌ | 🔶 | ✅ | |
| `[resource]:update:any` | ❌ | ❌ | ✅ | |
| `[resource]:delete` | ❌ | 🔶 | ✅ | |
| `[resource]:delete:any` | ❌ | ❌ | ✅ | |

**🔶 條件說明**:

- `[resource]:update` — `ROLE_USER` 只能更新 `owner_id = current_user.id` 的資源
- `[resource]:delete` — `ROLE_USER` 只能刪除 `owner_id = current_user.id` 的資源

---

## API Endpoint 權限對應

<!--
  ACTION REQUIRED: 每個 API endpoint 對應所需權限與角色。
  直接對應 contracts/api-contract.md 的 endpoint 清單。
-->

| Method | Path | 所需權限 | 最低角色 | 額外條件 |
|---|---|---|---|---|
| `POST` | `/[resource]` | `[resource]:create` | `ROLE_USER` | — |
| `GET` | `/[resource]` | `[resource]:read` | `ROLE_GUEST` | — |
| `GET` | `/[resource]/:id` | `[resource]:read` | `ROLE_GUEST` | — |
| `PATCH` | `/[resource]/:id` | `[resource]:update` | `ROLE_USER` | 僅限 `owner_id = current_user.id`，否則需要 `ROLE_ADMIN` |
| `DELETE` | `/[resource]/:id` | `[resource]:delete` | `ROLE_USER` | 僅限 `owner_id = current_user.id`，否則需要 `ROLE_ADMIN` |

---

## 資源所有權規則（Ownership Rules）

<!--
  ACTION REQUIRED: 說明哪些資源有「擁有者」概念，
  以及如何判斷當前用戶是否有權操作。
-->

| 資源 | 所有權欄位 | 判斷方式 | 說明 |
|---|---|---|---|
| `[resource]` | `owner_id` | `owner_id = current_user.id` | [說明] |
| `[resource]` | `created_by` | `created_by = current_user.id` | [說明] |
| `[resource]` | — | N/A（公開資源，無所有權概念） | [說明] |

---

## 權限執行層（Enforcement Layer）

<!--
  ACTION REQUIRED: 說明權限在哪一層執行，確保沒有漏洞。
-->

| 層級 | 執行方式 | 負責什麼 |
|---|---|---|
| **API Gateway** | JWT 驗證、角色解析 | 確認用戶已登入、解析 `role` claim |
| **Middleware** | 角色權限檢查 | 對照角色權限矩陣，拒絕無權限請求（回傳 403） |
| **Service Layer** | 所有權檢查 | 確認 `owner_id = current_user.id`，防止越權存取 |
| **Database** | Row-level Security（如適用） | [說明是否使用 RLS，如 PostgreSQL RLS] |

---

## 對應 Edge Cases

<!--
  確認 spec-template.md 的權限邊界 Edge Cases 都有設計依據。
  每條 EC 都應能在上方矩陣找到對應的設計。
-->

| Edge Case ID | 描述 | 對應設計 | 預期回應 |
|---|---|---|---|
| EC-020 | 未認證用戶存取受保護資源 | API Gateway JWT 驗證失敗 | `401 AUTH_TOKEN_MISSING` |
| EC-021 | `ROLE_USER` 執行僅限 `ROLE_ADMIN` 的操作 | Middleware 角色檢查 | `403 AUTH_PERMISSION_DENIED` |
| EC-022 | 用戶存取不屬於自己的資源 | Service Layer 所有權檢查 | `403 AUTH_RESOURCE_NOT_OWNED` |
| EC-023 | Token 已過期 | API Gateway JWT 驗證失敗 | `401 AUTH_TOKEN_EXPIRED` |
| [EC-ID] | [描述] | [對應哪層的設計] | [Error Code] |

---

## 未解決的問題

- [ ] [NEEDS CLARIFICATION] [問題描述，如「管理員是否能存取其他租戶的資料？」]
- [ ] [NEEDS CLARIFICATION] [問題描述]
