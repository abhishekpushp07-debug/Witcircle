{
  "addendum_meta": {
    "purpose": "ADDENDUM ONLY: normalize existing teal/blue literals to a matte maroon semantic token system + add coherent light/dark roles. No layout rewrite, no new component architecture.",
    "requested_change": "Change teal blue to maroon matte; preserve approved nav + ExamDetails polish and existing practice/player/results/staff architecture.",
    "critical_constraints": [
      "Do not change scope or code architecture.",
      "App.css is large (~6000 lines) with many historic blue/teal literals; migrate by mapping to tokens (no new styles).",
      "Add a dark palette system preference support via tokens (do not redesign layouts).",
      "Fonts must be Figtree (UI) + Roboto Mono (numbers).",
      "Primary buttons in dark mode must remain maroon with WHITE text (not pink/white).",
      "All interactive and key informational elements MUST include data-testid (kebab-case, role-based)."
    ]
  },

  "typography_addendum": {
    "font_pairing": {
      "ui": {
        "family": "Figtree",
        "weights": [400, 500, 600, 700],
        "use_for": ["body", "headings", "buttons", "labels", "nav"]
      },
      "numbers": {
        "family": "Roboto Mono",
        "weights": [400, 500, 600],
        "use_for": ["timer", "scores", "marks", "question numbers", "codes", "file extensions"],
        "css_note": "Apply tabular figures where possible: font-variant-numeric: tabular-nums;"
      }
    },
    "implementation_note_js": {
      "index_css_google_fonts_import": "Replace existing Google Fonts import with: https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap",
      "global_font_rules": {
        "body": "font-family: 'Figtree', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;",
        "headings": "font-family: 'Figtree', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;",
        "mono": "font-family: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;"
      }
    }
  },

  "color_system_addendum": {
    "strategy": {
      "goal": "Single coherent matte maroon system with explicit light + dark roles. Replace historical teal/blue literals by semantic roles without changing layout.",
      "brand_character": "premium, exam-serious, matte (low gloss), high contrast, calm",
      "non_negotiables": [
        "Brand primary is matte maroon (not rose/pink).",
        "Dark mode uses deep maroon surfaces + white on-brand text.",
        "Keep success green semantic; do not recolor success to maroon.",
        "Avoid gradients except subtle hero wash (<=20% viewport)."
      ]
    },

    "semantic_roles_light": {
      "surface": "#F8FAFC",
      "surface_alt": "#FBF7F5",
      "card": "#FFFFFF",
      "card_alt": "#FCFCFD",
      "ink": "#0B1F2A",
      "muted": "#4B6476",
      "muted_2": "#6B8192",
      "line": "#D7DEE7",

      "brand_primary": "#5C0025",
      "brand_hover": "#4A001E",
      "brand_active": "#3B0018",
      "brand_soft": "#F6E9EE",
      "brand_line": "#EBCFD9",
      "on_brand": "#FFFFFF",
      "focus_ring": "#8B1D3D",

      "success": "#16714B",
      "success_soft": "#EAF7F0",
      "success_line": "#CFEBDD",

      "warning": "#905515",
      "warning_soft": "#FFF7E9",
      "warning_line": "#F3E5C6",

      "danger": "#B42332",
      "danger_soft": "#FFF1F2",
      "danger_line": "#F0D7DD",

      "review": "#6B1B3A",
      "review_soft": "#F4EFF2",
      "review_line": "#D9B8C6",

      "hero_dark": "#1A0B12"
    },

    "semantic_roles_dark": {
      "surface": "#0E0A0C",
      "surface_alt": "#141013",
      "card": "#151114",
      "card_alt": "#1B1519",
      "ink": "#F6F7F9",
      "muted": "#C7CDD6",
      "muted_2": "#9AA6B2",
      "line": "#2A2227",

      "brand_primary": "#5C0025",
      "brand_hover": "#6A0A2F",
      "brand_active": "#4A001E",
      "brand_soft": "rgba(92,0,37,0.22)",
      "brand_line": "rgba(235,207,217,0.22)",
      "on_brand": "#FFFFFF",
      "focus_ring": "#D9B8C6",

      "success": "#2AA36B",
      "success_soft": "rgba(42,163,107,0.16)",
      "success_line": "rgba(42,163,107,0.28)",

      "warning": "#E0A24A",
      "warning_soft": "rgba(224,162,74,0.16)",
      "warning_line": "rgba(224,162,74,0.28)",

      "danger": "#E05A6A",
      "danger_soft": "rgba(224,90,106,0.16)",
      "danger_line": "rgba(224,90,106,0.28)",

      "review": "#E2B6C6",
      "review_soft": "rgba(217,184,198,0.14)",
      "review_line": "rgba(217,184,198,0.26)",

      "hero_dark": "#0B0709"
    },

    "token_binding_plan_existing_css": {
      "principle": "Keep existing variable names to avoid layout rewrite; only swap values and map literals to semantic roles.",
      "App_css_root_vars": {
        "keep_names_swap_values": {
          "--blue": "brand_primary",
          "--navy": "ink (light) / ink-like heading color; in dark becomes ink (light text) but keep --navy as heading token",
          "--page": "surface",
          "--ink": "ink",
          "--muted": "muted",
          "--line": "line",
          "--green": "success",
          "--amber": "warning",
          "--red": "danger"
        },
        "dark_mode_extension": {
          "how": "Add a prefers-color-scheme: dark block that overrides the same vars (no new classnames).",
          "vars_to_override": ["--page", "--navy", "--ink", "--muted", "--line", "--blue", "--green", "--amber", "--red"]
        }
      },
      "index_css_shadcn_hsl_tokens": {
        "light": {
          "--primary": "338 100% 18%",
          "--primary-foreground": "0 0% 100%",
          "--ring": "345 65% 33%",
          "--background": "210 40% 98%",
          "--foreground": "205 45% 12%",
          "--border": "214 20% 88%",
          "--muted": "210 25% 95%",
          "--muted-foreground": "205 18% 38%"
        },
        "dark": {
          "note": "Add .dark or prefers-color-scheme mapping depending on existing setup; do not change architecture—only define tokens.",
          "--background": "330 10% 5%",
          "--foreground": "210 20% 98%",
          "--card": "330 12% 8%",
          "--card-foreground": "210 20% 98%",
          "--primary": "338 100% 18%",
          "--primary-foreground": "0 0% 100%",
          "--border": "330 10% 16%",
          "--muted": "330 10% 12%",
          "--muted-foreground": "215 12% 78%",
          "--ring": "345 35% 78%"
        }
      }
    },

    "migration_guidance_literal_to_semantic": {
      "goal": "Consolidate ~300 historic blue/teal literals into a small set of semantic roles.",
      "rules": [
        "Any teal/blue used for PRIMARY actions/active states -> brand_primary (var(--blue)).",
        "Any light blue tint backgrounds (e.g., #edf3ff, #eef4ff, #eaf2ff, #f0f5ff) -> brand_soft OR surface_alt depending on intent:",
        "- If it indicates selection/active/brand emphasis -> brand_soft.",
        "- If it is just a gentle section background -> surface_alt.",
        "Any blue borders (e.g., #d9e5f8, #dbe6f6, #d6e6ef) -> line.",
        "Any blue focus outlines (#1d4ed8, #2563eb) -> focus_ring.",
        "Keep success greens as success; keep warning ambers as warning; keep danger reds as danger.",
        "Marked-for-review purple literals must be migrated to review_* tokens (plum-rose, not neon purple)."
      ],
      "high_value_targets_in_App_css": {
        "focus": {
          "current": ":focus-visible outline: 3px solid #1d4ed8",
          "migrate_to": "outline: 3px solid var(--focus-ring, #8B1D3D) OR replace literal with brand focus token"
        },
        "player": {
          "timer_chip": "#edf3ff/#d9e6fa/#38669f -> brand_soft/brand_line/brand_primary",
          "answer_selected": "#f0f5ff/#4f83e4/#245ba8 -> brand_soft/brand_primary/ink",
          "current_question_outline": "var(--blue) already maps to maroon; keep",
          "marked_state": "#9b86c4/#6f539d/#f6f2ff -> review_line/review/review_soft"
        },
        "results": {
          "score_card": "background var(--blue) becomes maroon; ensure small text uses on-brand white",
          "progress_bar": "background var(--blue) becomes maroon"
        },
        "landing": {
          "hero_bg": "#f5f9ff -> surface_alt",
          "cta_panel": "var(--navy) -> hero_dark (solid)"
        }
      }
    },

    "button_readability_in_dark": {
      "requirement": "Primary buttons must be maroon background with WHITE text in both themes.",
      "do_not": [
        "Do not invert to light/pink buttons in dark mode.",
        "Do not use gradients on buttons.",
        "Do not reduce contrast by using off-white text on maroon below AA."
      ],
      "recommended_states": {
        "default": "bg brand_primary, text on_brand",
        "hover": "bg brand_hover",
        "active": "bg brand_active",
        "focus": "ring focus_ring with offset matching surface"
      }
    }
  },

  "component_path": {
    "shadcn_primary": "/app/frontend/src/components/ui",
    "use_existing": [
      "button.jsx",
      "badge.jsx",
      "card.jsx",
      "input.jsx",
      "label.jsx",
      "tabs.jsx",
      "sheet.jsx",
      "dialog.jsx",
      "alert.jsx",
      "progress.jsx",
      "sonner.jsx"
    ],
    "note": "No new components required for this addendum; only ensure shadcn tokens align with maroon palette and dark mode tokens exist. Project uses .js/.jsx (not .tsx)."
  },

  "instructions_to_main_agent": [
    "Treat this as an addendum: update only tokens + font imports + literal-to-token mapping guidance; do not change layout or architecture.",
    "Replace Google Fonts import in index.css to Figtree + Roboto Mono; update body/headings/mono font-family accordingly.",
    "Implement explicit light + dark semantic roles by overriding existing CSS vars in App.css (:root + prefers-color-scheme: dark).",
    "Normalize historical teal/blue literals using the mapping rules: tints -> brand_soft/surface_alt, borders -> line, focus blues -> focus_ring, primary blues -> brand_primary.",
    "Ensure all primary CTAs remain maroon with white text in dark mode; verify hover/active states are darker maroon (not pink).",
    "When touching any interactive element during polish, add/keep data-testid attributes (kebab-case, role-based)."
  ],

  "General_UI_UX_Design_Guidelines": [
    "You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms",
    "You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text",
    "NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json",
    "GRADIENT RESTRICTION RULE",
    "NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc",
    "NEVER use dark gradients for logo, testimonial, footer etc",
    "NEVER let gradients cover more than 20% of the viewport.",
    "NEVER apply gradients to text-heavy content or reading areas.",
    "NEVER use gradients on small UI elements (<100px width).",
    "NEVER stack multiple gradient layers in the same viewport.",
    "ENFORCEMENT RULE:",
    "    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors",
    "How and where to use:",
    "   • Section backgrounds (not content backgrounds)",
    "   • Hero section header content. Eg: dark to light to dark color",
    "   • Decorative overlays and accent elements only",
    "   • Hero section with 2-3 mild color",
    "   • Gradients creation can be done for any angle say horizontal, vertical or diagonal",
    "- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc",
    "- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead.",
    "- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.",
    "- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.",
    "- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly",
    "Component Reuse:",
    "\t- Prioritize using pre-existing components from src/components/ui when applicable",
    "\t- Create new components that match the style and conventions of existing components when needed",
    "\t- Examine existing components to understand the project's component patterns before creating new ones",
    "IMPORTANT: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component",
    "Best Practices:",
    "\t- Use Shadcn/UI as the primary component library for consistency and accessibility",
    "\t- Import path: ./components/[component-name]",
    "Export Conventions:",
    "\t- Components MUST use named exports (export const ComponentName = ...)",
    "\t- Pages MUST use default exports (export default function PageName() {...})",
    "Toasts:",
    "  - Use `sonner` for toasts",
    "  - Sonner component are located in `/app/src/components/ui/sonner.tsx`",
    "Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
  ]
}
