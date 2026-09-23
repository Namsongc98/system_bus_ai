# JSON API Service Examples

Use these examples for normal JSON endpoints after reading [api-service-rules.md](../rules/api-service-rules.md).

## REST Naming

```js
getTickets(params)          // GET list
getTicketById(id)           // GET single
createTicket(data)          // POST
updateTicket(id, data)      // PUT / PATCH
deleteTicket(id)            // DELETE
```

## Request Shapes

```js
apiClient.get('/tickets', { params })
apiClient.get(`/tickets/${id}`)
apiClient.post('/tickets', data)
apiClient.put(`/tickets/${id}`, data)
apiClient.delete(`/tickets/${id}`)
```

## Service Example

```js
import apiClient from '@/services/axios'

export const getTickets = async (params) => {
  const res = await apiClient.get('/tickets', { params })
  return res.data
}

export const createTicket = async (data) => {
  const res = await apiClient.post('/tickets', data)
  return res.data
}
```
