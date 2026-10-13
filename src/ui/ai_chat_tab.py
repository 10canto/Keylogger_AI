"""
ai_chat_tab.py
==============
AI Security Assistant tab — Tkinter UI panel.

Integrates with AIChatService to provide a fully interactive Gemma 4 31B
chatbot inside the existing dashboard notebook.

Design rules
------------
  • Matches the existing application theme exactly:
      - Color palette from dashboard.C
      - Fonts: Segoe UI throughout
      - ttk styles: Modern.TFrame, Modern.Vertical.TScrollbar
      - Flat buttons with hover effects identical to other tabs
  • All Gemini API calls run in AIChatService's background thread.
    The _on_response() callback is scheduled back onto the main thread
    via self.after(0, ...) — never touches widgets from a worker thread.
  • No keystrokes, passwords, or personal data are forwarded to the API.
  • The tab degrades gracefully when the API key is missing.
"""

from __future__ import annotations

import textwrap
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ai_chat_service import AIChatService, ChatResponse

# ---------------------------------------------------------------------------
# Re-use the exact color palette and font conventions from dashboard.py
# ---------------------------------------------------------------------------
C = {
    "bg":           "#f5f7fa",
    "surface":      "#ffffff",
    "border":       "#e1e4e8",
    "border_hover": "#cbd2d9",
    "text":         "#2c3e50",
    "text_dim":     "#6c757d",
    "text_light":   "#95a5a6",
    "safe":         "#27ae60",
    "suspicious":   "#f39c12",
    "malicious":    "#e74c3c",
    "accent":       "#3498db",
    "accent_hover": "#2980b9",
    "btn_bg":       "#ecf0f1",
    "btn_hover":    "#d5dbdb",
    "btn_primary":  "#3498db",
    "btn_danger":   "#e74c3c",
}

# Chat-specific extra colors (not in the base palette)
_C_USER_BG      = "#dbeafe"   # light blue bubble  — user messages
_C_USER_FG      = "#1e3a5f"   # dark navy text
_C_ASST_BG      = "#ffffff"   # white bubble       — assistant messages
_C_ASST_FG      = C["text"]
_C_ERROR_BG     = "#fdecea"   # light red          — error messages
_C_ERROR_FG     = C["malicious"]
_C_SYSTEM_BG    = "#f0f7ff"   # pale blue          — system / welcome
_C_SYSTEM_FG    = "#2471a3"
_C_LOADING_FG   = C["text_dim"]
_C_SEND_ACTIVE  = C["accent"]
_C_SEND_HOVER   = C["accent_hover"]
_C_SEND_DIS     = "#a9cce3"

# Suggested question button colors
_C_SUGG_BG      = "#eaf4fb"
_C_SUGG_HOVER   = "#d6eaf8"
_C_SUGG_FG      = "#1a6a9a"
_C_SUGG_BORDER  = "#aed6f1"

# ---------------------------------------------------------------------------
# Suggested starter questions
# ---------------------------------------------------------------------------
SUGGESTIONS = [
    ("🔍 Analyze Latest Alert",       "Analyze my latest security alert in detail."),
    ("🔎 Explain Suspicious Process", "Explain what makes the most suspicious process flagged by the detection system."),
    ("📊 Summarize Security Status",  "Give me a summary of my current security status based on the dashboard data."),
    ("📈 Explain My Risk Score",      "What does my current risk score mean and how is it calculated?"),
    ("📋 Analyze Detection History",  "Analyze my recent detection history and identify any patterns or concerns."),
    ("🛡️ How to Prevent Keyloggers",  "How can I protect my computer from keyloggers?"),
]

# ---------------------------------------------------------------------------
# Helper: wrap text for display
# ---------------------------------------------------------------------------
_WRAP = 90   # chars before line-wrapping assistant text in the Text widget


