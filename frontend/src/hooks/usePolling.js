import { useCallback, useEffect, useRef, useState } from "react";

/**
 * usePolling - fetches data immediately, then re-fetches on an interval.
 * Keeps `data` populated across refreshes (no flicker to null) and exposes
 * `loading` only for the very first fetch, plus a manual `refetch`.
 */
export function usePolling(fetchFn, { intervalMs = 8000, deps = [] } = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const result = await fetchFn();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    setLoading(true);
    load();
    if (intervalMs) {
      timerRef.current = setInterval(load, intervalMs);
    }
    return () => timerRef.current && clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load, intervalMs]);

  return { data, error, loading, refetch: load };
}
