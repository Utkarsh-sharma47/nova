import { useCallback, useEffect, useReducer, useRef } from 'react'

export type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }

type Action<T> =
  | { type: 'load' }
  | { type: 'success'; data: T }
  | { type: 'error'; error: Error }
  | { type: 'reset' }

function reducer<T>(_state: AsyncState<T>, action: Action<T>): AsyncState<T> {
  switch (action.type) {
    case 'load':
      return { status: 'loading' }
    case 'success':
      return { status: 'success', data: action.data }
    case 'error':
      return { status: 'error', error: action.error }
    case 'reset':
      return { status: 'idle' }
    default:
      return { status: 'idle' }
  }
}

export function useAsync<T>(
  asyncFn: () => Promise<T>,
  deps: unknown[],
  options: { enabled?: boolean } = {},
): AsyncState<T> & { reload: () => void } {
  const { enabled = true } = options
  const [state, dispatch] = useReducer(reducer<T>, { status: 'idle' })
  const requestId = useRef(0)

  const reload = useCallback(() => {
    if (!enabled) {
      return
    }
    const id = ++requestId.current
    dispatch({ type: 'load' })
    asyncFn()
      .then((data) => {
        if (id === requestId.current) {
          dispatch({ type: 'success', data })
        }
      })
      .catch((error: unknown) => {
        if (id === requestId.current) {
          dispatch({
            type: 'error',
            error: error instanceof Error ? error : new Error(String(error)),
          })
        }
      })
  }, [asyncFn, enabled])

  useEffect(() => {
    if (!enabled) {
      dispatch({ type: 'reset' })
      return
    }
    reload()
  }, [...deps, enabled, reload])

  return { ...state, reload }
}
