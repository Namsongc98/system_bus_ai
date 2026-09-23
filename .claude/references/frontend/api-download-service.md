# Download API Service Examples

Use this reference for export, report, PDF, Excel, image, or other Blob endpoints.

## Service Example

```js
import apiClient from '@/services/axios'

export const exportRevenueReport = async (params) => {
  const res = await apiClient.get('/reports/revenue', {
    params,
    responseType: 'blob',
  })

  const blob = new Blob([res.data])
  const url = window.URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = 'report.xlsx'
  link.click()

  window.URL.revokeObjectURL(url)
}
```

## Notes

- Use `responseType: 'blob'`.
- Keep UI feedback outside the service.
- Return nothing unless an existing caller expects the Blob or URL.