class _AIChatTab(ttk.Frame):
    """
    The AI Security Assistant tab widget.

    Parameters
    ----------
    parent       : ttk.Notebook or any Tk container
    chat_service : AIChatService instance (may be None — tab degrades gracefully)
    """

    def __init__(
        self,
        parent: tk.Widget,
        chat_service: Optional["AIChatService"] = None,
    ) -> None:
        super().__init__(parent, style="Modern.TFrame")
        self._svc: Optional["AIChatService"] = chat_service
        self._root_ref: Optional[tk.Tk] = None
        self._busy = False          # True while waiting for API response
        self._msg_count = 0         # total messages rendered (for alternating colors)
        self._build()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_root_ref(self, root: tk.Tk) -> None:
        self._root_ref = root

    def set_chat_service(self, svc: "AIChatService") -> None:
        """Allow late-binding of the service (called from dashboard after init)."""
        self._svc = svc
        # Re-check key status and update the banner
        self.after(100, self._update_key_banner)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)   # chat area expands

        # ── Header ──────────────────────────────────────────────────────
        self._build_header()

        # ── API-key banner (shown when key missing) ──────────────────────
        self._build_key_banner()

        # ── Chat transcript area ─────────────────────────────────────────
        self._build_chat_area()

        # ── Suggested questions ──────────────────────────────────────────
        self._build_suggestions()

        # ── Input bar ───────────────────────────────────────────────────
        self._build_input_bar()

        # ── Status / model line ─────────────────────────────────────────
        self._build_status_bar()

        # Populate welcome message after widgets exist
        self.after(50, self._show_welcome)
        self.after(150, self._update_key_banner)

    # ── Header ──────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=C["surface"],
                       highlightthickness=1, highlightbackground=C["border"])
        hdr.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        inner = tk.Frame(hdr, bg=C["surface"], pady=10)
        inner.pack(fill=tk.X, padx=16)

        # Left: icon + title
        left = tk.Frame(inner, bg=C["surface"])
        left.pack(side=tk.LEFT)

        tk.Label(
            left, text="🤖", bg=C["surface"],
            font=("Segoe UI Emoji", 20), anchor="w",
        ).pack(side=tk.LEFT, padx=(0, 10))

        title_block = tk.Frame(left, bg=C["surface"])
        title_block.pack(side=tk.LEFT)

        tk.Label(
            title_block, text="AI Security Assistant",
            bg=C["surface"], fg=C["text"],
            font=("Segoe UI", 14, "bold"), anchor="w",
        ).pack(anchor="w")

        tk.Label(
            title_block,
            text="Powered by Google Gemma 4 31B  •  Reads live detection data",
            bg=C["surface"], fg=C["text_dim"],
            font=("Segoe UI", 8), anchor="w",
        ).pack(anchor="w")

        # Right: Clear button
        right = tk.Frame(inner, bg=C["surface"])
        right.pack(side=tk.RIGHT)

        self._btn_clear = tk.Button(
            right, text="🗑  Clear Chat",
            command=self._clear_chat,
            bg=C["btn_bg"], fg=C["text"],
            relief=tk.FLAT, padx=12, pady=6,
            font=("Segoe UI", 9), cursor="hand2", borderwidth=0,
        )
        self._btn_clear.pack(side=tk.RIGHT, padx=(8, 0))
        self._btn_clear.bind("<Enter>", lambda e: self._btn_clear.config(bg=C["btn_hover"]))
        self._btn_clear.bind("<Leave>", lambda e: self._btn_clear.config(bg=C["btn_bg"]))

    # ── API key banner ───────────────────────────────────────────────────

    def _build_key_banner(self) -> None:
        self._key_banner = tk.Frame(
            self, bg="#fff8e1",
            highlightthickness=1, highlightbackground="#f0c040",
        )
        # Row 1 (between header and chat)
        self._key_banner.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 0))
        self._key_banner.grid_remove()   # hidden by default

        tk.Label(
            self._key_banner,
            text=(
                "⚠️  No API key found.  "
                "Set GEMMA_API_KEY in a .env file next to main.py, then restart.  "
                "See .env.example for instructions."
            ),
            bg="#fff8e1", fg="#7d6608",
            font=("Segoe UI", 9), anchor="w", padx=12, pady=8,
            wraplength=780,
        ).pack(fill=tk.X)

    def _update_key_banner(self) -> None:
        """Show/hide the key banner depending on service state."""
        if self._svc is None or not self._svc.sdk_available or not self._svc.api_key_present:
            self._key_banner.grid()
            # Shift chat area down
            self._chat_outer.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 0))
            self.rowconfigure(1, weight=0)
            self.rowconfigure(2, weight=1)
        else:
            self._key_banner.grid_remove()
            self._chat_outer.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 0))
            self.rowconfigure(1, weight=0)
            self.rowconfigure(2, weight=1)

    # ── Chat transcript ──────────────────────────────────────────────────

    def _build_chat_area(self) -> None:
        # Outer frame (row 2 — expands)
        self._chat_outer = tk.Frame(self, bg=C["bg"])
        self._chat_outer.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 0))
        self._chat_outer.columnconfigure(0, weight=1)
        self._chat_outer.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Canvas + scrollbar for the chat transcript
        self._canvas = tk.Canvas(
            self._chat_outer, bg=C["bg"],
            highlightthickness=0, borderwidth=0,
        )
        self._vsb = ttk.Scrollbar(
            self._chat_outer, orient="vertical",
            command=self._canvas.yview,
            style="Modern.Vertical.TScrollbar",
        )
        self._canvas.configure(yscrollcommand=self._vsb.set)

        self._vsb.grid(row=0, column=1, sticky="ns")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # Inner frame rendered inside the canvas
        self._msg_frame = tk.Frame(self._canvas, bg=C["bg"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._msg_frame, anchor="nw",
        )

        # Keep canvas width in sync with outer frame
        self._msg_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse-wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        # Only scroll when this tab is visible
        try:
            if not self._canvas.winfo_viewable():
                return
        except tk.TclError:
            return
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _scroll_to_bottom(self) -> None:
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    # ── Suggestions ──────────────────────────────────────────────────────

    def _build_suggestions(self) -> None:
        self._sugg_frame = tk.Frame(self, bg=C["bg"], pady=4)
        self._sugg_frame.grid(row=3, column=0, sticky="ew", padx=8)

        tk.Label(
            self._sugg_frame,
            text="Quick questions:",
            bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 8, "italic"),
        ).pack(side=tk.LEFT, padx=(4, 8))

        # Two rows of three buttons
        btn_container = tk.Frame(self._sugg_frame, bg=C["bg"])
        btn_container.pack(side=tk.LEFT, fill=tk.X)

        for idx, (label, prompt) in enumerate(SUGGESTIONS):
            row_idx = idx // 3
            col_idx = idx % 3
            if col_idx == 0:
                row_frame = tk.Frame(btn_container, bg=C["bg"])
                row_frame.pack(anchor="w", pady=1)

            btn = tk.Button(
                row_frame,
                text=label,
                command=lambda p=prompt: self._send_suggestion(p),
                bg=_C_SUGG_BG, fg=_C_SUGG_FG,
                relief=tk.FLAT, padx=10, pady=4,
                font=("Segoe UI", 8), cursor="hand2", borderwidth=1,
                highlightthickness=1,
                highlightbackground=_C_SUGG_BORDER,
            )
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=_C_SUGG_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=_C_SUGG_BG))

    # ── Input bar ────────────────────────────────────────────────────────

    def _build_input_bar(self) -> None:
        bar = tk.Frame(
            self, bg=C["surface"],
            highlightthickness=1, highlightbackground=C["border"],
        )
        bar.grid(row=4, column=0, sticky="ew", padx=8, pady=(4, 4))
        bar.columnconfigure(0, weight=1)

        inner = tk.Frame(bar, bg=C["surface"], pady=8)
        inner.pack(fill=tk.X, padx=10)
        inner.columnconfigure(0, weight=1)

        # Multi-line input (3 rows feels roomy without wasting space)
        self._input_text = tk.Text(
            inner, height=3, wrap=tk.WORD,
            bg=C["surface"], fg=C["text"],
            insertbackground=C["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
            padx=8, pady=6,
        )
        self._input_text.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._input_text.bind("<Return>",       self._on_enter)
        self._input_text.bind("<Shift-Return>", self._on_shift_enter)
        self._input_text.bind("<KeyRelease>",   self._on_key_release)

        # Placeholder text
        self._placeholder = "Ask about your security status, a detected process, risk scores…"
        self._show_placeholder()
        self._input_text.bind("<FocusIn>",  self._on_focus_in)
        self._input_text.bind("<FocusOut>", self._on_focus_out)

        # Send button
        self._btn_send = tk.Button(
            inner,
            text="Send ➤",
            command=self._send_message,
            bg=_C_SEND_ACTIVE, fg="white",
            relief=tk.FLAT, padx=16, pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2", borderwidth=0,
        )
        self._btn_send.grid(row=0, column=1, sticky="ns")
        self._btn_send.bind("<Enter>", lambda e: self._btn_send.config(bg=_C_SEND_HOVER)
                            if not self._busy else None)
        self._btn_send.bind("<Leave>", lambda e: self._btn_send.config(bg=_C_SEND_ACTIVE)
                            if not self._busy else None)

        # Hint text
        tk.Label(
            inner,
            text="Enter to send  •  Shift+Enter for new line",
            bg=C["surface"], fg=C["text_light"],
            font=("Segoe UI", 7, "italic"),
        ).grid(row=1, column=0, sticky="w", padx=(2, 0), pady=(2, 0))

    # ── Status bar ───────────────────────────────────────────────────────

    def _build_status_bar(self) -> None:
        sb = tk.Frame(self, bg=C["surface"],
                      highlightthickness=1, highlightbackground=C["border"])
        sb.grid(row=5, column=0, sticky="ew", padx=0, pady=0)

        inner = tk.Frame(sb, bg=C["surface"])
        inner.pack(fill=tk.X, padx=12, pady=4)

        self._status_var = tk.StringVar(
            value=f"Model: {self._model_display()}  •  Ready"
        )
        tk.Label(
            inner, textvariable=self._status_var,
            bg=C["surface"], fg=C["text_dim"],
            font=("Segoe UI", 8), anchor="w",
        ).pack(side=tk.LEFT)

        self._loading_var = tk.StringVar(value="")
        self._loading_lbl = tk.Label(
            inner, textvariable=self._loading_var,
            bg=C["surface"], fg=_C_LOADING_FG,
            font=("Segoe UI", 8, "italic"),
        )
        self._loading_lbl.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Placeholder helpers
    # ------------------------------------------------------------------

    def _show_placeholder(self) -> None:
        self._input_text.config(fg=C["text_light"])
        self._input_text.delete("1.0", tk.END)
        self._input_text.insert("1.0", self._placeholder)
        self._is_placeholder = True

    def _hide_placeholder(self) -> None:
        if getattr(self, "_is_placeholder", False):
            self._input_text.config(fg=C["text"])
            self._input_text.delete("1.0", tk.END)
            self._is_placeholder = False

    def _on_focus_in(self, _event) -> None:
        self._hide_placeholder()

    def _on_focus_out(self, _event) -> None:
        if not self._input_text.get("1.0", tk.END).strip():
            self._show_placeholder()

    def _on_key_release(self, _event) -> None:
        if getattr(self, "_is_placeholder", False):
            return
        text = self._input_text.get("1.0", tk.END).strip()
        state = tk.NORMAL if (text and not self._busy) else tk.DISABLED
        self._btn_send.config(state=state)

    # ------------------------------------------------------------------
    # Enter key handling
    # ------------------------------------------------------------------

    def _on_enter(self, event) -> str:
        """Enter sends; Shift+Enter inserts newline."""
        self._send_message()
        return "break"   # prevent the default newline insertion

    def _on_shift_enter(self, event) -> None:
        """Shift+Enter — let the default newline through."""
        pass   # do nothing; Text widget handles it normally

    # ------------------------------------------------------------------
    # Welcome message
    # ------------------------------------------------------------------

    def _show_welcome(self) -> None:
        welcome = (
            "👋  Welcome to the AI Security Assistant\n\n"
            "I can help you understand your security dashboard, explain detection "
            "alerts, analyze process risk scores, and give practical advice on "
            "protecting your system from keyloggers.\n\n"
            "I read your live detection data — every response is based on what "
            "the system has actually observed, not on assumptions.\n\n"
            "Use the quick-question buttons below, or type your own question."
        )
        self._append_message("assistant", welcome, style="welcome")

    # ------------------------------------------------------------------
    # Message rendering
    # ------------------------------------------------------------------

    def _append_message(
        self,
        role: str,
        text: str,
        style: str = "normal",
        tag: str = "",
    ) -> None:
        """
        Render a chat bubble in the scrollable canvas.

        role  : "user" | "assistant" | "system"
        style : "normal" | "welcome" | "error" | "loading"
        tag   : optional string identifier stored on the frame for later removal
        """
        outer = tk.Frame(self._msg_frame, bg=C["bg"], pady=3)
        outer.pack(fill=tk.X, padx=8)
        if tag:
            outer._tag = tag  # type: ignore[attr-defined]

        # ── Bubble colors by role / style ────────────────────────────────
        if style == "error":
            bubble_bg = _C_ERROR_BG
            bubble_fg = _C_ERROR_FG
            align = tk.LEFT
            label_text = "⚠ Error"
            label_fg = _C_ERROR_FG
        elif style == "loading":
            bubble_bg = C["bg"]
            bubble_fg = _C_LOADING_FG
            align = tk.LEFT
            label_text = ""
            label_fg = C["text_dim"]
        elif style == "welcome":
            bubble_bg = _C_SYSTEM_BG
            bubble_fg = _C_SYSTEM_FG
            align = tk.LEFT
            label_text = "🤖  AI Security Assistant"
            label_fg = _C_SYSTEM_FG
        elif role == "user":
            bubble_bg = _C_USER_BG
            bubble_fg = _C_USER_FG
            align = tk.RIGHT
            label_text = "You"
            label_fg = C["text_dim"]
        else:   # assistant / normal
            bubble_bg = _C_ASST_BG
            bubble_fg = _C_ASST_FG
            align = tk.LEFT
            label_text = "🤖  Assistant"
            label_fg = C["text_dim"]

        # ── Outer alignment wrapper ──────────────────────────────────────
        wrapper = tk.Frame(outer, bg=C["bg"])
        if align == tk.RIGHT:
            wrapper.pack(anchor="e", padx=(60, 0))
        else:
            wrapper.pack(anchor="w", padx=(0, 60))

        # ── Role label ───────────────────────────────────────────────────
        if label_text:
            tk.Label(
                wrapper, text=label_text,
                bg=C["bg"], fg=label_fg,
                font=("Segoe UI", 7, "bold"),
                anchor="w" if align == tk.LEFT else "e",
            ).pack(fill=tk.X, padx=4, pady=(0, 2))

        # ── Bubble frame ─────────────────────────────────────────────────
        bubble = tk.Frame(
            wrapper, bg=bubble_bg,
            highlightthickness=1,
            highlightbackground=C["border"],
            padx=14, pady=10,
        )
        bubble.pack(fill=tk.X)

        # ── Message body ─────────────────────────────────────────────────
        if style == "loading":
            # Animated dots label
            self._loading_dots_lbl = tk.Label(
                bubble, text="Thinking…",
                bg=bubble_bg, fg=bubble_fg,
                font=("Segoe UI", 9, "italic"),
                anchor="w",
            )
            self._loading_dots_lbl.pack(anchor="w")
            self._animate_loading_dots()
        else:
            # Use a read-only Text widget so text is selectable and wraps
            txt = tk.Text(
                bubble,
                bg=bubble_bg, fg=bubble_fg,
                font=("Segoe UI", 9),
                relief=tk.FLAT, borderwidth=0,
                highlightthickness=0,
                wrap=tk.WORD,
                cursor="arrow",
            )
            txt.insert(tk.END, text)
            txt.config(state=tk.DISABLED)

            # Compute natural height (cap at 40 lines for very long responses)
            line_count = text.count("\n") + 1
            height = min(max(line_count, 2), 40)
            txt.config(height=height)
            txt.pack(fill=tk.X, expand=True)

            # ── Copy button (assistant messages only) ────────────────────
            if role == "assistant" and style not in ("error", "loading", "welcome"):
                self._add_copy_button(wrapper, bubble, text)

        # ── Timestamp ────────────────────────────────────────────────────
        if style not in ("loading",):
            ts = time.strftime("%H:%M")
            tk.Label(
                wrapper, text=ts,
                bg=C["bg"], fg=C["text_light"],
                font=("Segoe UI", 7),
                anchor="e" if align == tk.RIGHT else "w",
            ).pack(fill=tk.X, padx=4, pady=(2, 0))

        self._msg_count += 1
        self._scroll_to_bottom()
        return outer   # type: ignore[return-value]

    def _add_copy_button(
        self,
        wrapper: tk.Frame,
        bubble: tk.Frame,
        text: str,
    ) -> None:
        """Small 'Copy' button that appears beneath assistant bubbles."""
        action_bar = tk.Frame(wrapper, bg=C["bg"])
        action_bar.pack(anchor="w", padx=4, pady=(2, 0))

        def _do_copy():
            try:
                self.clipboard_clear()
                self.clipboard_append(text)
                copy_btn.config(text="✓ Copied")
                self.after(2000, lambda: copy_btn.config(text="⧉ Copy"))
            except tk.TclError:
                pass

        copy_btn = tk.Button(
            action_bar, text="⧉ Copy",
            command=_do_copy,
            bg=C["bg"], fg=C["text_dim"],
            relief=tk.FLAT, padx=6, pady=2,
            font=("Segoe UI", 7), cursor="hand2",
            borderwidth=0,
        )
        copy_btn.pack(side=tk.LEFT)
        copy_btn.bind("<Enter>", lambda e: copy_btn.config(fg=C["accent"]))
        copy_btn.bind("<Leave>", lambda e: copy_btn.config(fg=C["text_dim"]))

    # ── Loading animation ────────────────────────────────────────────────

    def _animate_loading_dots(self, _step: int = 0) -> None:
        """Cycle the 'Thinking…' label while the API call is in flight."""
        frames = ["Thinking·", "Thinking··", "Thinking···", "Thinking·"]
        if not self._busy:
            return
        try:
            if hasattr(self, "_loading_dots_lbl") and self._loading_dots_lbl.winfo_exists():
                self._loading_dots_lbl.config(text=frames[_step % len(frames)])
                self.after(400, lambda: self._animate_loading_dots(_step + 1))
        except tk.TclError:
            pass

    def _remove_loading_bubble(self) -> None:
        """Remove the 'Thinking…' bubble once the response arrives."""
        for child in self._msg_frame.winfo_children():
            if getattr(child, "_tag", None) == "_loading":
                child.destroy()
                break
        self._on_frame_configure()

    # ------------------------------------------------------------------
    # Sending messages
    # ------------------------------------------------------------------

    def _get_input_text(self) -> str:
        raw = self._input_text.get("1.0", tk.END)
        if getattr(self, "_is_placeholder", False):
            return ""
        return raw.strip()

    def _clear_input(self) -> None:
        self._input_text.delete("1.0", tk.END)
        self._show_placeholder()
        self._btn_send.config(state=tk.DISABLED)

    def _send_suggestion(self, prompt: str) -> None:
        if self._busy:
            return
        self._hide_placeholder()
        self._input_text.delete("1.0", tk.END)
        self._input_text.insert("1.0", prompt)
        self._send_message()

    def _send_message(self) -> None:
        if self._busy:
            return

        text = self._get_input_text()
        if not text:
            return

        # Guard: no service attached
        if self._svc is None:
            self._append_message(
                "assistant",
                "The AI chat service is not initialised. Please restart the application.",
                style="error",
            )
            return

        # Render user bubble
        self._append_message("user", text)
        self._clear_input()
        self._set_busy(True)

        # Render loading bubble
        self._append_message("assistant", "", style="loading", tag="_loading")

        # Dispatch to background thread via service
        self._svc.send_message(
            user_text=text,
            result_callback=self._on_response_threadsafe,
            include_context=True,
        )

    def _on_response_threadsafe(self, response: "ChatResponse") -> None:
        """Called from the AIChatService worker thread — must not touch widgets directly."""
        self.after(0, lambda: self._on_response(response))

    def _on_response(self, response: "ChatResponse") -> None:
        """Called on the main thread after the API returns."""
        self._remove_loading_bubble()
        self._set_busy(False)

        if response.success:
            self._append_message("assistant", response.text)
            self._status_var.set(
                f"Model: {self._model_display()}  •  "
                f"Last reply: {time.strftime('%H:%M:%S')}"
            )
        else:
            self._append_message("assistant", response.text, style="error")
            self._status_var.set(
                f"Model: {self._model_display()}  •  "
                f"Error: {response.error_code or 'unknown'}"
            )

    # ------------------------------------------------------------------
    # Clear chat
    # ------------------------------------------------------------------

    def _clear_chat(self) -> None:
        if self._busy:
            return
        # Destroy all message bubbles
        for child in self._msg_frame.winfo_children():
            child.destroy()
        self._msg_count = 0
        if self._svc is not None:
            self._svc.clear_history()
        self._show_welcome()
        self._status_var.set(f"Model: {self._model_display()}  •  Chat cleared")

    # ------------------------------------------------------------------
    # Busy state
    # ------------------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            self._btn_send.config(
                state=tk.DISABLED,
                bg=_C_SEND_DIS,
                text="Sending…",
            )
            self._loading_var.set("⏳ Waiting for Gemma…")
        else:
            self._btn_send.config(
                state=tk.NORMAL,
                bg=_C_SEND_ACTIVE,
                text="Send ➤",
            )
            self._loading_var.set("")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _model_display(self) -> str:
        return "gemma-4-31b-it  (Gemini API)"


# ---------------------------------------------------------------------------
# Public alias used by dashboard.py
# ---------------------------------------------------------------------------
AIChatTab = _AIChatTab
