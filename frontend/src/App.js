import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  LayoutDashboard,
  FolderSync,
  FileText,
  HelpCircle,
  ClipboardList,
  Download,
  ChevronRight,
  RefreshCw,
  Play,
  Lock,
  FileJson,
  AlertTriangle,
  Loader2,
  Flag,
  X,
  Zap,
  Eye,
  CheckCircle,
  XCircle,
  DownloadCloud,
  BarChart3
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/admin/jea`;

// Utility function for status badge
const StatusBadge = ({ status }) => {
  const statusClasses = {
    NEW: "status-new",
    DOWNLOADED: "status-downloaded",
    PARSED: "status-parsed",
    LOCKED: "status-locked",
    ERROR: "status-error",
    DRAFT: "status-new",
    APPROVED: "status-locked",
    SUCCESS: "status-locked",
    FAILED: "status-error",
    SKIPPED: "status-new",
    PENDING: "status-downloaded"
  };
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${statusClasses[status] || "status-new"}`}>
      {status}
    </span>
  );
};

// Subject Badge
const SubjectBadge = ({ subject }) => {
  const colors = {
    PHY: "bg-blue-900/50 text-blue-300 border-blue-700",
    CHEM: "bg-green-900/50 text-green-300 border-green-700",
    MATH: "bg-purple-900/50 text-purple-300 border-purple-700",
    UNKNOWN: "bg-red-900/50 text-red-300 border-red-700"
  };
  
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colors[subject] || colors.UNKNOWN}`}>
      {subject}
    </span>
  );
};

// Loading Spinner
const Spinner = ({ size = "md" }) => {
  const sizes = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-8 h-8" };
  return <Loader2 className={`${sizes[size]} animate-spin text-primary`} />;
};

// PDF Preview Modal
const PDFPreviewModal = ({ catalogId, year, paperNo, onClose }) => {
  const [pdfInfo, setPdfInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/catalog/${catalogId}/pdf-info`)
      .then(res => setPdfInfo(res.data))
      .catch(() => setPdfInfo({ has_pdf: false }))
      .finally(() => setLoading(false));
  }, [catalogId]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="pdf-preview-modal">
      <div className="bg-card rounded-xl border border-border w-full max-w-6xl h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h3 className="font-heading text-lg font-semibold">PDF Preview: {year} Paper {paperNo}</h3>
            {pdfInfo?.has_pdf && (
              <p className="text-xs text-muted-foreground mt-1">
                v{pdfInfo.file_version} | {pdfInfo.pages_count} pages | SHA256: {pdfInfo.sha256?.slice(0, 16)}...
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground" data-testid="close-preview">
            <X className="w-6 h-6" />
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          {pdfInfo?.has_pdf ? (
            <iframe
              src={`${API}/catalog/${catalogId}/preview-pdf`}
              className="w-full h-full"
              title="PDF Preview"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              No PDF available. Download the paper first.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Bulk Download Modal
const BulkDownloadModal = ({ onClose, onComplete }) => {
  const [status, setStatus] = useState("idle"); // idle, running, done
  const [result, setResult] = useState(null);

  const startBulkDownload = async () => {
    setStatus("running");
    try {
      const res = await axios.post(`${API}/bulk-download?force=false&max_concurrent=2`);
      setResult(res.data);
      setStatus("done");
      toast.success(`Bulk download complete: ${res.data.success} success, ${res.data.failed} failed`);
      onComplete();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Bulk download failed");
      setStatus("idle");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="bulk-download-modal">
      <div className="bg-card rounded-xl border border-border w-full max-w-2xl">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h3 className="font-heading text-lg font-semibold">Bulk Download All PDFs</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          {status === "idle" && (
            <div className="text-center space-y-4">
              <DownloadCloud className="w-12 h-12 text-primary mx-auto" />
              <p className="text-muted-foreground">Download all NEW catalogs (max 2 concurrent)</p>
              <button
                onClick={startBulkDownload}
                className="bg-primary text-primary-foreground px-6 py-2 rounded-lg font-medium hover:bg-primary/90"
                data-testid="start-bulk-download"
              >
                Start Bulk Download
              </button>
            </div>
          )}
          {status === "running" && (
            <div className="text-center space-y-4">
              <Spinner size="lg" />
              <p className="text-muted-foreground">Downloading PDFs... Please wait.</p>
            </div>
          )}
          {status === "done" && result && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-green-900/30 rounded-lg p-3">
                  <p className="text-2xl font-bold text-green-400">{result.success}</p>
                  <p className="text-xs text-green-400">Success</p>
                </div>
                <div className="bg-red-900/30 rounded-lg p-3">
                  <p className="text-2xl font-bold text-red-400">{result.failed}</p>
                  <p className="text-xs text-red-400">Failed</p>
                </div>
                <div className="bg-slate-800 rounded-lg p-3">
                  <p className="text-2xl font-bold text-slate-400">{result.skipped}</p>
                  <p className="text-xs text-slate-400">Skipped</p>
                </div>
              </div>
              <div className="max-h-64 overflow-auto rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead className="bg-secondary sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left">Paper</th>
                      <th className="px-3 py-2 text-left">Status</th>
                      <th className="px-3 py-2 text-left">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {result.items.map((item, i) => (
                      <tr key={i}>
                        <td className="px-3 py-2">{item.year} P{item.paper_no}</td>
                        <td className="px-3 py-2">
                          {item.status === "SUCCESS" && <CheckCircle className="w-4 h-4 text-green-400" />}
                          {item.status === "FAILED" && <XCircle className="w-4 h-4 text-red-400" />}
                          {item.status === "SKIPPED" && <span className="text-slate-400">-</span>}
                        </td>
                        <td className="px-3 py-2 text-xs text-muted-foreground truncate max-w-xs">
                          {item.sha256 ? `SHA: ${item.sha256.slice(0, 12)}...` : item.error || "Skipped"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <button
                onClick={onClose}
                className="w-full bg-secondary text-secondary-foreground py-2 rounded-lg font-medium hover:bg-secondary/80"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Subject Suggestions Modal
const SubjectSuggestionsModal = ({ catalogId, onClose, onApply }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState({});
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    axios.get(`${API}/catalog/${catalogId}/suggest-subjects`)
      .then(res => {
        setSuggestions(res.data.suggestions);
        // Pre-select high confidence suggestions
        const preSelected = {};
        res.data.suggestions.forEach(s => {
          if (s.confidence >= 0.5 && s.suggested_subject !== "UNKNOWN") {
            preSelected[s.question_id] = s.suggested_subject;
          }
        });
        setSelected(preSelected);
      })
      .catch(err => toast.error("Failed to get suggestions"))
      .finally(() => setLoading(false));
  }, [catalogId]);

  const handleApply = async () => {
    const toApply = Object.entries(selected).map(([question_id, subject]) => ({ question_id, subject }));
    if (toApply.length === 0) {
      toast.error("No suggestions selected");
      return;
    }
    setApplying(true);
    try {
      const res = await axios.post(`${API}/catalog/${catalogId}/apply-suggestions`, { suggestions: toApply });
      toast.success(`Applied ${res.data.applied} subject assignments`);
      onApply();
      onClose();
    } catch (err) {
      toast.error("Failed to apply suggestions");
    } finally {
      setApplying(false);
    }
  };

  const toggleSelect = (qId, subject) => {
    setSelected(prev => {
      if (prev[qId]) {
        const { [qId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [qId]: subject };
    });
  };

  const selectAll = () => {
    const all = {};
    suggestions.forEach(s => {
      if (s.suggested_subject !== "UNKNOWN") {
        all[s.question_id] = s.suggested_subject;
      }
    });
    setSelected(all);
  };

  const selectNone = () => setSelected({});

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="suggestions-modal">
      <div className="bg-card rounded-xl border border-border w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h3 className="font-heading text-lg font-semibold">Subject Suggestions (Assistive)</h3>
            <p className="text-xs text-muted-foreground">Review and select which suggestions to apply</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {loading ? (
          <div className="flex-1 flex items-center justify-center p-8"><Spinner size="lg" /></div>
        ) : (
          <>
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button onClick={selectAll} className="text-xs text-primary hover:underline">Select All Valid</button>
                <button onClick={selectNone} className="text-xs text-muted-foreground hover:underline">Clear Selection</button>
              </div>
              <span className="text-sm text-muted-foreground">{Object.keys(selected).length} selected</span>
            </div>
            
            <div className="flex-1 overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-secondary sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left w-10"></th>
                    <th className="px-3 py-2 text-left">Q#</th>
                    <th className="px-3 py-2 text-left">Suggested</th>
                    <th className="px-3 py-2 text-left">Confidence</th>
                    <th className="px-3 py-2 text-left">Keywords</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {suggestions.map(s => (
                    <tr 
                      key={s.question_id} 
                      className={`cursor-pointer transition-colors ${selected[s.question_id] ? "bg-primary/10" : "hover:bg-secondary/50"}`}
                      onClick={() => s.suggested_subject !== "UNKNOWN" && toggleSelect(s.question_id, s.suggested_subject)}
                    >
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={!!selected[s.question_id]}
                          onChange={() => {}}
                          disabled={s.suggested_subject === "UNKNOWN"}
                          className="rounded border-border"
                        />
                      </td>
                      <td className="px-3 py-2 font-mono">Q.{s.q_no}</td>
                      <td className="px-3 py-2"><SubjectBadge subject={s.suggested_subject} /></td>
                      <td className="px-3 py-2">
                        <span className={`${s.confidence >= 0.6 ? "text-green-400" : s.confidence >= 0.4 ? "text-yellow-400" : "text-red-400"}`}>
                          {Math.round(s.confidence * 100)}%
                        </span>
                      </td>
                      <td className="px-3 py-2 text-xs text-muted-foreground truncate max-w-xs">
                        {s.matched_keywords.slice(0, 5).join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div className="p-4 border-t border-border flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Only selected suggestions will be applied. UNKNOWN suggestions are not selectable.
              </p>
              <button
                onClick={handleApply}
                disabled={applying || Object.keys(selected).length === 0}
                className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50"
                data-testid="apply-suggestions-btn"
              >
                {applying ? <Spinner size="sm" /> : `Apply ${Object.keys(selected).length} Suggestions`}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// Sidebar Component
const Sidebar = () => {
  const navItems = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/catalog", icon: FolderSync, label: "Catalog" },
    { to: "/yearspec", icon: FileText, label: "YearSpec" },
    { to: "/questions", icon: HelpCircle, label: "Questions" },
    { to: "/baseline", icon: BarChart3, label: "Baseline" },
    { to: "/audit", icon: ClipboardList, label: "Audit Logs" }
  ];

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6 border-b border-border">
        <h1 className="font-heading text-xl font-bold text-foreground">JEA Paper Source</h1>
        <p className="text-xs text-muted-foreground mt-1">Admin Module v1.0</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary border-l-2 border-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-border">
        <p className="text-xs text-muted-foreground">2021-2025 English Papers</p>
        <p className="text-xs text-muted-foreground">Step-1: Paper Source Module</p>
      </div>
    </aside>
  );
};

// Dashboard Page
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/stats`)
      .then(res => setStats(res.data))
      .catch(() => toast.error("Failed to load stats"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-8 animate-fade-in" data-testid="dashboard">
      <div>
        <h2 className="font-heading text-3xl font-bold text-foreground">Dashboard</h2>
        <p className="text-muted-foreground mt-1">Overview of paper source module</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Catalogs" value={stats?.catalogs?.total || 0} icon={FolderSync} subtitle="Papers indexed" />
        <StatCard title="Questions" value={stats?.questions?.total || 0} icon={HelpCircle} subtitle={`${stats?.questions?.flagged || 0} flagged`} />
        <StatCard title="YearSpec Sections" value={stats?.yearspec_sections || 0} icon={FileText} subtitle="Section definitions" />
        <StatCard title="Unknown Subject" value={stats?.questions?.unknown_subject || 0} icon={AlertTriangle} subtitle="Need assignment" variant="warning" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="font-heading text-lg font-semibold mb-4">Catalog Status</h3>
          <div className="space-y-3">
            {["NEW", "DOWNLOADED", "PARSED", "LOCKED"].map(status => (
              <div key={status} className="flex items-center justify-between">
                <StatusBadge status={status} />
                <span className="text-foreground font-medium">{stats?.catalogs?.by_status?.[status] || 0}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="font-heading text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <NavLink to="/catalog" className="flex items-center justify-between p-3 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors group">
              <span className="text-sm font-medium">Manage Catalog</span>
              <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
            </NavLink>
            <NavLink to="/questions?subject=UNKNOWN" className="flex items-center justify-between p-3 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors group">
              <span className="text-sm font-medium">Review UNKNOWN Subjects</span>
              <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
            </NavLink>
          </div>
        </div>
      </div>
    </div>
  );
};

// Stat Card Component
const StatCard = ({ title, value, icon: Icon, subtitle, variant = "default" }) => (
  <div className={`rounded-xl border bg-card p-6 card-hover ${variant === "warning" ? "border-yellow-800" : "border-border"}`}>
    <div className="flex items-center justify-between">
      <Icon className={`w-5 h-5 ${variant === "warning" ? "text-yellow-400" : "text-muted-foreground"}`} />
    </div>
    <div className="mt-4">
      <p className="text-3xl font-bold text-foreground">{value}</p>
      <p className="text-sm font-medium text-foreground mt-1">{title}</p>
      <p className="text-xs text-muted-foreground">{subtitle}</p>
    </div>
  </div>
);

// Catalog Page
const CatalogPage = () => {
  const [catalogs, setCatalogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [previewCatalog, setPreviewCatalog] = useState(null);
  const [showBulkDownload, setShowBulkDownload] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(null);

  const fetchCatalogs = useCallback(() => {
    setLoading(true);
    axios.get(`${API}/catalog`)
      .then(res => setCatalogs(res.data))
      .catch(() => toast.error("Failed to load catalogs"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchCatalogs(); }, [fetchCatalogs]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await axios.post(`${API}/archive/sync?start_year=2021&end_year=2025&language=EN`);
      toast.success(`Synced: ${res.data.created} created, ${res.data.updated} updated`);
      fetchCatalogs();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleAction = async (catalogId, action) => {
    setActionLoading(prev => ({ ...prev, [`${catalogId}-${action}`]: true }));
    try {
      if (action === "download") {
        const res = await axios.post(`${API}/catalog/${catalogId}/download`);
        toast.success(`Downloaded: SHA256=${res.data.sha256.slice(0, 16)}..., ${res.data.pages_count} pages`);
      } else if (action === "parse") {
        const res = await axios.post(`${API}/catalog/${catalogId}/parse`);
        toast.success(`Parsed: ${res.data.questions} questions, ${res.data.yearspec_sections} sections`);
      } else if (action === "lock") {
        const res = await axios.post(`${API}/catalog/${catalogId}/lock`);
        if (res.data.locked) {
          toast.success("Catalog LOCKED successfully - ready for export");
        } else {
          toast.error(`Lock failed: ${res.data.reason}`);
        }
      } else if (action === "export") {
        const res = await axios.get(`${API}/catalog/${catalogId}/export`);
        // Export main payload
        const payloadBlob = new Blob([JSON.stringify(res.data.payload, null, 2)], { type: "application/json" });
        const payloadUrl = URL.createObjectURL(payloadBlob);
        const a = document.createElement("a");
        a.href = payloadUrl;
        a.download = `JEA_${res.data.payload.catalog.year}_P${res.data.payload.catalog.paper_no}_export.json`;
        a.click();
        toast.success("Export JSON downloaded");
      }
      fetchCatalogs();
    } catch (err) {
      toast.error(err.response?.data?.detail || `${action} failed`);
    } finally {
      setActionLoading(prev => ({ ...prev, [`${catalogId}-${action}`]: false }));
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="catalog-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-3xl font-bold text-foreground">Catalog</h2>
          <p className="text-muted-foreground mt-1">Manage paper sources (2021-2025 English)</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowBulkDownload(true)}
            className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-lg font-medium hover:bg-secondary/80 transition-colors"
            data-testid="bulk-download-btn"
          >
            <DownloadCloud className="w-4 h-4" />
            Bulk Download
          </button>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            data-testid="sync-button"
          >
            {syncing ? <Spinner size="sm" /> : <RefreshCw className="w-4 h-4" />}
            Sync Archive
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>
      ) : catalogs.length === 0 ? (
        <div className="text-center py-12 rounded-xl border border-border bg-card">
          <FolderSync className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No catalogs found. Click "Sync Archive" to fetch papers.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full" data-testid="catalog-table">
            <thead className="bg-secondary">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Year</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Paper</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {catalogs.map(cat => (
                <tr key={cat.id} className="table-row-hover" data-testid={`catalog-row-${cat.year}-${cat.paper_no}`}>
                  <td className="px-4 py-4 text-sm font-medium text-foreground">{cat.year}</td>
                  <td className="px-4 py-4 text-sm text-foreground">Paper {cat.paper_no} ({cat.language})</td>
                  <td className="px-4 py-4"><StatusBadge status={cat.status} /></td>
                  <td className="px-4 py-4">
                    <div className="flex items-center justify-end gap-2">
                      {/* Preview PDF - always available if downloaded */}
                      {cat.status !== "NEW" && (
                        <ActionButton
                          onClick={() => setPreviewCatalog(cat)}
                          icon={Eye}
                          label="Preview"
                          data-testid={`preview-btn-${cat.id}`}
                        />
                      )}
                      
                      {cat.status === "NEW" && (
                        <ActionButton
                          onClick={() => handleAction(cat.id, "download")}
                          loading={actionLoading[`${cat.id}-download`]}
                          icon={Download}
                          label="Download"
                          data-testid={`download-btn-${cat.id}`}
                        />
                      )}
                      {cat.status === "DOWNLOADED" && (
                        <ActionButton
                          onClick={() => handleAction(cat.id, "parse")}
                          loading={actionLoading[`${cat.id}-parse`]}
                          icon={Play}
                          label="Parse"
                          data-testid={`parse-btn-${cat.id}`}
                        />
                      )}
                      {cat.status === "PARSED" && (
                        <>
                          <ActionButton
                            onClick={() => setShowSuggestions(cat.id)}
                            icon={Zap}
                            label="Suggest"
                            variant="warning"
                            data-testid={`suggest-btn-${cat.id}`}
                          />
                          <ActionButton
                            onClick={() => handleAction(cat.id, "lock")}
                            loading={actionLoading[`${cat.id}-lock`]}
                            icon={Lock}
                            label="Lock"
                            variant="success"
                            data-testid={`lock-btn-${cat.id}`}
                          />
                        </>
                      )}
                      {cat.status === "LOCKED" && (
                        <ActionButton
                          onClick={() => handleAction(cat.id, "export")}
                          loading={actionLoading[`${cat.id}-export`]}
                          icon={FileJson}
                          label="Export"
                          variant="primary"
                          data-testid={`export-btn-${cat.id}`}
                        />
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      {previewCatalog && (
        <PDFPreviewModal
          catalogId={previewCatalog.id}
          year={previewCatalog.year}
          paperNo={previewCatalog.paper_no}
          onClose={() => setPreviewCatalog(null)}
        />
      )}
      {showBulkDownload && (
        <BulkDownloadModal
          onClose={() => setShowBulkDownload(false)}
          onComplete={fetchCatalogs}
        />
      )}
      {showSuggestions && (
        <SubjectSuggestionsModal
          catalogId={showSuggestions}
          onClose={() => setShowSuggestions(null)}
          onApply={fetchCatalogs}
        />
      )}
    </div>
  );
};

// Action Button Component
const ActionButton = ({ onClick, loading, icon: Icon, label, variant = "default", ...props }) => {
  const variants = {
    default: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    success: "bg-green-900/50 text-green-400 hover:bg-green-900/70",
    primary: "bg-primary/20 text-primary hover:bg-primary/30",
    warning: "bg-amber-900/50 text-amber-400 hover:bg-amber-900/70"
  };
  
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors disabled:opacity-50 ${variants[variant]}`}
      {...props}
    >
      {loading ? <Spinner size="sm" /> : <Icon className="w-3.5 h-3.5" />}
      {label}
    </button>
  );
};

// YearSpec Page
const YearSpecPage = () => {
  const [yearspecs, setYearspecs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSpec, setSelectedSpec] = useState(null);
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchYearspecs = useCallback(() => {
    setLoading(true);
    axios.get(`${API}/yearspec`)
      .then(res => setYearspecs(res.data))
      .catch(() => toast.error("Failed to load yearspec"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchYearspecs(); }, [fetchYearspecs]);

  const handleSave = async () => {
    if (!selectedSpec) return;
    setSaving(true);
    try {
      await axios.patch(`${API}/yearspec/${selectedSpec.id}`, editData);
      toast.success("Section updated");
      fetchYearspecs();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Update failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="yearspec-page">
      <div>
        <h2 className="font-heading text-3xl font-bold text-foreground">YearSpec Review</h2>
        <p className="text-muted-foreground mt-1">Section definitions with marking rules and evidence</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 rounded-xl border border-border overflow-hidden">
          <div className="bg-secondary px-4 py-3 border-b border-border">
            <h3 className="text-sm font-medium text-foreground">Sections ({yearspecs.length})</h3>
          </div>
          <div className="divide-y divide-border max-h-[600px] overflow-auto">
            {yearspecs.map(spec => (
              <button
                key={spec.id}
                onClick={() => {
                  setSelectedSpec(spec);
                  setEditData({ subject: spec.subject, question_type: spec.question_type });
                }}
                className={`w-full text-left p-4 transition-colors ${
                  selectedSpec?.id === spec.id ? "bg-primary/10" : "hover:bg-secondary"
                }`}
                data-testid={`yearspec-item-${spec.id}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">{spec.year} P{spec.paper_no} - {spec.section_code}</span>
                  <SubjectBadge subject={spec.subject} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">{spec.question_type} | Expected: {spec.q_count_expected || "?"} Q</p>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-7">
          {selectedSpec ? (
            <div className="rounded-xl border border-border bg-card p-6 space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-heading text-lg font-semibold">{selectedSpec.year} P{selectedSpec.paper_no} - {selectedSpec.section_code}</h3>
                <button onClick={() => setSelectedSpec(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">Subject *</label>
                  <select
                    value={editData.subject || ""}
                    onChange={e => setEditData(prev => ({ ...prev, subject: e.target.value }))}
                    className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm"
                    data-testid="yearspec-subject-select"
                  >
                    <option value="UNKNOWN">UNKNOWN</option>
                    <option value="PHY">Physics</option>
                    <option value="CHEM">Chemistry</option>
                    <option value="MATH">Mathematics</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">Question Type</label>
                  <select
                    value={editData.question_type || ""}
                    onChange={e => setEditData(prev => ({ ...prev, question_type: e.target.value }))}
                    className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm"
                    data-testid="yearspec-qtype-select"
                  >
                    <option value="SCQ">Single Correct (SCQ)</option>
                    <option value="MCQ_MULTI">Multiple Correct (MCQ)</option>
                    <option value="INTEGER">Numerical/Integer</option>
                    <option value="MATCH">Matching</option>
                    <option value="COMP_SET">Comprehension Set</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">Marking Rule (Evidence)</label>
                <pre className="evidence-text text-xs">{selectedSpec.marking_rule_json}</pre>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">Evidence Text (from PDF)</label>
                <div className="evidence-text whitespace-pre-wrap text-xs max-h-48">{selectedSpec.evidence_text}</div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                  data-testid="yearspec-save-btn"
                >
                  {saving ? <Spinner size="sm" /> : "Save Changes"}
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card p-12 text-center">
              <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Select a section to view and edit details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Questions Page
const QuestionsPage = () => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [editData, setEditData] = useState({});
  const [filters, setFilters] = useState({ year: "", subject: "", has_flags: false });
  const [saving, setSaving] = useState(false);

  const fetchQuestions = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filters.year) params.append("year", filters.year);
    if (filters.subject) params.append("subject", filters.subject);
    if (filters.has_flags) params.append("has_flags", "true");
    
    axios.get(`${API}/questions?${params}`)
      .then(res => setQuestions(res.data))
      .catch(() => toast.error("Failed to load questions"))
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => { fetchQuestions(); }, [fetchQuestions]);

  const handleSave = async () => {
    if (!selectedQuestion) return;
    setSaving(true);
    try {
      const payload = { ...editData };
      if (payload.options) {
        payload.options_json = JSON.stringify(payload.options);
        delete payload.options;
      }
      await axios.patch(`${API}/questions/${selectedQuestion.id}`, payload);
      toast.success("Question updated");
      fetchQuestions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const handleFlag = async (flagType) => {
    if (!selectedQuestion) return;
    try {
      await axios.post(`${API}/questions/${selectedQuestion.id}/flag`, { flag_type: flagType });
      toast.success(`Flag "${flagType}" added`);
      fetchQuestions();
    } catch (err) {
      toast.error("Failed to add flag");
    }
  };

  const detectSubject = async () => {
    if (!selectedQuestion) return;
    try {
      const res = await axios.post(`${API}/questions/${selectedQuestion.id}/detect-subject`);
      if (res.data.detected_subject !== "UNKNOWN") {
        setEditData(prev => ({ ...prev, subject: res.data.detected_subject }));
        toast.success(`Detected: ${res.data.detected_subject} (${Math.round(res.data.confidence * 100)}%)\nKeywords: ${res.data.matched_keywords.slice(0, 5).join(", ")}`);
      } else {
        toast.error("Could not detect subject with confidence");
      }
    } catch (err) {
      toast.error("Detection failed");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="questions-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-3xl font-bold text-foreground">Questions</h2>
          <p className="text-muted-foreground mt-1">Review and edit parsed questions ({questions.length} shown)</p>
        </div>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <select
          value={filters.year}
          onChange={e => setFilters(prev => ({ ...prev, year: e.target.value }))}
          className="bg-secondary border border-border rounded-md px-3 py-2 text-sm"
          data-testid="filter-year"
        >
          <option value="">All Years</option>
          {[2021, 2022, 2023, 2024, 2025].map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <select
          value={filters.subject}
          onChange={e => setFilters(prev => ({ ...prev, subject: e.target.value }))}
          className="bg-secondary border border-border rounded-md px-3 py-2 text-sm"
          data-testid="filter-subject"
        >
          <option value="">All Subjects</option>
          <option value="PHY">Physics</option>
          <option value="CHEM">Chemistry</option>
          <option value="MATH">Mathematics</option>
          <option value="UNKNOWN">UNKNOWN (Needs Review)</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={filters.has_flags}
            onChange={e => setFilters(prev => ({ ...prev, has_flags: e.target.checked }))}
            className="rounded border-border"
            data-testid="filter-flagged"
          />
          Flagged Only
        </label>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 rounded-xl border border-border overflow-hidden">
          <div className="bg-secondary px-4 py-3 border-b border-border">
            <h3 className="text-sm font-medium text-foreground">Questions</h3>
          </div>
          {loading ? (
            <div className="flex items-center justify-center h-64"><Spinner /></div>
          ) : questions.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">No questions found</div>
          ) : (
            <div className="divide-y divide-border max-h-[600px] overflow-auto">
              {questions.map(q => (
                <button
                  key={q.id}
                  onClick={() => {
                    setSelectedQuestion(q);
                    setEditData({
                      subject: q.subject,
                      q_type: q.q_type,
                      stem_text: q.stem_text,
                      status: q.status,
                      options: q.options_json ? JSON.parse(q.options_json) : {}
                    });
                  }}
                  className={`w-full text-left p-4 transition-colors ${
                    selectedQuestion?.id === q.id ? "bg-primary/10" : "hover:bg-secondary"
                  }`}
                  data-testid={`question-item-${q.id}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-foreground">Q.{q.q_no} - {q.year} P{q.paper_no}</span>
                    <SubjectBadge subject={q.subject} />
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">{q.stem_text?.slice(0, 100)}...</p>
                  {q.flags?.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      {q.flags.map((f, i) => (
                        <span key={i} className="text-xs bg-red-900/30 text-red-400 px-1.5 py-0.5 rounded">{f.type}</span>
                      ))}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-7">
          {selectedQuestion ? (
            <div className="rounded-xl border border-border bg-card p-6 space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-heading text-lg font-semibold">Q.{selectedQuestion.q_no} - {selectedQuestion.year} P{selectedQuestion.paper_no}</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleFlag("BROKEN_OCR")}
                    className="text-xs bg-secondary px-2 py-1 rounded hover:bg-secondary/80"
                    data-testid="flag-ocr-btn"
                  >
                    <Flag className="w-3 h-3 inline mr-1" />OCR Issue
                  </button>
                  <button onClick={() => setSelectedQuestion(null)} className="text-muted-foreground hover:text-foreground">
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">Subject *</label>
                  <div className="flex gap-2">
                    <select
                      value={editData.subject || ""}
                      onChange={e => setEditData(prev => ({ ...prev, subject: e.target.value }))}
                      className="flex-1 bg-secondary border border-border rounded-md px-3 py-2 text-sm"
                      data-testid="question-subject-select"
                    >
                      <option value="UNKNOWN">UNKNOWN</option>
                      <option value="PHY">Physics</option>
                      <option value="CHEM">Chemistry</option>
                      <option value="MATH">Mathematics</option>
                    </select>
                    <button
                      onClick={detectSubject}
                      className="bg-amber-900/50 text-amber-400 px-2 py-1 rounded hover:bg-amber-900/70"
                      title="Auto-detect subject"
                      data-testid="detect-subject-btn"
                    >
                      <Zap className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">Type</label>
                  <select
                    value={editData.q_type || ""}
                    onChange={e => setEditData(prev => ({ ...prev, q_type: e.target.value }))}
                    className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm"
                    data-testid="question-type-select"
                  >
                    <option value="SCQ">SCQ</option>
                    <option value="MCQ_MULTI">MCQ_MULTI</option>
                    <option value="INTEGER">INTEGER</option>
                    <option value="MATCH">MATCH</option>
                    <option value="COMP_SET">COMP_SET</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">Stem Text</label>
                <textarea
                  value={editData.stem_text || ""}
                  onChange={e => setEditData(prev => ({ ...prev, stem_text: e.target.value }))}
                  rows={6}
                  className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm font-mono"
                  data-testid="question-stem-input"
                />
              </div>

              {(editData.q_type === "SCQ" || editData.q_type === "MCQ_MULTI") && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">Options (A-D required for lock)</label>
                  <div className="space-y-2">
                    {["A", "B", "C", "D"].map(opt => (
                      <div key={opt} className="flex items-start gap-2">
                        <span className="text-sm font-medium text-muted-foreground w-6">({opt})</span>
                        <input
                          value={editData.options?.[opt] || ""}
                          onChange={e => setEditData(prev => ({
                            ...prev,
                            options: { ...prev.options, [opt]: e.target.value }
                          }))}
                          className="flex-1 bg-secondary border border-border rounded-md px-3 py-1.5 text-sm"
                          placeholder={`Option ${opt}`}
                          data-testid={`question-option-${opt}`}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                  data-testid="question-save-btn"
                >
                  {saving ? <Spinner size="sm" /> : "Save Changes"}
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card p-12 text-center">
              <HelpCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Select a question to view and edit details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Audit Logs Page
const AuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/audit-logs?limit=100`)
      .then(res => setLogs(res.data))
      .catch(() => toast.error("Failed to load audit logs"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="audit-page">
      <div>
        <h2 className="font-heading text-3xl font-bold text-foreground">Audit Logs</h2>
        <p className="text-muted-foreground mt-1">Track all changes and actions ({logs.length} entries)</p>
      </div>

      <div className="rounded-xl border border-border overflow-hidden">
        <table className="w-full" data-testid="audit-table">
          <thead className="bg-secondary">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Time</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Entity</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {logs.length === 0 ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">No audit logs yet</td></tr>
            ) : logs.map(log => (
              <tr key={log.id} className="table-row-hover">
                <td className="px-4 py-3 text-sm text-muted-foreground font-mono">
                  {new Date(log.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-foreground">{log.entity_type}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    log.action === "LOCK" ? "bg-green-900/50 text-green-400" :
                    log.action === "EDIT" ? "bg-blue-900/50 text-blue-400" :
                    log.action === "PARSE" ? "bg-yellow-900/50 text-yellow-400" :
                    log.action === "DOWNLOAD" || log.action === "BULK_DOWNLOAD" ? "bg-cyan-900/50 text-cyan-400" :
                    "bg-secondary text-secondary-foreground"
                  }`}>
                    {log.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground font-mono truncate max-w-xs">
                  {log.after_json ? log.after_json.slice(0, 50) + "..." : log.entity_id.slice(0, 20)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Main Layout
const Layout = ({ children }) => (
  <div className="min-h-screen bg-background">
    <Sidebar />
    <main className="ml-64 p-8">{children}</main>
  </div>
);

// App Component
function App() {
  return (
    <div className="dark">
      <Toaster 
        position="top-right" 
        toastOptions={{
          style: { background: "hsl(240 4% 10%)", color: "hsl(210 40% 98%)", border: "1px solid hsl(240 4% 16%)" }
        }}
      />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/yearspec" element={<YearSpecPage />} />
            <Route path="/questions" element={<QuestionsPage />} />
            <Route path="/audit" element={<AuditPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </div>
  );
}

export default App;
