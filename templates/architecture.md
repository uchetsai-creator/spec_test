# System Architecture: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]` | **Date**: [DATE] | **Plan**: [link to plan.md]

**Input**: Feature specification from `spec.md`, technical context from `plan.md`

---

## 總覽

[簡短說明此功能的系統架構，涵蓋幾個主要元件、核心資料流向。2-4 句話。]

---

## 系統元件

<!--
  ACTION REQUIRED: 列出所有元件。
  類型（type）只能填：gateway / service / database / cache / queue / external
-->

| 元件 | 類型 | 職責 | 對外協定 |
|---|---|---|---|
| [元件名稱] | gateway | [職責描述] | HTTP |
| [元件名稱] | service | [職責描述] | REST |
| [元件名稱] | service | [職責描述] | REST |
| [元件名稱] | database | [職責描述] | TCP |
| [元件名稱] | cache | [職責描述] | TCP |
| [元件名稱] | queue | [職責描述] | AMQP |

---

## 資料流

<!--
  ACTION REQUIRED: 按順序描述主要請求路徑。
  每條描述格式：[來源] → [目的]：[發生了什麼]
-->

### 主要路徑（Happy Path）

1. [元件 A] → [元件 B]：[說明，如「Client 送下單請求，API Gateway 驗證 JWT」]
2. [元件 B] → [元件 C]：[說明]
3. [元件 C] → [元件 D]：[說明]

### 非同步路徑（如有）

1. [元件 A] → [Queue]：[發送什麼 Event]
2. [Queue] → [元件 B]：[訂閱什麼 Event，做什麼處理]

### 錯誤路徑（如有）

1. [說明錯誤情境] → [元件如何處理]

---

## 結構化定義（供 architecture_to_html.py 使用）

<!--
  ACTION REQUIRED: 依照以下格式填寫。
  此 YAML block 會被 scripts/python/architecture_to_html.py 直接讀取生成架構圖。

  type 允許值：gateway / service / database / cache / queue / external
  protocol 允許值：HTTP / REST / TCP / AMQP / GRPC / WS
  
  data_flows 的 from/to 必須與 components 的 name 完全一致。
-->

```yaml
components:
  - name: [元件名稱]
    type: gateway
    responsibilities:
      - [職責 1，如 routing]
      - [職責 2，如 jwt_validation]
      - [職責 3，如 rate_limiting]
    communicates_with:
      - [元件名稱]
      - [元件名稱]
    protocol: HTTP

  - name: [元件名稱]
    type: service
    responsibilities:
      - [職責 1]
      - [職責 2]
    communicates_with:
      - [元件名稱]
      - [元件名稱]
    protocol: REST

  - name: [元件名稱]
    type: database
    responsibilities:
      - persistent_storage
    communicates_with: []
    protocol: TCP

  - name: [元件名稱]
    type: cache
    responsibilities:
      - [職責 1，如 session]
      - [職責 2，如 rate_limit_counter]
    communicates_with: []
    protocol: TCP

  - name: [元件名稱]
    type: queue
    responsibilities:
      - async_event_bus
    communicates_with: []
    protocol: AMQP

data_flows:
  - from: [元件名稱]
    to: [元件名稱]
    trigger: [觸發條件，如 HTTP Request]
    protocol: HTTP

  - from: [元件名稱]
    to: [元件名稱]
    trigger: [觸發條件]
    protocol: REST

  - from: [元件名稱]
    to: [元件名稱]
    trigger: [Event 名稱]
    protocol: AMQP
```

---

## 部署環境

<!--
  ACTION REQUIRED: 說明各元件部署在哪裡。
  不適用的項目標記 N/A。
-->

| 元件 | 部署方式 | 環境 | 備註 |
|---|---|---|---|
| [元件名稱] | [Container / Serverless / Managed Service] | [Production / Staging] | [說明] |
| [元件名稱] | [e.g., AWS RDS / Supabase / 自建] | [Production / Staging] | [說明] |

---

## 未解決的問題

- [ ] [NEEDS CLARIFICATION] [問題描述，如「Message Queue 要用 RabbitMQ 還是 AWS SQS？」]
- [ ] [NEEDS CLARIFICATION] [問題描述]
