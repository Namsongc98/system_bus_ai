# API Error Handling

`src/services/axios.js` currently unwraps backend errors before they reach stores, composables, or components.

## Backend Error Shape

```json
{
  "code": 400,
  "message": "Error message",
  "data": null
}
```

## Interceptor Behavior

The response interceptor rejects with:

```js
error.response?.data ?? error
```

For most API failures, callers receive the unwrapped backend object, not a raw Axios error.

## Caller Pattern

```js
catch (error) {
  const message = error?.message || 'Unexpected error'
  const code = error?.code || 500
}
```

Do not add `try/catch` inside normal service functions just to normalize errors. Let stores, composables, or pages handle user-facing feedback.
