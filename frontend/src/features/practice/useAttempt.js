import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, post, put } from "../../lib/api";
export function useAttempt(id, user) {
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState(null);
  const [pending, setPending] = useState({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const [seconds, setSeconds] = useState(null);
  const [conflict, setConflict] = useState(false);
  const data = useRef(null),
    drafts = useRef({}),
    running = useRef(false),
    loading = useRef(false),
    anchor = useRef({ server: 0, mono: 0 }),
    timer = useRef(null),
    conflictRef = useRef(false);
  const storage = `tejas-draft-${user.id}-${id}`;
  const syncClock = (server) => {
    anchor.current = { server: server * 1000, mono: performance.now() };
  };
  const persist = useCallback(() => {
    setPending({ ...drafts.current });
    try {
      localStorage.setItem(storage, JSON.stringify(drafts.current));
    } catch {
      setError(
        "Browser storage is unavailable. Pending drafts cannot survive a refresh; stay connected.",
      );
    }
  }, [storage]);
  const openResult = useCallback(
    () =>
      navigate(
        "/results/" +
          id +
          (Object.keys(drafts.current).length ? "?late=true" : ""),
        { replace: true },
      ),
    [id, navigate],
  );
  const load = useCallback(async () => {
    if (loading.current) return;
    loading.current = true;
    try {
      const d = await api("/attempts/" + id);
      syncClock(d.server_now);
      data.current = d;
      setAttempt(d);
      let stored = {};
      try {
        stored = JSON.parse(localStorage.getItem(storage) || "{}");
      } catch {}
      for (const [qid, v] of Object.entries(stored)) {
        if (d.answers[qid]?.request_id === v.request_id) delete stored[qid];
      }
      drafts.current = stored;
      persist();
      setError("");
      if (d.status === "completed") openResult();
    } catch (e) {
      setError(e.message);
    } finally {
      loading.current = false;
    }
  }, [id, storage, persist, openResult]);
  useEffect(() => {
    load();
  }, [load]);
  const flush = useCallback(async () => {
    if (
      running.current ||
      !navigator.onLine ||
      !data.current ||
      conflictRef.current
    )
      return;
    running.current = true;
    setSaving(true);
    try {
      for (const qid of Object.keys(drafts.current)) {
        const draft = drafts.current[qid];
        if (!draft) continue;
        const q = data.current.questions.find((q) => q.id === qid);
        if (
          q?.type === "integer" &&
          draft.value.trim() &&
          !/^[+−-]?[0-9]{1,20}$/.test(draft.value.trim())
        ) {
          setError(
            "Enter an exact integer. Decimal values such as 3.0 and pasted letters are not accepted. Your draft has not been scored.",
          );
          continue;
        }
        try {
          const res = await put(`/attempts/${id}/answers/${qid}`, draft);
          data.current.answers[qid] = res.accepted;
          data.current.visited = [
            ...new Set([...(data.current.visited || []), qid]),
          ];
          setAttempt({ ...data.current, answers: { ...data.current.answers } });
          syncClock(res.server_now);
          if (drafts.current[qid]?.request_id === draft.request_id)
            delete drafts.current[qid];
          else if (drafts.current[qid])
            drafts.current[qid].revision = res.accepted.revision + 1;
          persist();
          setError("");
        } catch (e) {
          setError(e.message);
          if (e.status === 409) {
            const latest = await api("/attempts/" + id);
            if (latest.status === "completed") {
              openResult();
              return;
            }
            if (latest.answers[qid]?.request_id === draft.request_id) {
              data.current = latest;
              setAttempt(latest);
              if (drafts.current[qid]?.request_id === draft.request_id)
                delete drafts.current[qid];
              else if (drafts.current[qid])
                drafts.current[qid].revision = latest.answers[qid].revision + 1;
              persist();
            } else {
              conflictRef.current = true;
              setConflict(true);
            }
          }
          break;
        }
      }
    } finally {
      running.current = false;
      setSaving(false);
    }
  }, [id, persist, openResult]);
  useEffect(() => {
    const recover = async () => {
      if (!navigator.onLine) return;
      if (!data.current) await load();
      await flush();
    };
    const on = () => {
      setOnline(true);
      recover();
    };
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    const retry = setInterval(recover, 5000);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
      clearInterval(retry);
      clearTimeout(timer.current);
    };
  }, [flush, load]);
  useEffect(() => {
    if (!attempt?.deadline) return;
    let checking = false;
    const confirmDeadline = async () => {
      if (checking || !navigator.onLine) return;
      checking = true;
      try {
        const latest = await api("/attempts/" + id);
        syncClock(latest.server_now);
        if (latest.status === "completed") openResult();
      } catch (e) {
        setError(e.message);
      } finally {
        checking = false;
      }
    };
    const tick = () => {
      const serverNow =
        anchor.current.server + performance.now() - anchor.current.mono;
      const left = Math.max(
        0,
        Math.ceil((attempt.deadline * 1000 - serverNow) / 1000),
      );
      setSeconds(left);
      if (left === 0) confirmDeadline();
    };
    tick();
    const interval = setInterval(tick, 1000);
    const visible = () => {
      if (document.visibilityState === "visible") confirmDeadline();
    };
    document.addEventListener("visibilitychange", visible);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [attempt?.deadline, id, openResult]);
  useEffect(() => {
    const warn = (e) => {
      if (Object.keys(drafts.current).length) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, []);
  const edit = (qid, change) => {
    if (seconds === 0 || conflictRef.current) return;
    const old = drafts.current[qid] ||
      data.current.answers[qid] || { value: "", marked: false };
    drafts.current[qid] = {
      value: old.value,
      marked: old.marked,
      ...change,
      revision: (data.current.answers[qid]?.revision || 0) + 1,
      request_id: crypto.randomUUID(),
    };
    persist();
    clearTimeout(timer.current);
    timer.current = setTimeout(flush, 350);
  };
  const visit = useCallback(
    async (qid) => {
      if (
        !data.current ||
        data.current.status !== "active" ||
        data.current.visited?.includes(qid)
      )
        return;
      try {
        const r = await post(`/attempts/${id}/visit`, { question_id: qid });
        data.current.visited = r.visited;
        setAttempt({ ...data.current });
      } catch (e) {
        if (e.status === 409) load();
      }
    },
    [id, load],
  );
  const discard = () => {
    drafts.current = {};
    persist();
    conflictRef.current = false;
    setConflict(false);
    setError("");
    load();
  };
  const submit = async () => {
    setError("");
    await flush();
    if (running.current || Object.keys(drafts.current).length)
      throw new Error(
        "Wait for pending responses to be acknowledged before submitting.",
      );
    const receipt = await post("/attempts/" + id + "/submit");
    localStorage.removeItem(storage);
    navigate("/results/" + receipt.id);
  };
  return {
    attempt,
    pending,
    error,
    setError,
    saving,
    online,
    seconds,
    conflict,
    load,
    edit,
    visit,
    discard,
    submit,
  };
}
