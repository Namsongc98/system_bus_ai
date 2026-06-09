# PINIA_STORE.md

---

## 1. Purpose

This document defines rules for generating Pinia stores that interact with API services. Pinia stores act as the **state management layer** between UI components and API services, ensuring a consistent flow of data and error handling throughout the application.

**Architecture Flow:**
`Component` → `Pinia Store` → `API Service` → `Backend API`

---

## 2. Store location

All stores must be created in:

    src/stores/

**Naming convention:**
The file should be named `<entity>.js` and the exported hook should follow the naming pattern:

    use<Entity>Store

**Examples:**
- `useAuthStore`
- `useTicketStore`
- `useTripStore`
- `useUserStore`

---

## 3. Store structure

Stores must use **Pinia Composition API syntax**. 

**Template:**

```javascript
import { defineStore } from "pinia"
import { ref, computed } from "vue"
import * as ticketService from "@/services/ticketService"

export const useTicketStore = defineStore("ticket", () => {
  // state
  const tickets = ref([])
  const loading = ref(false)
  const error = ref(null)

  // getters
  const ticketCount = computed(() => tickets.value.length)

  // actions
  const fetchTickets = async (params) => {
    loading.value = true
    error.value = null

    try {
      const data = await ticketService.getTickets(params)
      // Assuming Service returns res.data which contains the array or object
      tickets.value = data
      return data
    } catch (err) {
      error.value = err.message
      throw err // Rethrow so UI can handle notifications
    } finally {
      loading.value = false
    }
  }

  return {
    tickets,
    loading,
    error,
    ticketCount,
    fetchTickets
  }
})
```

---

## 4. State management rules

Each store should consistently define:
- **data**: The primary resource(s) (e.g., `items`, `user`, `tickets`).
- **loading**: Boolean ref to track pending API calls.
- **error**: Ref to store the latest error message.

**Example:**
```javascript
const items = ref([])
const loading = ref(false)
const error = ref(null)
```

---

## 5. Service usage

Stores must call services defined in `src/services/` (following [api-service-rules](rules/api-service-rules.md)).
**Stores must NOT call axios or apiClient directly.**

**Correct Example:**
```javascript
const data = await ticketService.getTickets()
```

---

## 6. Error handling

Backend error format:
```json
{
  "code": 400,
  "message": "Error message",
  "data": null
}
```

**Store responsibility:**
1. Catch errors thrown by services (which are already normalized by the service layer).
2. Store the `error.message` in the local `error` state.
3. Rethrow the error object so the UI layer can trigger toast notifications.

**Example:**
```javascript
catch (err) {
  error.value = err.message
  throw err
}
```

---

## 7. Nuxt UI integration

UI components (Pages/Components) are responsible for displaying errors using Nuxt UI `useToast`. **Pinia stores must NOT directly call UI functions or toast libraries.**

**Example in UI layer:**
```javascript
const toast = useToast()
const ticketStore = useTicketStore()

try {
  await ticketStore.fetchTickets()
} catch (error) {
  toast.add({
    title: "Error",
    description: error.message,
    color: "red"
  })
}
```

---

## 8. Store responsibilities

**Pinia store SHOULD:**
- Manage global/shared state.
- Call API services.
- Normalize or format data for the UI if necessary.
- Expose actions to components.

**Pinia store MUST NOT:**
- Manipulate the DOM.
- Render UI components.
- Call UI libraries/framework-specific UI functions directly (e.g., `toast`, `modal`).

---

## 9. Reusability and scalability

Stores must be designed for reuse across multiple pages. For instance, `useTripStore` might be utilized in:
- Trip selection pages.
- Driver dashboard.
- Admin management views.

---

## 10. Example conversion from API documentation

**`.codex/references/frontend/api-document.md`:**
`GET /tickets`

**Service (from API_SERVICE.md):**
```javascript
export const getTickets = async () => {
  try {
    const res = await apiClient.get("/tickets")
    return res.data
  } catch (error) {
    throw {
      code: error.response?.data?.code || 500,
      message: error.response?.data?.message || "Unexpected error"
    }
  }
}
```

**Pinia store action:**
```javascript
const fetchTickets = async () => {
  loading.value = true
  try {
    const data = await ticketService.getTickets()
    tickets.value = data
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    loading.value = false
  }
}
```

---

## 11. Reusable store patterns

Stores should support common patterns like:
- **CRUD operations**: `create`, `update`, `delete` actions.
- **Pagination**: Storing current page and page size.
- **Filtering**: Storing filter objects that sync with API params.

**Example:**
```javascript
const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0
})
```

---

## 12. Output rules

When generating Pinia stores:
1. Follow **API_SERVICE.md** naming and structure rules.
2. Use **Composition API** syntax (`ref`, `computed`, `defineStore`).
3. Keep stores modular and focused on a single entity.
4. Ensure all async actions follow the `try-catch-finally` pattern with loading/error state updates.
