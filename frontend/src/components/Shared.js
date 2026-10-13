import React, { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  ArrowRight,
  Menu,
  X,
  Loader2,
  BookOpen,
  LogOut,
  CheckCircle2,
  AlertCircle,
  ZoomIn,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import { API, post } from "../lib/api";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { toast } from "sonner";
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Skeleton } from './ui/skeleton';
import { ThemeToggle } from './ThemeToggle';
import { Sheet, SheetContent, SheetTitle, SheetDescription } from "./ui/sheet";
export const Logo = () => (
  <Link to="/" className="logo" data-testid="brand-home">
    <span className="logo-mark">
      <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <path
          d="M6 9h21M16 10v16M8 16h7M22 5l-4 5"
          stroke="currentColor"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
      </svg>
    </span>
    <span>
      tejas<span className="logo-sub">EXAM PLATFORM</span>
    </span>
  </Link>
);
export function Header() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const nav = useNavigate();
  useEffect(() => setOpen(false), [loc]);
  return (
    <header className="site-header">
      <div className="container header-inner">
        <Logo />
        <nav
          className="desktop-nav"
          aria-label="Main navigation"
          data-testid="site-header-nav"
        >
          {user && (
            <NavLink
              to={
                ["owner", "reviewer"].includes(user.role) ? "/studio" : "/home"
              }
              data-testid={
                ["owner", "reviewer"].includes(user.role)
                  ? "nav-studio"
                  : "nav-home"
              }
            >
              {["owner", "reviewer"].includes(user.role)
                ? "Content Studio"
                : "My practice"}
            </NavLink>
          )}
          <NavLink to="/competitions" data-testid="nav-competitions">Competitions</NavLink>
          <NavLink to="/exams" data-testid="nav-exams">
            Explore exams
          </NavLink>
          {!user && loc.pathname === "/" && (
            <a href="/#how-it-works" data-testid="nav-how">
              How it works
            </a>
          )}
        </nav>
        <div className="header-actions">
          <ThemeToggle />
          {user ? (
            <Button
              className="btn btn-quiet"
              data-testid="logout"
              onClick={async () => {
                try {
                  await logout();
                  nav("/");
                } catch (e) {
                  toast.error(e.message);
                }
              }}
            >
              <LogOut size={17} />
              <span>Sign out</span>
            </Button>
          ) : (
            <>
              <Link className="login-link" to="/login" data-testid="nav-login">
                Log in
              </Link>
              <Link
                className="btn btn-primary nav-start"
                to="/exams"
                data-testid="nav-start"
              >
                Start practicing <ArrowUpRight size={17} />
              </Link>
            </>
          )}
          <Button
            className="menu-button"
            aria-label={open ? "Close navigation" : "Open navigation"}
            aria-expanded={open}
            data-testid="mobile-menu"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </Button>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetContent className="mobile-sheet">
              <SheetTitle>Find your next step.</SheetTitle>
              <SheetDescription>Simple, focused navigation.</SheetDescription>
              <nav className="mobile-links" aria-label="Mobile navigation">
                {user && (
                  <NavLink data-testid="mobile-home" to="/home">
                    My practice
                  </NavLink>
                )}
                {["owner", "reviewer"].includes(user?.role) && (
                  <NavLink data-testid="mobile-studio" to="/studio">
                    Content Studio
                  </NavLink>
                )}
                <NavLink to="/competitions" data-testid="mobile-competitions">Competitions</NavLink>
                <NavLink to="/exams" data-testid="mobile-exams">
                  Explore exams
                </NavLink>
                {!user && (
                  <NavLink to="/login" data-testid="mobile-login">
                    Log in
                  </NavLink>
                )}
                <NavLink to="/accessibility" data-testid="mobile-accessibility">
                  Accessibility
                </NavLink>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
export const Footer = () => (
  <footer className="footer">
    <div className="container">
      <div className="footer-top">
        <div>
          <Logo />
          <p>
            A little more understanding.
            <br />A better way to practice.
          </p>
        </div>
        <div className="footer-links">
          <Link to="/exams" data-testid="footer-exams">
            Explore exams
          </Link>
          <Link to="/privacy" data-testid="footer-privacy">
            Privacy & content rights
          </Link>
          <Link to="/accessibility" data-testid="footer-accessibility">
            Accessibility
          </Link>
          <Link to="/studio" data-testid="footer-studio">
            Content Studio <ArrowUpRight size={14} />
          </Link>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} Tejas Exam Platform</span>
        <span>
          Independent practice. Not affiliated with NTA, JEE or BITS Pilani.
        </span>
      </div>
    </div>
  </footer>
);
export const Loading = ({ text = "Loading your workspace…" }) => (
  <div className="loading" role="status" data-testid="workspace-loading">
    <Loader2 className="spin" aria-hidden="true" />
    <span>{text}</span>
    <Skeleton className="loading-skeleton" />
  </div>
);
export const ErrorBox = ({ error, retry }) =>
  error ? (
    <div className="error-box" role="alert" data-testid="request-error">
      <AlertCircle size={19} />
      <div>
        {typeof error === "string" ? error : error.message}
        {retry && (
          <Button
            data-testid="retry-error"
            className="text-button"
            onClick={retry}
          >
            Try again <ArrowRight size={15} />
          </Button>
        )}
      </div>
    </div>
  ) : null;
