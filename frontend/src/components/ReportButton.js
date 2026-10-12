import React, { useState, useEffect, useRef } from "react";
import { Download, Loader2, RefreshCw } from "lucide-react";
import { api, post, downloadFile } from "../lib/api";
import { toast } from "sonner";
export function ReportButton({
  id,
  compact = false,
  scoreVersion = "original",
}) {
  const [job, setJob] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const downloaded = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  useEffect(() => {
    if (!job || ["done", "failed"].includes(job.status)) return;
    const t = setInterval(
      () =>
        api("/jobs/" + job.id)
          .then(async (j) => {
            if (!mounted.current) return;
            setJob(j);
            if (j.status === "done" && !downloaded.current) {
              downloaded.current = true;
              await downloadFile(
                "/jobs/" + j.id + "/download",
                "Tejas-results-and-solutions.pdf",
              );
              setBusy(false);
            }
            if (j.status === "failed") {
              setError(j.error);
              setBusy(false);
            }
          })
          .catch((e) => {
            setError(e.message);
            setBusy(false);
          }),
      1600,
    );
    return () => clearInterval(t);
  }, [job]);
  async function start() {
    setBusy(true);
    setError("");
    downloaded.current = false;
    try {
      const j = await post("/attempts/" + id + "/report", {
        score_version: scoreVersion,
      });
      if (!mounted.current) return;
      setJob(j);
      if (j.status === "done") {
        await downloadFile(
          "/jobs/" + j.id + "/download",
          "Tejas-results-and-solutions.pdf",
        );
        downloaded.current = true;
        setBusy(false);
      }
    } catch (e) {
      setError(e.message);
      toast.error(e.message);
      setBusy(false);
    }
  }
  return (
    <div className="report-button-wrap">
      <button
        className={"btn " + (compact ? "btn-quiet" : "btn-primary")}
        data-testid="results-download-report-button"
        disabled={busy}
        onClick={start}
      >
        {busy ? (
          <Loader2 size={18} className="spin" />
        ) : error ? (
          <RefreshCw size={18} />
        ) : (
          <Download size={18} />
        )}{" "}
        {busy
          ? `Preparing report${job ? " · " + job.progress + "%" : ""}`
          : error
            ? "Retry PDF download"
            : compact
              ? "Download PDF"
              : "Download results & solutions PDF"}
      </button>
      {error && (
        <small className="error-text" role="alert">
          {error}
        </small>
      )}
      {busy && (
        <div
          className="report-progress"
          role="progressbar"
          aria-label="Report generation"
          aria-valuenow={job?.progress || 5}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span style={{ width: (job?.progress || 5) + "%" }} />
        </div>
      )}
    </div>
  );
}
