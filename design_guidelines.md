{
  "design_system_name": "Tejas Exam Platform — Calm Premium (Blue/White) v2",
  "revision_scope": {
    "intent": "REVISION REQUEST ONLY — update design guidelines to fix navigation simplicity, studio cognitive load, and premium editorial feel. No code implementation.",
    "must_keep": [
      "Brand tokens: #2563EB (blue), #0B1F3A (navy), #F5F9FF (bg)",
      "No fake metrics/testimonials/endorsements",
      "Phone-first for Indian entrance students",
      "Shadcn/ui components (JS) as primary primitives",
      "No purple for AI/chat styling (not relevant here but keep rule)"
    ]
  },
  "brand_attributes": [
    "academically-credible",
    "calm-premium",
    "fast-to-navigate",
    "trust-first (no hype)",
    "editorial clarity"
  ],
  "information_architecture": {
    "global_principles": [
      "Navigation must be role-aware and capped: fewer top-level items, more contextual actions inside pages.",
      "Landing anchors must NOT appear inside app pages (avoid mixing marketing IA with product IA).",
      "Prefer 1 primary action per screen; secondary actions become ghost buttons or menu items.",
      "No horizontal overflow anywhere; all nav patterns must wrap/scroll safely (ScrollArea) on mobile."
    ],
    "nav_model": {
      "public": {
        "top_nav_items_max": 3,
        "items": [
          {
            "label": "Explore",
            "route": "/exams",
            "data_testid": "nav-public-explore-link"
          },
          {
            "label": "How it works",
            "route": "/#how-it-works",
            "data_testid": "nav-public-how-it-works-link",
            "note": "Landing-only anchor; hide when route != '/'."
          },
          {
            "label": "Sign in",
            "route": "/login",
            "data_testid": "nav-public-signin-link"
          }
        ],
        "primary_cta": {
          "label": "Start practicing",
          "route": "/exams",
          "data_testid": "nav-public-start-practicing-button"
        }
      },
      "student_authenticated": {
        "top_nav_items_max": 2,
        "items": [
          {
            "label": "My practice",
            "route": "/home",
            "data_testid": "nav-student-my-practice-link"
          },
          {
            "label": "Explore",
            "route": "/exams",
            "data_testid": "nav-student-explore-link"
          }
        ],
        "utility": [
          {
            "label": "Account",
            "route": "/account",
            "placement": "avatar-dropdown",
            "data_testid": "nav-student-account-link"
          },
          {
            "label": "Sign out",
            "action": "logout",
            "placement": "avatar-dropdown",
            "data_testid": "nav-student-signout-button"
          }
        ]
      },
      "reviewer_staff": {
        "top_nav_items_max": 2,
        "items": [
          {
            "label": "Studio",
            "route": "/studio",
            "data_testid": "nav-staff-studio-link"
          },
          {
            "label": "Explore",
            "route": "/exams",
            "data_testid": "nav-staff-explore-link"
          }
        ],
        "studio_secondary": {
          "pattern": "inside-studio sidebar/tabs, not global nav",
          "items": [
            "Uploads",
            "Review",
            "Publish",
            "Settings",
            "Audit"
          ]
        }
      }
    },
    "studio_organization": {
      "goal": "Reduce cognitive load: make Studio a guided pipeline, not a dashboard of everything.",
      "primary_flow": [
        {
          "step": "Upload",
          "description": "Add PDFs + rights confirmation. Show processing status and failures.",
          "ui_pattern": "Stepper + Card sections",
          "data_testid": "studio-step-upload"
        },
        {
          "step": "Review",
          "description": "Resolve extraction, verify Q↔Solution pairing, fix math/diagrams, confirm answers.",
          "ui_pattern": "Two-pane review (question left, solution right) + source preview drawer",
          "data_testid": "studio-step-review"
        },
        {
          "step": "Publish",
          "description": "Preflight checklist (rights, pairing 100%, rules set) then publish/withdraw.",
          "ui_pattern": "Checklist + destructive confirmation dialog",
          "data_testid": "studio-step-publish"
        }
      ],
      "secondary_areas": [
        {
          "name": "Settings",
          "description": "Exam metadata, marking rules presets, permissions.",
          "placement": "secondary tab or dropdown",
          "data_testid": "studio-settings-tab"
        },
        {
          "name": "Audit",
          "description": "Immutable log of actions (upload/edit/publish/withdraw/report generation).",
          "placement": "secondary tab",
          "data_testid": "studio-audit-tab"
        }
      ],
      "no_horizontal_overflow_rules": [
        "Use `ScrollArea` for long tables/lists on mobile.",
        "Use `Tabs` with `overflow-x-auto` only for <=3 tabs; otherwise use `Select` or `DropdownMenu` for section switching.",
        "All chips/badges wrap: `flex flex-wrap gap-2`.",
        "Never use fixed-width columns on mobile; use stacked rows with `Separator`."
      ]
    }
  },
  "typography": {
    "font_pairing": {
      "headings": {
        "family": "Manrope",
        "fallback": "system-ui, -apple-system, Segoe UI, Roboto",
        "usage": "H1–H4, nav labels, card titles"
      },
      "body": {
        "family": "Public Sans",
        "fallback": "system-ui, -apple-system, Segoe UI, Roboto",
        "usage": "paragraphs, helper text, forms"
      },
      "mono": {
        "family": "JetBrains Mono",
        "usage": "IDs, version tags, audit entries"
      }
    },
    "scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight",
      "h2": "text-base md:text-lg font-semibold text-muted-foreground",
      "section_title": "text-xl sm:text-2xl font-bold tracking-tight",
      "card_title": "text-base font-semibold",
      "body": "text-sm sm:text-base leading-relaxed",
      "small": "text-xs text-muted-foreground"
    },
    "editorial_rules": [
      "Max line length for reading blocks: `max-w-prose`.",
      "Use 2–3x more whitespace than default: section padding `py-12 sm:py-16`.",
      "Prefer sentence case; avoid ALL CAPS except tiny labels."
    ]
  },
  "color_system": {
    "tokens_css_custom_properties": {
      "note": "Keep existing HSL tokens in index.css but add semantic aliases for clarity in components.",
      "add_to_:root": {
        "--brand-blue": "#2563EB",
        "--brand-navy": "#0B1F3A",
        "--page-bg": "#F5F9FF",
        "--text": "#14243A",
        "--muted-text": "#52637A",
        "--border-soft": "#D7E2F0",
        "--focus": "#1D4ED8",
        "--success": "#16A34A",
        "--warning": "#F59E0B",
        "--danger": "#DC2626"
      }
    },
    "usage": {
      "background": "page uses --page-bg; cards are white; avoid tinted card backgrounds except subtle `secondary`.",
      "primary_actions": "solid brand blue background with white text; hover darken slightly.",
      "borders": "use --border-soft; avoid heavy outlines.",
      "focus": "2px ring using --focus; always visible."
    },
    "gradients": {
      "allowed": [
        {
          "name": "hero-wash",
          "css": "radial-gradient(900px circle at 20% 10%, rgba(37,99,235,0.10), transparent 55%), radial-gradient(700px circle at 85% 20%, rgba(11,31,58,0.08), transparent 60%)",
          "rule": "Decorative only; keep under 20% perceived intensity; never behind dense text blocks."
        }
      ],
      "prohibited": [
        "blue-500 to purple-600",
        "purple-500 to pink-500",
        "green-500 to blue-500",
        "red to pink"
      ]
    }
  },
  "layout_and_grid": {
    "container": {
      "max_width": "max-w-6xl",
      "padding": "px-4 sm:px-6 lg:px-8",
      "rule": "Never center-align all text globally; align left by default."
    },
    "landing_layout": {
      "pattern": "Editorial + Bento",
      "sections": [
        "Hero (value prop + 2 CTAs)",
        "Exam cards (JEE Main, BITSAT) with honest availability",
        "How it works (4-step learning loop)",
        "Trust & accessibility (no hype)",
        "FAQ",
        "Footer"
      ],
      "hero_composition": [
        "Left: headline + subhead + CTAs",
        "Right: single calm illustration/photo in rounded card (no fake dashboards)",
        "Below: 3 proof points as plain text bullets (not metrics)"
      ]
    },
    "app_shell": {
      "header": "sticky top-0 with subtle border + blur; contains role-aware nav",
      "page_header": "each page has its own title + contextual actions; do not overload global nav",
      "mobile": "use Sheet for menu; keep 44px min tap targets"
    }
  },
  "components": {
    "component_path": {
      "shadcn_primary": [
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/navigation-menu.jsx",
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/dropdown-menu.jsx",
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/breadcrumb.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/table.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/alert-dialog.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx",
        "/app/frontend/src/components/ui/sonner.jsx"
      ]
    },
    "nav_components": {
      "desktop": {
        "use": "navigation-menu + dropdown-menu",
        "pattern": "2-3 links + 1 primary CTA + avatar dropdown",
        "classes": {
          "header": "sticky top-0 z-50 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60 border-b border-[color:var(--border-soft)]",
          "inner": "mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-3",
          "brand": "flex items-center gap-2 font-semibold text-[color:var(--brand-navy)]",
          "nav_links": "hidden md:flex items-center gap-1",
          "cta": "hidden md:inline-flex"
        }
      },
      "mobile": {
        "use": "sheet",
        "pattern": "Hamburger opens vertical list; primary CTA pinned at bottom",
        "classes": {
          "trigger": "md:hidden",
          "sheet_content": "w-[320px] sm:w-[360px]",
          "link": "w-full justify-start",
          "bottom_cta_wrap": "mt-6 pt-4 border-t border-[color:var(--border-soft)]"
        }
      }
    },
    "studio_components": {
      "pipeline_header": {
        "use": "tabs OR segmented buttons (toggle-group)",
        "rule": "Max 3 primary steps visible: Upload / Review / Publish. Settings & Audit go into DropdownMenu labeled 'More'."
      },
      "review_layout": {
        "pattern": "Two-pane on desktop, stacked on mobile",
        "desktop_grid": "lg:grid lg:grid-cols-2 lg:gap-6",
        "mobile_stack": "grid grid-cols-1 gap-4",
        "source_preview": "Drawer for mobile, Dialog for desktop"
      },
      "tables": {
        "rule": "On mobile, replace wide tables with Card rows; on desktop use Table + sticky header."
      }
    },
    "buttons": {
      "style": "Professional / Corporate",
      "tokens": {
        "radius": "rounded-xl (matches --radius .875rem)",
        "primary": "bg-[color:var(--brand-blue)] text-white hover:bg-[#1D4ED8]",
        "secondary": "bg-white border border-[color:var(--border-soft)] text-[color:var(--text)] hover:bg-[hsl(var(--secondary))]",
        "ghost": "hover:bg-[hsl(var(--secondary))] text-[color:var(--text)]"
      },
      "motion": "hover: translateY(-1px) on primary only; active: scale-[0.98]; focus-visible ring"
    },
    "status_badges": {
      "use": "badge",
      "variants": {
        "published": "bg-green-50 text-green-700 border-green-200",
        "draft": "bg-slate-50 text-slate-700 border-slate-200",
        "needs_review": "bg-amber-50 text-amber-800 border-amber-200",
        "blocked": "bg-red-50 text-red-700 border-red-200"
      },
      "rule": "Always pair color with label text/icon; never color-only meaning."
    }
  },
  "motion_and_microinteractions": {
    "principles": [
      "Motion should reduce anxiety: quick, subtle, and purposeful.",
      "Respect prefers-reduced-motion; disable non-essential animations."
    ],
    "recommended_library": {
      "name": "framer-motion",
      "install": "npm i framer-motion",
      "usage": [
        "Landing hero: fade+slide in headline and CTA",
        "Cards: subtle hover lift",
        "Studio step transitions: crossfade between steps"
      ],
      "fallback": "If not installed, use Tailwind transitions on opacity/background-color only (no transition: all)."
    },
    "interaction_specs": {
      "buttons": "transition-colors duration-150; primary adds shadow-sm on hover",
      "cards": "hover:shadow-md hover:-translate-y-0.5 (only on marketing pages)",
      "nav": "active link uses underline indicator + subtle background"
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text on backgrounds.",
      "Visible focus states on all interactive elements (ring + offset).",
      "Touch targets >= 44px height for primary controls.",
      "Keyboard navigable menus (NavigationMenu/DropdownMenu already helps).",
      "Reduced motion support."
    ],
    "content_truth": [
      "No fabricated metrics, ranks, endorsements, or guarantees.",
      "If BITSAT has no published sets, show an explicit empty state with next step."
    ]
  },
  "data_testid_conventions": {
    "rule": "All interactive and key informational elements MUST include data-testid in kebab-case describing role.",
    "examples": [
      "data-testid=\"landing-hero-start-practicing-button\"",
      "data-testid=\"exams-jee-card\"",
      "data-testid=\"studio-upload-submit-button\"",
      "data-testid=\"results-download-report-button\"",
      "data-testid=\"player-question-navigator\""
    ]
  },
  "image_urls": {
    "hero": [
      {
        "url": "https://images.unsplash.com/photo-1659355889768-5bb2aa1b84f9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTF8MHwxfHNlYXJjaHwxfHxpbmRpYW4lMjBzdHVkZW50JTIwc3R1ZHlpbmclMjBtaW5pbWFsJTIwZWRpdG9yaWFsJTIwYmx1ZSUyMHdoaXRlfGVufDB8fHxibHVlfDE3OTE3NTQ1NjB8MA&ixlib=rb-4.1.0&q=85",
        "category": "landing-hero",
        "description": "Calm student portrait; use inside a white card with soft border; avoid implying endorsements."
      }
    ],
    "secondary": [
      {
        "url": "https://images.unsplash.com/photo-1563888430434-7823117fa92e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTF8MHwxfHNlYXJjaHwyfHxpbmRpYW4lMjBzdHVkZW50JTIwc3R1ZHlpbmclMjBtaW5pbWFsJTIwZWRpdG9yaWFsJTIwYmx1ZSUyMHdoaXRlfGVufDB8fHxibHVlfDE3OTE3NTQ1NjB8MA&ixlib=rb-4.1.0&q=85",
        "category": "landing-trust-section",
        "description": "Optional small image for trust/accessibility section; keep subtle and not dominant."
      }
    ]
  },
  "instructions_to_main_agent": [
    "Do NOT touch backend. This revision is UI/UX only.",
    "Replace legacy CRA App.css leftovers; keep only utilities like line-clamp. Do not add `.App { text-align:center }`.",
    "Implement role-aware nav: public (Explore/How it works/Sign in + Start practicing CTA), student (My practice/Explore), staff (Studio/Explore).",
    "Hide landing anchors on non-landing routes.",
    "Studio IA: enforce 3-step pipeline (Upload→Review→Publish). Put Settings/Audit under 'More' dropdown to reduce cognitive load.",
    "Ensure no horizontal overflow: use ScrollArea for long lists; avoid wide tables on mobile.",
    "Use existing shadcn components from /src/components/ui (JS).",
    "Add data-testid to every interactive element and key info label/value.",
    "Keep gradients minimal and decorative only (hero wash). No gradients on reading areas.",
    "Use editorial spacing: section padding py-12/16, max-w-prose for text blocks, left-aligned content."
  ],
  "appendix_general_ui_ux_design_guidelines": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