export const Empty = ({ title, children, action }) => (
  <div className="empty-state">
    <span className="empty-icon">
      <BookOpen size={30} />
    </span>
    <h3>{title}</h3>
    <p>{children}</p>
    {action}
  </div>
);
export const Badge = ({ children, tone = "" }) => (
  <span className={"badge " + tone}>{children}</span>
);
export const PageTitle = ({ eyebrow, title, description, action }) => (
  <div className="page-title">
    <div>
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h1>{title}</h1>
      {description && <p>{description}</p>}
    </div>
    {action}
  </div>
);
export function Field({ label, id, children, hint, ...props }) {
  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      {children || <Input id={id} data-testid={id} {...props} />}{" "}
      {hint && <small>{hint}</small>}
    </label>
  );
}
export function SelectField({ label, value, onChange, options, id }) {
  return (
    <div className="field">
      <label id={id + "-label"}>{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger
          className="select-trigger"
          aria-labelledby={id + "-label"}
          data-testid={id}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem
              key={o.value || o}
              value={o.value || o}
              data-testid={id + "-" + (o.value || o)}
            >
              {o.label || o}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
export function Confirm({
  open,
  onClose,
  title,
  children,
  onConfirm,
  button = "Confirm",
  busy = false,
}) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="tejas-dialog">
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription asChild>
          <div className="dialog-description">{children}</div>
        </DialogDescription>
        <div className="button-row">
          <Button
            className="btn btn-secondary"
            data-testid="confirm-cancel"
            onClick={onClose}
          >
            Go back
          </Button>
          <Button
            className="btn btn-primary"
            data-testid="confirm-accept"
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? <Loader2 size={17} className="spin" /> : null}
            {button}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
export function SourceImage({ path, alt = "Source region", onError, onLoad }) {
  const [failed, setFailed] = useState(false);
  const [v, setV] = useState(0);
  const [zoom, setZoom] = useState(false);
  const [refreshed,setRefreshed]=useState(false);
  useEffect(()=>{setFailed(false);setRefreshed(false);setV(0);},[path]);
  return (
    <div className="source-image">
      {failed ? (
        <ErrorBox
          error="This source image did not load. Do not guess missing content."
          retry={() => {
            setFailed(false);
            setRefreshed(false);
            setV(v + 1);
          }}
        />
      ) : (
        <Button
          className="image-button"
          data-testid="source-image-zoom"
          aria-label="Enlarge source image"
          onClick={() => setZoom(true)}
        >
          <img
            src={API + path + (path.includes("?") ? "&" : "?") + "v=" + v}
            alt={alt}
            loading="lazy"
            onLoad={onLoad}
            onError={async () => {
              onError?.();
              if(!refreshed){setRefreshed(true);try{await post('/auth/refresh');setV(n=>n+1);return;}catch{}}
              setFailed(true);
            }}
          />
          <span>
            <ZoomIn size={14} /> Enlarge
          </span>
        </Button>
      )}
      <Dialog open={zoom} onOpenChange={setZoom}>
        <DialogContent className="image-dialog">
          <DialogTitle>Source detail</DialogTitle>
          <DialogDescription>
            Pinch or use your browser zoom to inspect the original notation.
          </DialogDescription>
          <div className="zoom-scroll">
            <img
              src={API + path + (path.includes("?") ? "&" : "?") + "v=" + v}
              alt={alt}
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
export const CheckLine = ({ children }) => (
  <span className="check-line">
    <CheckCircle2 size={16} />
    {children}
  </span>
);
