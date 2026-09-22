import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Small data-fetching hook: { data, loading, error, reload }.
 * fetcher is a function returning an axios promise. Runs on mount and on
 * every change of the dependency array. Errors are surfaced to the caller
 * for clean rendering rather than thrown.
 */
export function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const runRef = useRef(null);

  useEffect(() => {
    let active = true;
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetcherRef.current();
        if (active) {
          setData(res.data);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Request failed");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };
    runRef.current = run;
    run();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  const reload = useCallback(() => {
    if (runRef.current) {
      runRef.current();
    }
  }, []);

  return { data, loading, error, reload };
}

export function getErrorMessage(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") {
    return detail;
  }
  const errors = err?.response?.data?.errors;
  if (Array.isArray(errors) && errors.length > 0) {
    const first = errors[0];
    const loc = (first.loc || []).slice(1).join(".");
    return first.msg ? (loc ? `${loc}: ${first.msg}` : first.msg) : undefined;
  }
  return err?.message || "Something went wrong";
}