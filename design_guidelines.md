{
  "brand": {
    "name": "Stanvard School ERP",
    "personality": [
      "premium enterprise",
      "calm + trustworthy (finance + student data)",
      "warm for parents, precise for admins",
      "fast, minimal, accessible",
      "India-context friendly (₹, UPI, multi-branch)"
    ],
    "visual_style": {
      "layout_principles": [
        "Linear/Vercel-like density control: compact tables, generous page padding",
        "Notion-like clarity: soft neutrals, subtle dividers, strong typography hierarchy",
        "Bento KPI grid + activity feed",
        "No transparent/glass backgrounds (solid surfaces only)"
      ],
      "signature_details": [
        "Warm ‘paper’ background tint (not pure white)",
        "Navy primary + teal success + saffron accent (India cue) used sparingly",
        "Subtle noise texture only in hero/login header band (<=20% viewport)",
        "Rounded-rectangle geometry (10–12px) + crisp 1px borders"
      ]
    }
  },

  "design_tokens": {
    "colors": {
      "notes": [
        "Primary theme is LIGHT mode.",
        "Avoid purple for AI/chat (not relevant here, but keep palette consistent).",
        "No transparent backgrounds; cards are solid.",
        "Gradients only as decorative section backgrounds (<=20% viewport)."
      ],
      "palette_hex": {
        "bg": {
          "canvas": "#F7F8FB",
          "canvas_alt": "#F2F4F8",
          "sidebar": "#F5F7FA"
        },
        "surface": {
          "card": "#FFFFFF",
          "card_alt": "#FBFCFE",
          "popover": "#FFFFFF"
        },
        "text": {
          "primary": "#111827",
          "secondary": "#374151",
          "muted": "#6B7280",
          "inverse": "#F9FAFB"
        },
        "border": {
          "subtle": "#E6EAF0",
          "default": "#D7DEE8",
          "strong": "#C3CEDC"
        },
        "brand": {
          "primary_navy": "#0B2F4A",
          "primary_navy_hover": "#0A2740",
          "primary_navy_soft": "#E7F0F7",
          "accent_teal": "#0F766E",
          "accent_teal_soft": "#E6F6F4",
          "accent_saffron": "#D97706",
          "accent_saffron_soft": "#FFF3E0"
        },
        "semantic": {
          "success": "#0F766E",
          "success_bg": "#E6F6F4",
          "warning": "#B45309",
          "warning_bg": "#FFF3E0",
          "danger": "#B42318",
          "danger_bg": "#FEE4E2",
          "info": "#1D4ED8",
          "info_bg": "#E8F0FF"
        },
        "charts": {
          "chart_1_income": "#0B2F4A",
          "chart_2_collection": "#0F766E",
          "chart_3_pending": "#D97706",
          "chart_4_attendance": "#1D4ED8",
          "chart_5_neutral": "#64748B"
        }
      },
      "css_variables_recommendation": {
        "file": "/app/frontend/src/index.css",
        "instructions": [
          "Replace shadcn default HSL tokens with these HSL equivalents (or keep HEX in comments and convert).",
          "Keep --radius at 0.75rem for premium feel.",
          "Set --ring to primary navy for consistent focus.",
          "Set --muted to canvas_alt and --muted-foreground to text.muted.",
          "Update --chart-1..5 to match charts palette."
        ],
        "suggested_hsl": {
          "--background": "220 33% 98%",
          "--foreground": "222 47% 11%",
          "--card": "0 0% 100%",
          "--card-foreground": "222 47% 11%",
          "--popover": "0 0% 100%",
          "--popover-foreground": "222 47% 11%",
          "--primary": "203 74% 17%",
          "--primary-foreground": "210 40% 98%",
          "--secondary": "220 20% 96%",
          "--secondary-foreground": "203 74% 17%",
          "--muted": "220 20% 96%",
          "--muted-foreground": "215 16% 47%",
          "--accent": "173 55% 28%",
          "--accent-foreground": "210 40% 98%",
          "--destructive": "4 74% 40%",
          "--destructive-foreground": "210 40% 98%",
          "--border": "214 24% 88%",
          "--input": "214 24% 88%",
          "--ring": "203 74% 17%",
          "--chart-1": "203 74% 17%",
          "--chart-2": "173 55% 28%",
          "--chart-3": "32 90% 44%",
          "--chart-4": "221 83% 53%",
          "--chart-5": "215 16% 47%",
          "--radius": "0.75rem"
        }
      },
      "gradients_and_texture": {
        "allowed_gradients": [
          {
            "name": "login-header-band",
            "css": "linear-gradient(135deg, #F7F8FB 0%, #E7F0F7 45%, #E6F6F4 100%)",
            "usage": "Only as a top header band on /login and /parent home hero strip; keep height <= 180px on desktop, <= 140px on mobile."
          },
          {
            "name": "dashboard-accent-wash",
            "css": "radial-gradient(900px 300px at 20% 0%, rgba(15,118,110,0.10) 0%, rgba(15,118,110,0.00) 60%), radial-gradient(900px 300px at 80% 0%, rgba(11,47,74,0.10) 0%, rgba(11,47,74,0.00) 60%)",
            "usage": "Optional decorative background behind dashboard header area only (<=20% viewport)."
          }
        ],
        "noise_overlay": {
          "usage": "Optional subtle noise on large section backgrounds only (never on cards).",
          "css_snippet": ".noise-bg{position:relative;} .noise-bg:before{content:'';position:absolute;inset:0;background-image:url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Cfilter id=%22n%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.9%22 numOctaves=%222%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22120%22 height=%22120%22 filter=%22url(%23n)%22 opacity=%220.06%22/%3E%3C/svg%3E');mix-blend-mode:multiply;pointer-events:none;border-radius:inherit;}"
        }
      }
    },

    "typography": {
      "font_pairing": {
        "heading": {
          "name": "Space Grotesk",
          "fallback": "ui-sans-serif, system-ui",
          "why": "Modern enterprise feel (Linear-esque), crisp numerals for KPIs."
        },
        "body": {
          "name": "Inter",
          "fallback": "ui-sans-serif, system-ui",
          "why": "High legibility for dense tables/forms; familiar to enterprise users."
        }
      },
      "google_fonts_import": {
        "instructions": "Add to /app/frontend/public/index.html <head> or via CSS @import in index.css (prefer <link> for performance).",
        "links": [
          "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap"
        ]
      },
      "tailwind_usage": {
        "recommendation": "Set body font to Inter in index.css; use Space Grotesk via className on headings (e.g., font-[\"Space Grotesk\"]). If Tailwind config isn’t editable, use inline style or a utility class via arbitrary font-family.",
        "css_snippet": "body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;}
.h-font{font-family:'Space Grotesk',Inter,ui-sans-serif,system-ui;}"
      },
      "type_scale": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
        "h2": "text-base md:text-lg font-medium text-muted-foreground",
        "section_title": "text-lg md:text-xl font-semibold",
        "card_title": "text-sm font-medium text-muted-foreground",
        "kpi_value": "text-2xl md:text-3xl font-semibold tabular-nums",
        "body": "text-sm md:text-base",
        "small": "text-xs text-muted-foreground"
      },
      "numerals": {
        "rule": "Use tabular numbers for money/attendance counts.",
        "class": "tabular-nums"
      }
    },

    "spacing": {
      "system": "8px base",
      "tokens_px": {
        "1": 4,
        "2": 8,
        "3": 12,
        "4": 16,
        "5": 20,
        "6": 24,
        "8": 32,
        "10": 40,
        "12": 48,
        "16": 64
      },
      "layout_padding": {
        "page_x": "px-4 sm:px-6 lg:px-8",
        "page_y": "py-4 sm:py-6",
        "card_padding": "p-4 sm:p-5",
        "form_gap": "gap-4 sm:gap-5"
      }
    },

    "radius": {
      "scale": {
        "sm": "rounded-md (8px)",
        "md": "rounded-lg (12px)",
        "lg": "rounded-xl (16px)"
      },
      "default": "rounded-lg",
      "rule": "Use rounded-lg for cards/dialogs; rounded-md for inputs; avoid fully pill buttons except small chips."
    },

    "shadows": {
      "scale": {
        "xs": "shadow-[0_1px_0_rgba(16,24,40,0.04)]",
        "sm": "shadow-[0_1px_2px_rgba(16,24,40,0.06)]",
        "md": "shadow-[0_6px_18px_rgba(16,24,40,0.08)]"
      },
      "rule": "Prefer borders over heavy shadows; use md shadow only for dialogs/drawers/popovers."
    }
  },

  "layout_system": {
    "app_shell": {
      "pattern": "Sidebar + Top Header (sticky) + Content",
      "sidebar": {
        "width": "w-[280px] (desktop), collapsible to icons-only w-[72px]",
        "mobile": "Use Sheet (drawer) for sidebar",
        "components": ["/app/frontend/src/components/ui/sheet.jsx", "/app/frontend/src/components/ui/navigation-menu.jsx", "/app/frontend/src/components/ui/scroll-area.jsx"],
        "nav_item_style": {
          "base": "flex items-center gap-2 rounded-md px-3 py-2 text-sm text-foreground/80 hover:bg-secondary hover:text-foreground",
          "active": "bg-secondary text-foreground font-medium",
          "icon": "h-4 w-4 text-muted-foreground group-hover:text-foreground"
        }
      },
      "header": {
        "height": "h-14",
        "sticky": "sticky top-0 z-40",
        "style": "bg-card border-b",
        "left": "Breadcrumb + Page title",
        "center": "(optional) global search",
        "right": "School switcher + notifications + user menu",
        "components": ["/app/frontend/src/components/ui/breadcrumb.jsx", "/app/frontend/src/components/ui/command.jsx", "/app/frontend/src/components/ui/dropdown-menu.jsx", "/app/frontend/src/components/ui/avatar.jsx", "/app/frontend/src/components/ui/button.jsx"]
      },
      "content_container": {
        "max_width": "max-w-[1400px]",
        "rule": "Do not center-align text globally; align content naturally left."
      }
    },

    "grid_patterns": {
      "dashboard": {
        "top_row": "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4",
        "middle": "grid grid-cols-1 xl:grid-cols-3 gap-4",
        "charts": "xl:col-span-2",
        "activity_feed": "xl:col-span-1"
      },
      "list_pages": {
        "toolbar": "flex flex-col gap-3 md:flex-row md:items-center md:justify-between",
        "table_wrap": "rounded-lg border bg-card",
        "filters": "use Drawer on mobile; inline on desktop"
      },
      "detail_pages": {
        "header": "flex flex-col gap-3 md:flex-row md:items-start md:justify-between",
        "body": "grid grid-cols-1 xl:grid-cols-3 gap-4",
        "main": "xl:col-span-2",
        "side": "xl:col-span-1"
      }
    }
  },

  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui/",
      "use_components": [
        "button.jsx",
        "input.jsx",
        "select.jsx",
        "textarea.jsx",
        "checkbox.jsx",
        "radio-group.jsx",
        "badge.jsx",
        "card.jsx",
        "table.jsx",
        "tabs.jsx",
        "dialog.jsx",
        "drawer.jsx",
        "sheet.jsx",
        "dropdown-menu.jsx",
        "popover.jsx",
        "calendar.jsx",
        "command.jsx",
        "pagination.jsx",
        "tooltip.jsx",
        "sonner.jsx"
      ]
    },

    "buttons": {
      "variants": {
        "primary": {
          "usage": "Main actions: Collect Fee, Save, Publish, Send Notification",
          "style": "bg-[--primary] text-[--primary-foreground] hover:bg-[#0A2740]",
          "motion": "transition-colors duration-150; active:scale-[0.98] (apply only on button)"
        },
        "secondary": {
          "usage": "Secondary actions: Export, View Receipt",
          "style": "bg-secondary text-secondary-foreground hover:bg-secondary/70 border border-border",
          "motion": "transition-colors duration-150"
        },
        "ghost": {
          "usage": "Icon buttons in header/table rows",
          "style": "hover:bg-secondary",
          "motion": "transition-colors duration-150"
        },
        "destructive": {
          "usage": "Delete student/fee head",
          "style": "bg-destructive text-destructive-foreground hover:bg-destructive/90"
        }
      },
      "sizes": {
        "sm": "h-8 px-3 text-sm",
        "md": "h-9 px-4",
        "lg": "h-10 px-5"
      },
      "data_testid_rule": "All buttons must include data-testid (e.g., data-testid=\"fee-collect-submit-button\")."
    },

    "inputs_forms": {
      "rules": [
        "Always show Label above input (use shadcn Label).",
        "Use helper text for formats (UPI ref, cheque no.).",
        "Errors: show inline text + red border + aria-describedby.",
        "Do not rely on placeholder as label."
      ],
      "patterns": {
        "field_group": "grid gap-2",
        "two_col": "grid grid-cols-1 md:grid-cols-2 gap-4",
        "money_input": "right-aligned tabular-nums; prefix ₹ as muted text"
      },
      "components": ["label.jsx", "input.jsx", "select.jsx", "textarea.jsx", "radio-group.jsx", "checkbox.jsx"]
    },

    "cards_kpis": {
      "kpi_card": {
        "structure": [
          "CardHeader: label + small trend badge",
          "CardContent: big number + subtext",
          "Optional sparkline (Recharts)"
        ],
        "style": "bg-card border rounded-lg p-4 sm:p-5",
        "micro_interaction": "On hover: border color to strong + subtle lift shadow-sm (no transform on container if it breaks layout; prefer shadow change).",
        "testids": [
          "data-testid=\"kpi-total-students\"",
          "data-testid=\"kpi-fees-collected\"",
          "data-testid=\"kpi-attendance-today\""
        ]
      }
    },

    "tables": {
      "style": {
        "header": "bg-secondary/60 text-xs uppercase tracking-wide text-muted-foreground",
        "row": "hover:bg-secondary/40",
        "cell": "py-3",
        "sticky_header": "optional for long lists"
      },
      "patterns": {
        "row_actions": "Use DropdownMenu with actions (View, Edit, Collect Fee).",
        "bulk_actions": "Checkbox in first column + toolbar appears when selected.",
        "empty_state": "Centered within table container with icon + CTA"
      },
      "accessibility": [
        "Use proper <TableHead> and <TableRow> semantics from shadcn table.",
        "Ensure row action buttons are keyboard reachable.",
        "Add data-testid to search input, filters, pagination controls."
      ]
    },

    "badges": {
      "usage": "Payment status, attendance status, role tags",
      "mapping": {
        "paid": "bg-[#E6F6F4] text-[#0F766E] border border-[#BFEAE6]",
        "pending": "bg-[#FFF3E0] text-[#B45309] border border-[#FFD7A8]",
        "overdue": "bg-[#FEE4E2] text-[#B42318] border border-[#FECACA]",
        "draft": "bg-secondary text-muted-foreground border"
      }
    },

    "dialogs_drawers": {
      "rule": "Use Dialog for confirmations and small forms; Drawer for mobile-first editing/filter panels.",
      "components": ["dialog.jsx", "drawer.jsx", "alert-dialog.jsx"],
      "motion": "Keep durations 150–220ms; prefer opacity/translate on overlay/content only."
    },

    "toasts": {
      "library": "sonner",
      "component": "/app/frontend/src/components/ui/sonner.jsx",
      "rules": [
        "Use for success/error after save/payment/receipt generation.",
        "Include action when relevant (e.g., View Receipt).",
        "Add data-testid to toast trigger buttons; toast itself can be asserted by text."
      ]
    }
  },

  "page_specific_guidelines": {
    "login": {
      "layout": "Split layout on desktop (left brand panel, right form). Single column on mobile.",
      "left_panel": {
        "background": "Use login-header-band gradient + noise overlay (<=20% viewport).",
        "content": "Stanvard logo, tagline, 3 trust bullets (Secure payments, Multi-branch, Audit logs)."
      },
      "form": {
        "components": ["card.jsx", "input.jsx", "button.jsx", "select.jsx"],
        "role_hint": "Show role chips (Super Admin/School Admin/Accountant/Teacher/Parent) as non-interactive helper badges.",
        "testids": [
          "login-email-input",
          "login-password-input",
          "login-submit-button"
        ]
      }
    },

    "school_switcher": {
      "placement": "Always visible in header, left of notifications.",
      "interaction": {
        "component": "Popover + Command (searchable list)",
        "behavior": [
          "Shows current branch name + short code (e.g., ‘Ganesh Nagar • KNP’)",
          "Search by branch name/city",
          "Instant switch with optimistic UI; show toast ‘Switched to …’",
          "Persist selection in localStorage"
        ],
        "testids": [
          "school-switcher-trigger",
          "school-switcher-search-input",
          "school-switcher-option-ganesh-nagar",
          "school-switcher-option-kanpur",
          "school-switcher-option-ayar"
        ]
      },
      "visual": "Use subtle left accent bar in dropdown items (primary_navy_soft) for selected branch."
    },

    "dashboard": {
      "must_have_widgets": [
        "KPI bento grid",
        "Fee collection trend chart (Recharts)",
        "Attendance today (mini chart)",
        "Calendar (shadcn Calendar)",
        "Activity feed (audit-like)"
      ],
      "charts": {
        "library": "recharts",
        "style": [
          "Use muted gridlines (#E6EAF0)",
          "Use tabular-nums for axis ticks",
          "Tooltips in Card-like popover (bg-card border shadow-md)"
        ],
        "testids": [
          "dashboard-fee-collection-chart",
          "dashboard-attendance-chart"
        ]
      }
    },

    "students": {
      "list": {
        "row": "Avatar (photo) + name + class/section + guardian + fee status badge",
        "filters": "Class, Section, Status, Search",
        "bulk": "Promote, Assign fee plan, Send notification",
        "testids": [
          "students-search-input",
          "students-filter-class-select",
          "students-add-button",
          "students-table"
        ]
      },
      "profile": {
        "layout": "Detail header + Tabs (Info, Fees, Attendance, Documents)",
        "components": ["tabs.jsx", "card.jsx", "table.jsx", "badge.jsx"],
        "testids": [
          "student-profile-tabs",
          "student-profile-fees-tab",
          "student-profile-attendance-tab"
        ]
      }
    },

    "fee_collection": {
      "layout": "Two-pane on desktop: left student + fee items, right payment summary. Single column on mobile with sticky summary CTA.",
      "left_pane": {
        "sections": [
          "Student picker (Command)",
          "Fee heads checklist with amounts",
          "Discount + Late fee inputs",
          "Notes (optional)"
        ]
      },
      "right_pane": {
        "summary_card": [
          "Subtotal",
          "Discount",
          "Late fee",
          "Total payable (large)",
          "Payment mode (RadioGroup)",
          "Conditional fields: UPI ref, cheque no, bank txn id",
          "Primary CTA: Generate Receipt"
        ],
        "payment_modes": ["Cash", "UPI", "Card", "Cheque", "Bank Transfer", "Razorpay"],
        "testids": [
          "fee-collect-student-picker",
          "fee-collect-discount-input",
          "fee-collect-latefee-input",
          "fee-collect-payment-mode",
          "fee-collect-generate-receipt-button"
        ]
      },
      "micro_interactions": [
        "As fee heads are toggled, animate total number change with a subtle count-up (optional).",
        "On successful payment/receipt generation: toast with ‘View PDF’ action."
      ]
    },

    "receipts": {
      "list": {
        "table": "Receipt No, Student, Date, Amount, Mode, Status, Actions",
        "actions": "View PDF, Download, Refund (if allowed)",
        "testids": ["receipts-table", "receipt-download-button"]
      },
      "pdf_view": {
        "pattern": "In-app viewer in Dialog/Drawer with Download button; fallback to open in new tab.",
        "testids": ["receipt-pdf-viewer", "receipt-pdf-download"]
      }
    },

    "attendance": {
      "marking_grid": {
        "pattern": "Sticky first column (student names) + date columns; quick toggles present/absent.",
        "components": ["table.jsx", "toggle-group.jsx", "badge.jsx"],
        "colors": {
          "present": "success_bg/success",
          "absent": "danger_bg/danger",
          "leave": "warning_bg/warning"
        },
        "testids": ["attendance-class-select", "attendance-grid", "attendance-save-button"]
      }
    },

    "parent_portal": {
      "tone": "Warmer, simpler, fewer admin controls.",
      "layout": "Top child selector + 3 primary cards: Pay Fees, Attendance, Homework. Secondary: Receipts, Circulars.",
      "visual": [
        "Use accent_teal_soft and accent_saffron_soft as card highlights (solid, not gradients).",
        "Use larger tap targets (min h-11 for primary buttons).",
        "Use plain language labels (e.g., ‘Pay fees’ not ‘Fee collection’)."
      ],
      "testids": [
        "parent-child-selector",
        "parent-pay-fees-button",
        "parent-receipts-link",
        "parent-homework-card"
      ]
    }
  },

  "libraries": {
    "icons": {
      "library": "lucide-react",
      "usage": "Use consistent 16px icons in nav, 18px in buttons, 20px in empty states.",
      "rule": "No emoji icons."
    },
    "charts": {
      "library": "recharts",
      "usage": "Dashboard KPIs + fee trends + attendance trends.",
      "install": "npm i recharts",
      "scaffold_js": "import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';"
    },
    "motion": {
      "library": "framer-motion (optional)",
      "install": "npm i framer-motion",
      "usage": "Page transitions (fade/slide), KPI entrance stagger, drawer transitions. Keep subtle.",
      "rule": "Respect prefers-reduced-motion."
    }
  },

  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text and interactive controls.",
      "Visible focus ring using --ring (navy).",
      "Keyboard navigation for menus, dialogs, tables.",
      "Use aria-label for icon-only buttons.",
      "Do not convey status by color alone; pair with text/badge label."
    ],
    "focus_styles": {
      "rule": "Use focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      "ring_offset": "bg matches surface (card)"
    }
  },

  "image_urls": {
    "login_brand_panel": [
      {
        "url": "https://images.unsplash.com/photo-1613896527026-f195d5c818ed?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85",
        "description": "School building exterior (generic). Use as subtle background image with low opacity overlay.",
        "category": "login"
      }
    ],
    "parent_portal_hero": [
      {
        "url": "https://images.unsplash.com/photo-1619852182277-79aa23f82c8e?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85",
        "description": "Parent using laptop (generic). Use in parent portal header card or empty state illustration.",
        "category": "parent"
      }
    ],
    "gallery_placeholder": [
      {
        "url": "https://images.unsplash.com/photo-1577896851231-70ef18881754?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85",
        "description": "Classroom scene placeholder for gallery albums.",
        "category": "gallery"
      }
    ]
  },

  "instructions_to_main_agent": {
    "implementation_priorities": [
      "1) Replace App.css default CRA header styles; ensure no global center alignment.",
      "2) Update index.css tokens to match palette; keep light mode primary.",
      "3) Build AppShell (Sidebar + Header) with School Switcher always visible.",
      "4) Implement data-testid on all interactive elements and key info fields.",
      "5) Use shadcn components for all UI primitives (no raw HTML dropdowns/calendars/toasts).",
      "6) Use Recharts for dashboard charts; keep tooltips and axes styled to tokens.",
      "7) Parent portal: simplify IA, larger tap targets, warmer accent surfaces."
    ],
    "data_testid_convention": {
      "rule": "kebab-case describing role, page, and element purpose",
      "examples": [
        "school-switcher-trigger",
        "students-add-button",
        "fee-collect-generate-receipt-button",
        "receipt-pdf-download",
        "parent-pay-fees-button"
      ]
    },
    "do_not": [
      "Do not use transparent/glass backgrounds.",
      "Do not use transition: all.",
      "Do not apply gradients beyond header bands (<=20% viewport).",
      "Do not use emoji icons."
    ]
  },

  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
