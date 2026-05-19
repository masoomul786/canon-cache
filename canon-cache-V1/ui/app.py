"""
CanonCache — Main Application Window
Professional research GUI for KV-cache canonicalization benchmarking.
"""

import os
import sys
import json
import time
import threading
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Make sure imports resolve from project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from ui.theme import *
from ui.widgets import (
    StatusDot, Card, MetricCard, StyledButton,
    ProgressBar, Separator, ScrolledText, SectionLabel
)
from core.lm_studio import LMStudioClient
from core.benchmark import (
    BenchmarkRunner, BenchmarkReport,
    export_report_json, export_report_csv
)


DATA_PATH = ROOT / "data" / "sample_clusters.jsonl"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR NAV
# ─────────────────────────────────────────────────────────────────────────────

class Sidebar(tk.Frame):
    ITEMS = [
        ("🏠", "Dashboard"),
        ("⚡", "Benchmark"),
        ("💬", "Chat"),
        ("📊", "Results"),
        ("⚙️", "Settings"),
    ]

    def __init__(self, parent, on_select, **kwargs):
        super().__init__(parent, bg=BG_SURFACE, width=SIDEBAR_W, **kwargs)
        self.pack_propagate(False)
        self._on_select = on_select
        self._buttons: dict[str, tk.Button] = {}
        self._active = "Dashboard"
        self._build()

    def _build(self):
        # Logo area
        logo_frame = tk.Frame(self, bg=BG_SURFACE, pady=PAD_LG)
        logo_frame.pack(fill=tk.X)
        tk.Label(logo_frame, text="CanonCache",
                 font=("Segoe UI", 15, "bold"), fg=ACCENT_BLUE, bg=BG_SURFACE).pack()
        tk.Label(logo_frame, text="KV-Cache Research Tool",
                 font=FONT_SANS_SM, fg=TEXT_SECONDARY, bg=BG_SURFACE).pack()

        Separator(self).pack(fill=tk.X, padx=PAD)

        # Nav items
        nav_frame = tk.Frame(self, bg=BG_SURFACE, pady=PAD_SM)
        nav_frame.pack(fill=tk.X)

        for icon, name in self.ITEMS:
            btn = tk.Button(
                nav_frame,
                text=f"  {icon}  {name}",
                anchor="w",
                font=FONT_SANS,
                fg=TEXT_SECONDARY,
                bg=BG_SURFACE,
                activeforeground=TEXT_PRIMARY,
                activebackground=BG_HOVER,
                relief="flat",
                bd=0,
                pady=10,
                padx=PAD,
                cursor="hand2",
                command=lambda n=name: self.select(n),
            )
            btn.pack(fill=tk.X, padx=PAD_SM)
            self._buttons[name] = btn

        self.select("Dashboard")

        # Bottom: connection status
        self._conn_frame = tk.Frame(self, bg=BG_SURFACE)
        self._conn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=PAD, pady=PAD)
        Separator(self._conn_frame).pack(fill=tk.X, pady=(0, PAD_SM))
        row = tk.Frame(self._conn_frame, bg=BG_SURFACE)
        row.pack(fill=tk.X)
        self._dot = StatusDot(row)
        self._dot.pack(side=tk.LEFT, padx=(0, 6))
        self._status_lbl = tk.Label(row, text="Disconnected",
                                     font=FONT_SANS_SM, fg=TEXT_SECONDARY, bg=BG_SURFACE)
        self._status_lbl.pack(side=tk.LEFT)
        self._model_lbl = tk.Label(self._conn_frame, text="",
                                    font=FONT_SANS_SM, fg=TEXT_DISABLED, bg=BG_SURFACE,
                                    wraplength=SIDEBAR_W - PAD * 2, justify="left")
        self._model_lbl.pack(fill=tk.X, pady=(2, 0))

    def select(self, name: str):
        for n, btn in self._buttons.items():
            btn.config(
                fg=TEXT_PRIMARY if n == name else TEXT_SECONDARY,
                bg=BG_RAISED if n == name else BG_SURFACE,
            )
        self._active = name
        self._on_select(name)

    def set_connection(self, connected: bool, model: str = ""):
        if connected:
            self._dot.set_color(ACCENT_GREEN)
            self._status_lbl.config(text="Connected", fg=ACCENT_GREEN)
            self._model_lbl.config(text=model[:40] if model else "", fg=TEXT_SECONDARY)
        else:
            self._dot.set_color(ACCENT_RED)
            self._status_lbl.config(text="Disconnected", fg=ACCENT_RED)
            self._model_lbl.config(text="")


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD TAB
# ─────────────────────────────────────────────────────────────────────────────

class DashboardTab(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_DEEP, **kwargs)
        self.app = app
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_DEEP, pady=PAD_LG)
        hdr.pack(fill=tk.X, padx=PAD_LG)
        tk.Label(hdr, text="CanonCache Research Dashboard",
                 font=FONT_TITLE, fg=TEXT_PRIMARY, bg=BG_DEEP).pack(anchor="w")
        tk.Label(hdr, text="Semantic KV-Cache Canonicalization Benchmark for LLM Inference Efficiency",
                 font=FONT_SUBTITLE, fg=TEXT_SECONDARY, bg=BG_DEEP).pack(anchor="w", pady=(2, 0))
        Separator(self).pack(fill=tk.X, padx=PAD_LG)

        # Metrics row
        metrics_frame = tk.Frame(self, bg=BG_DEEP, pady=PAD_LG)
        metrics_frame.pack(fill=tk.X, padx=PAD_LG)

        self.m_model    = MetricCard(metrics_frame, "Active Model", "—")
        self.m_clusters = MetricCard(metrics_frame, "Benchmark Clusters", "0")
        self.m_runs     = MetricCard(metrics_frame, "Benchmark Runs", "0")
        self.m_hit_rate = MetricCard(metrics_frame, "Cache Hit Rate (Canonical)", "—", ACCENT_GREEN)

        for m in [self.m_model, self.m_clusters, self.m_runs, self.m_hit_rate]:
            m.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, PAD_SM))

        Separator(self).pack(fill=tk.X, padx=PAD_LG, pady=(0, PAD))

        # Two-column layout
        cols = tk.Frame(self, bg=BG_DEEP)
        cols.pack(fill=tk.BOTH, expand=True, padx=PAD_LG, pady=(0, PAD_LG))

        # Left: About
        left = tk.Frame(cols, bg=BG_SURFACE,
                        highlightbackground=BG_BORDER, highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PAD_SM))

        tk.Label(left, text="About CanonCache", font=FONT_BOLD,
                 fg=ACCENT_BLUE, bg=BG_SURFACE, pady=PAD).pack(anchor="w", padx=PAD)
        Separator(left).pack(fill=tk.X)
        about_text = (
            "CanonCache is a research tool for evaluating semantic KV-cache "
            "canonicalization as a strategy to improve inference efficiency in "
            "multi-tenant LLM serving environments.\n\n"
            "Core hypothesis: By rewriting semantically equivalent but "
            "syntactically diverse prompts into a canonical form, we can "
            "dramatically increase prefix cache hit rates — reducing GPU-hours "
            "per request without degrading output quality.\n\n"
            "This tool benchmarks:\n"
            "  • Raw vs. canonical prompt latency\n"
            "  • Simulated prefix cache hit rates\n"
            "  • Semantic similarity of responses\n"
            "  • Token usage efficiency\n"
            "  • Quality score preservation\n\n"
            "Based on: SemCache — Semantic KV-Cache Merging for Multi-Tenant LLM Inference"
        )
        tk.Label(left, text=about_text, font=FONT_SANS, fg=TEXT_SECONDARY,
                 bg=BG_SURFACE, justify="left", wraplength=380,
                 pady=PAD, padx=PAD).pack(anchor="w")

        # Right: Quick actions
        right = tk.Frame(cols, bg=BG_SURFACE,
                         highlightbackground=BG_BORDER, highlightthickness=1)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(right, text="Quick Actions", font=FONT_BOLD,
                 fg=ACCENT_BLUE, bg=BG_SURFACE, pady=PAD).pack(anchor="w", padx=PAD)
        Separator(right).pack(fill=tk.X)

        btn_cfg = [
            ("⚡  Connect to LM Studio", "primary", lambda: self.app.sidebar.select("Settings")),
            ("▶  Run Full Benchmark", "success", lambda: self.app.sidebar.select("Benchmark")),
            ("💬  Open Chat Interface", "ghost", lambda: self.app.sidebar.select("Chat")),
            ("📊  View Last Results", "secondary", lambda: self.app.sidebar.select("Results")),
        ]
        for text, style, cmd in btn_cfg:
            StyledButton(right, text=text, style=style, command=cmd).pack(
                fill=tk.X, padx=PAD, pady=4
            )

        Separator(right).pack(fill=tk.X, pady=PAD_SM)

        tk.Label(right, text="RESEARCH PAPER CONTEXT",
                 font=FONT_SANS_SM, fg=TEXT_DISABLED, bg=BG_SURFACE).pack(anchor="w", padx=PAD)
        tk.Label(right,
                 text="SemCache: Semantic KV-Cache Merging\nfor Multi-Tenant LLM Inference\n\nTarget venue: MLSys / OSDI / SOSP",
                 font=FONT_SANS_SM, fg=TEXT_SECONDARY, bg=BG_SURFACE,
                 justify="left", pady=PAD_SM, padx=PAD).pack(anchor="w")

    def refresh(self, model: str, cluster_count: int, run_count: int, hit_rate: str):
        self.m_model.update(model[:30] if model else "—")
        self.m_clusters.update(str(cluster_count))
        self.m_runs.update(str(run_count))
        self.m_hit_rate.update(hit_rate, ACCENT_GREEN if hit_rate != "—" else TEXT_SECONDARY)


# ─────────────────────────────────────────────────────────────────────────────
#  BENCHMARK TAB
# ─────────────────────────────────────────────────────────────────────────────

class BenchmarkTab(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_DEEP, **kwargs)
        self.app = app
        self._runner: BenchmarkRunner | None = None
        self._thread: threading.Thread | None = None
        self._last_report: BenchmarkReport | None = None
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_DEEP, pady=PAD_LG)
        hdr.pack(fill=tk.X, padx=PAD_LG)
        tk.Label(hdr, text="Benchmark Runner", font=FONT_TITLE,
                 fg=TEXT_PRIMARY, bg=BG_DEEP).pack(anchor="w")
        tk.Label(hdr, text="Evaluate raw vs. canonical prompt performance with your LM Studio model",
                 font=FONT_SUBTITLE, fg=TEXT_SECONDARY, bg=BG_DEEP).pack(anchor="w")
        Separator(self).pack(fill=tk.X, padx=PAD_LG)

        # Config row
        config = tk.Frame(self, bg=BG_DEEP, pady=PAD)
        config.pack(fill=tk.X, padx=PAD_LG)

        # Dataset path
        ds_frame = tk.Frame(config, bg=BG_SURFACE,
                             highlightbackground=BG_BORDER, highlightthickness=1)
        ds_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, PAD_SM))
        tk.Label(ds_frame, text="Dataset", font=FONT_SANS_SM,
                 fg=TEXT_SECONDARY, bg=BG_SURFACE).pack(anchor="w", padx=PAD, pady=(PAD_SM, 0))
        self._ds_var = tk.StringVar(value=str(DATA_PATH))
        ds_entry = tk.Entry(ds_frame, textvariable=self._ds_var,
                             font=FONT_MONO_SM, fg=TEXT_PRIMARY, bg=BG_RAISED,
                             insertbackground=ACCENT_BLUE, relief="flat", width=40)
        ds_entry.pack(side=tk.LEFT, padx=PAD, pady=PAD_SM)
        StyledButton(ds_frame, "Browse", command=self._browse, style="secondary").pack(
            side=tk.LEFT, padx=(0, PAD))

        # Max clusters
        mc_frame = tk.Frame(config, bg=BG_SURFACE,
                             highlightbackground=BG_BORDER, highlightthickness=1)
        mc_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, PAD_SM))
        tk.Label(mc_frame, text="Clusters", font=FONT_SANS_SM,
                 fg=TEXT_SECONDARY, bg=BG_SURFACE).pack(anchor="w", padx=PAD, pady=(PAD_SM, 0))
        self._max_clusters = tk.IntVar(value=10)
        spin = tk.Spinbox(mc_frame, from_=1, to=100, textvariable=self._max_clusters,
                          font=FONT_SANS, fg=TEXT_PRIMARY, bg=BG_RAISED,
                          buttonbackground=BG_BORDER, relief="flat", width=5)
        spin.pack(padx=PAD, pady=PAD_SM)

        # Raw per cluster
        rpc_frame = tk.Frame(config, bg=BG_SURFACE,
                              highlightbackground=BG_BORDER, highlightthickness=1)
        rpc_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, PAD_SM))
        tk.Label(rpc_frame, text="Raw/Cluster", font=FONT_SANS_SM,
                 fg=TEXT_SECONDARY, bg=BG_SURFACE).pack(anchor="w", padx=PAD, pady=(PAD_SM, 0))
        self._raw_per = tk.IntVar(value=2)
        spin2 = tk.Spinbox(rpc_frame, from_=1, to=4, textvariable=self._raw_per,
                           font=FONT_SANS, fg=TEXT_PRIMARY, bg=BG_RAISED,
                           buttonbackground=BG_BORDER, relief="flat", width=5)
        spin2.pack(padx=PAD, pady=PAD_SM)

        # Action buttons
        btn_frame = tk.Frame(config, bg=BG_DEEP)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=PAD)
        self._run_btn = StyledButton(btn_frame, "▶  Run Benchmark", command=self._run, style="success")
        self._run_btn.pack(pady=(PAD_SM, 4))
        self._stop_btn = StyledButton(btn_frame, "⏹  Stop", command=self._stop, style="danger")
        self._stop_btn.pack()
        self._stop_btn.config(state=tk.DISABLED)

        # Progress
        prog_frame = tk.Frame(self, bg=BG_DEEP, padx=PAD_LG)
        prog_frame.pack(fill=tk.X, padx=PAD_LG)
        self._progress_lbl = tk.Label(prog_frame, text="Ready",
                                       font=FONT_SANS_SM, fg=TEXT_SECONDARY, bg=BG_DEEP)
        self._progress_lbl.pack(anchor="w", pady=(0, 4))
        self._progress_bar = ProgressBar(prog_frame)
        self._progress_bar.pack(fill=tk.X)

        Separator(self).pack(fill=tk.X, padx=PAD_LG, pady=PAD)

        # Live metrics row
        metrics_frame = tk.Frame(self, bg=BG_DEEP)
        metrics_frame.pack(fill=tk.X, padx=PAD_LG, pady=(0, PAD))

        self._m_hit    = MetricCard(metrics_frame, "Cache Hit Rate (Canonical)", "—", ACCENT_GREEN)
        self._m_lat    = MetricCard(metrics_frame, "Latency Δ (Raw→Canonical)", "—", ACCENT_BLUE)
        self._m_tok    = MetricCard(metrics_frame, "Token Reduction", "—", ACCENT_AMBER)
        self._m_qual   = MetricCard(metrics_frame, "Quality Score", "—", ACCENT_PURPLE)
        self._m_sim    = MetricCard(metrics_frame, "Avg Semantic Similarity", "—")

        for m in [self._m_hit, self._m_lat, self._m_tok, self._m_qual, self._m_sim]:
            m.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, PAD_SM))

        # Log output
        tk.Label(self, text="Execution Log", font=FONT_BOLD,
                 fg=TEXT_SECONDARY, bg=BG_DEEP).pack(anchor="w", padx=PAD_LG)
        self._log = ScrolledText(self, height=18)
        self._log.pack(fill=tk.BOTH, expand=True, padx=PAD_LG, pady=(PAD_SM, PAD_LG))

        # Export row
        export_row = tk.Frame(self, bg=BG_DEEP)
        export_row.pack(fill=tk.X, padx=PAD_LG, pady=(0, PAD_LG))
        StyledButton(export_row, "📥  Export JSON", command=self._export_json, style="secondary").pack(side=tk.LEFT, padx=(0, PAD_SM))
        StyledButton(export_row, "📥  Export CSV", command=self._export_csv, style="secondary").pack(side=tk.LEFT)

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("JSONL", "*.jsonl"), ("All", "*.*")])
        if path:
            self._ds_var.set(path)

    def _run(self):
        if not self.app.client.base_url:
            messagebox.showerror("Not Connected",
                                  "Please connect to LM Studio first (Settings tab).")
            return
        ds = self._ds_var.get()
        if not Path(ds).exists():
            messagebox.showerror("File Not Found", f"Dataset not found:\n{ds}")
            return
        self._log.clear()
        self._progress_bar.reset()
        self._run_btn.config(state=tk.DISABLED)
        self._stop_btn.config(state=tk.NORMAL)
        self._runner = BenchmarkRunner(self.app.client, ds)
        self._runner.load_clusters()
        self._log_line(f"Loaded {len(self._runner.clusters)} clusters from {ds}\n", "info")
        self._log_line(f"Model: {self.app.client.active_model}\n", "info")
        self._log_line(f"Running {self._max_clusters.get()} clusters × {self._raw_per.get()} raw + 1 canonical each\n", "label")
        self._log_line("─" * 60 + "\n", "muted")

        def worker():
            report = self._runner.run(
                max_clusters=self._max_clusters.get(),
                max_raw_per_cluster=self._raw_per.get(),
                progress_cb=self._on_progress,
            )
            self._last_report = report
            self.after(0, self._on_done, report)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def _stop(self):
        if self._runner:
            self._runner.stop()
        self._stop_btn.config(state=tk.DISABLED)
        self._progress_lbl.config(text="Stopping…")

    def _on_progress(self, current: int, total: int, msg: str):
        self.after(0, self._update_progress, current, total, msg)

    def _update_progress(self, current: int, total: int, msg: str):
        pct = current / total if total > 0 else 0
        self._progress_bar.set(pct)
        self._progress_lbl.config(
            text=f"{current}/{total}  ({pct:.0%})  {msg}"
        )
        tag = "prompt_raw" if "Raw:" in msg else "prompt_can" if "Canonical:" in msg else "info"
        self._log_line(f"[{current:>3}/{total}] {msg}\n", tag)

    def _on_done(self, report: BenchmarkReport):
        self._run_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)
        self._progress_bar.set(1.0)
        self._progress_lbl.config(text=f"Done — {report.total_prompts} prompts in {report.total_clusters} clusters")

        # Update metrics
        hit_pct = f"{report.simulated_cache_hit_rate_canonical:.0%}"
        lat_delta = (
            f"{report.overall_latency_improvement_pct:+.1f}%"
            if report.overall_latency_improvement_pct != 0 else "—"
        )
        tok_red = f"{report.token_reduction_pct:.1f}%" if report.token_reduction_pct else "—"
        qual = f"{report.avg_quality_score:.3f}" if report.avg_quality_score else "—"
        sim = f"{report.avg_semantic_similarity:.3f}" if report.avg_semantic_similarity else "—"

        self._m_hit.update(hit_pct, ACCENT_GREEN)
        self._m_lat.update(lat_delta, ACCENT_GREEN if report.overall_latency_improvement_pct > 0 else ACCENT_RED)
        self._m_tok.update(tok_red, ACCENT_AMBER)
        self._m_qual.update(qual, ACCENT_PURPLE)
        self._m_sim.update(sim)

        self._log_line("\n" + "═" * 60 + "\n", "muted")
        self._log_line("  BENCHMARK SUMMARY\n", "heading")
        self._log_line(f"  Run ID:          {report.run_id}\n", "label")
        self._log_line(f"  Model:           {report.model_id}\n", "value")
        self._log_line(f"  Clusters:        {report.total_clusters}\n", "value")
        self._log_line(f"  Total Prompts:   {report.total_prompts}\n", "value")
        self._log_line(f"  Cache Hit Rate (Canonical): {hit_pct}\n", "good")
        self._log_line(f"  Cache Hit Rate (Raw):       {report.simulated_cache_hit_rate_raw:.0%}\n", "warn")
        self._log_line(f"  Avg Raw Latency:     {report.avg_latency_raw_ms:.1f} ms\n", "value")
        self._log_line(f"  Avg Canonical Lat:   {report.avg_latency_canonical_ms:.1f} ms\n", "value")
        self._log_line(f"  Latency Δ:           {lat_delta}\n", "good")
        self._log_line(f"  Token Reduction:     {tok_red}\n", "good")
        self._log_line(f"  Avg Semantic Sim:    {sim}\n", "info")
        self._log_line(f"  Avg Quality Score:   {qual}\n", "info")
        self._log_line(f"  Errors:              {report.errors}\n", "bad" if report.errors else "muted")
        self._log_line("═" * 60 + "\n", "muted")

        # Auto-save
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        auto_path = RESULTS_DIR / f"report_{report.run_id}_{ts}.json"
        export_report_json(report, str(auto_path))
        self._log_line(f"\nAuto-saved: {auto_path}\n", "muted")

        self.app.on_benchmark_done(report)

    def _log_line(self, text: str, tag: str = ""):
        self._log.append(text, tag)

    def _export_json(self):
        if not self._last_report:
            messagebox.showinfo("No Results", "Run a benchmark first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"report_{self._last_report.run_id}.json",
        )
        if path:
            export_report_json(self._last_report, path)
            messagebox.showinfo("Exported", f"JSON report saved:\n{path}")

    def _export_csv(self):
        if not self._last_report:
            messagebox.showinfo("No Results", "Run a benchmark first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"report_{self._last_report.run_id}.csv",
        )
        if path:
            export_report_csv(self._last_report, path)
            messagebox.showinfo("Exported", f"CSV report saved:\n{path}")


# ─────────────────────────────────────────────────────────────────────────────
#  CHAT TAB
# ─────────────────────────────────────────────────────────────────────────────

class ChatTab(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_DEEP, **kwargs)
        self.app = app
        self._history: list[dict] = []
        self._streaming = False
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_DEEP, pady=PAD_LG)
        hdr.pack(fill=tk.X, padx=PAD_LG)
        tk.Label(hdr, text="Chat Interface", font=FONT_TITLE,
                 fg=TEXT_PRIMARY, bg=BG_DEEP).pack(side=tk.LEFT, anchor="w")
        StyledButton(hdr, "Clear", command=self._clear, style="secondary").pack(side=tk.RIGHT)
        tk.Label(hdr, text="Test your model directly — useful for qualitative evaluation",
                 font=FONT_SUBTITLE, fg=TEXT_SECONDARY, bg=BG_DEEP).pack(anchor="w")
        Separator(self).pack(fill=tk.X, padx=PAD_LG)

        # System prompt
        sys_row = tk.Frame(self, bg=BG_DEEP, padx=PAD_LG, pady=PAD_SM)
        sys_row.pack(fill=tk.X)
        tk.Label(sys_row, text="System Prompt:", font=FONT_BOLD,
                 fg=TEXT_SECONDARY, bg=BG_DEEP).pack(side=tk.LEFT, padx=(0, PAD_SM))
        self._sys_var = tk.StringVar(
            value="You are a helpful AI research assistant. Provide accurate, detailed answers."
        )
        sys_entry = tk.Entry(sys_row, textvariable=self._sys_var,
                              font=FONT_MONO_SM, fg=TEXT_SECONDARY, bg=BG_RAISED,
                              insertbackground=ACCENT_BLUE, relief="flat")
        sys_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Chat display
        self._chat_display = tk.Text(
            self,
            font=FONT_SANS,
            fg=TEXT_PRIMARY, bg=BG_SURFACE,
            insertbackground=ACCENT_BLUE,
            selectbackground=ACCENT_BLUE,
            selectforeground=TEXT_PRIMARY,
            relief="flat", bd=0,
            padx=PAD_LG, pady=PAD,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        from ui.theme import apply_tags
        apply_tags(self._chat_display)
        sb = tk.Scrollbar(self, command=self._chat_display.yview,
                          bg=BG_RAISED, troughcolor=BG_DEEP,
                          activebackground=BG_HOVER, relief="flat", width=10)
        self._chat_display.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._chat_display.pack(fill=tk.BOTH, expand=True, padx=(PAD_LG, 0))

        Separator(self).pack(fill=tk.X, padx=PAD_LG, pady=(PAD_SM, 0))

        # Input row
        input_row = tk.Frame(self, bg=BG_DEEP, pady=PAD)
        input_row.pack(fill=tk.X, padx=PAD_LG)

        self._input = tk.Text(
            input_row,
            font=FONT_SANS,
            fg=TEXT_PRIMARY, bg=BG_RAISED,
            insertbackground=ACCENT_BLUE,
            relief="flat", bd=0,
            height=3, wrap=tk.WORD,
            padx=PAD_SM, pady=PAD_SM,
            highlightbackground=BG_BORDER, highlightthickness=1,
        )
        self._input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._input.bind("<Return>", self._on_enter)
        self._input.bind("<Shift-Return>", lambda e: None)  # allow newline

        btn_col = tk.Frame(input_row, bg=BG_DEEP)
        btn_col.pack(side=tk.LEFT, padx=(PAD_SM, 0))
        self._send_btn = StyledButton(btn_col, "Send", command=self._send, style="primary")
        self._send_btn.pack(fill=tk.X, pady=(0, 4))

        # Token / latency display
        self._stats_lbl = tk.Label(self, text="",
                                    font=FONT_SANS_SM, fg=TEXT_DISABLED, bg=BG_DEEP)
        self._stats_lbl.pack(anchor="e", padx=PAD_LG, pady=(0, PAD_SM))

        self._welcome()

    def _welcome(self):
        self._chat_write("\nCanonCache Chat Interface\n", "heading")
        self._chat_write(
            "Connected to your local LM Studio model.\n"
            "Type a message and press Enter (Shift+Enter for newline).\n\n"
            "Tip: Try sending semantically similar prompts to compare outputs!\n\n",
            "system_msg"
        )

    def _on_enter(self, event):
        if not event.state & 0x1:  # Shift not held
            self._send()
            return "break"

    def _send(self):
        if self._streaming:
            return
        if not self.app.client.base_url:
            messagebox.showerror("Not Connected", "Please connect to LM Studio first.")
            return
        text = self._input.get("1.0", tk.END).strip()
        if not text:
            return
        self._input.delete("1.0", tk.END)
        self._display_message("user", text)
        self._history.append({"role": "user", "content": text})

        # Add system message if history is fresh
        messages = []
        sys_txt = self._sys_var.get().strip()
        if sys_txt:
            messages.append({"role": "system", "content": sys_txt})
        messages.extend(self._history)

        self._streaming = True
        self._send_btn.config(state=tk.DISABLED)
        self._chat_write(f"\n  Assistant\n", "assistant_msg")

        t0 = time.perf_counter()
        buffer = []

        def worker():
            for chunk in self.app.client.stream_complete(messages, max_tokens=1024):
                buffer.append(chunk)
                self.after(0, self._append_chunk, chunk)
            elapsed = (time.perf_counter() - t0) * 1000
            full_response = "".join(buffer)
            self._history.append({"role": "assistant", "content": full_response})
            token_estimate = len(full_response.split())
            self.after(0, self._on_stream_done, elapsed, token_estimate)

        threading.Thread(target=worker, daemon=True).start()

    def _append_chunk(self, chunk: str):
        self._chat_display.config(state=tk.NORMAL)
        self._chat_display.insert(tk.END, chunk)
        self._chat_display.see(tk.END)
        self._chat_display.config(state=tk.DISABLED)

    def _on_stream_done(self, latency_ms: float, tokens: int):
        self._streaming = False
        self._send_btn.config(state=tk.NORMAL)
        self._chat_write("\n", "")
        self._stats_lbl.config(
            text=f"~{tokens} tokens  ·  {latency_ms:.0f} ms  ·  {self.app.client.active_model or '—'}"
        )

    def _display_message(self, role: str, text: str):
        self._chat_write("\n", "")
        if role == "user":
            self._chat_write(f"  You\n", "user_msg")
        else:
            self._chat_write(f"  Assistant\n", "assistant_msg")
        self._chat_write(f"  {text}\n", "")

    def _chat_write(self, text: str, tag: str = ""):
        self._chat_display.config(state=tk.NORMAL)
        if tag:
            self._chat_display.insert(tk.END, text, tag)
        else:
            self._chat_display.insert(tk.END, text)
        self._chat_display.see(tk.END)
        self._chat_display.config(state=tk.DISABLED)

    def _clear(self):
        self._history.clear()
        self._chat_display.config(state=tk.NORMAL)
        self._chat_display.delete("1.0", tk.END)
        self._chat_display.config(state=tk.DISABLED)
        self._welcome()


# ─────────────────────────────────────────────────────────────────────────────
#  RESULTS TAB
# ─────────────────────────────────────────────────────────────────────────────

class ResultsTab(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_DEEP, **kwargs)
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG_DEEP, pady=PAD_LG)
        hdr.pack(fill=tk.X, padx=PAD_LG)
        tk.Label(hdr, text="Results Viewer", font=FONT_TITLE,
                 fg=TEXT_PRIMARY, bg=BG_DEEP).pack(anchor="w")
        tk.Label(hdr, text="Detailed cluster-level benchmark results",
                 font=FONT_SUBTITLE, fg=TEXT_SECONDARY, bg=BG_DEEP).pack(anchor="w")
        Separator(self).pack(fill=tk.X, padx=PAD_LG)

        # Load controls
        ctrl = tk.Frame(self, bg=BG_DEEP, padx=PAD_LG, pady=PAD_SM)
        ctrl.pack(fill=tk.X)
        StyledButton(ctrl, "📂  Load JSON Report", command=self._load_file, style="secondary").pack(side=tk.LEFT)
        StyledButton(ctrl, "↻  Refresh (Last Run)", command=self._refresh_last, style="ghost").pack(side=tk.LEFT, padx=PAD_SM)
        self._loaded_lbl = tk.Label(ctrl, text="No report loaded",
                                     font=FONT_SANS_SM, fg=TEXT_DISABLED, bg=BG_DEEP)
        self._loaded_lbl.pack(side=tk.LEFT, padx=PAD_SM)

        # Left: cluster list, Right: detail pane
        panes = tk.Frame(self, bg=BG_DEEP)
        panes.pack(fill=tk.BOTH, expand=True, padx=PAD_LG, pady=(PAD_SM, PAD_LG))

        # Cluster list
        list_frame = tk.Frame(panes, bg=BG_SURFACE,
                               highlightbackground=BG_BORDER, highlightthickness=1, width=260)
        list_frame.pack(side=tk.LEFT, fill=tk.Y)
        list_frame.pack_propagate(False)

        tk.Label(list_frame, text="Clusters", font=FONT_BOLD,
                 fg=TEXT_SECONDARY, bg=BG_SURFACE, pady=PAD_SM).pack(anchor="w", padx=PAD)
        Separator(list_frame).pack(fill=tk.X)

        lb_frame = tk.Frame(list_frame, bg=BG_SURFACE)
        lb_frame.pack(fill=tk.BOTH, expand=True)
        lb_sb = tk.Scrollbar(lb_frame, bg=BG_RAISED, relief="flat", width=8)
        lb_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._cluster_lb = tk.Listbox(
            lb_frame,
            font=FONT_MONO_SM,
            fg=TEXT_PRIMARY, bg=BG_SURFACE,
            selectbackground=ACCENT_BLUE,
            selectforeground=TEXT_PRIMARY,
            relief="flat", bd=0,
            activestyle="none",
            yscrollcommand=lb_sb.set,
        )
        lb_sb.config(command=self._cluster_lb.yview)
        self._cluster_lb.pack(fill=tk.BOTH, expand=True)
        self._cluster_lb.bind("<<ListboxSelect>>", self._on_cluster_select)

        # Detail pane
        self._detail = ScrolledText(panes, height=30, font=FONT_MONO_SM)
        self._detail.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(PAD_SM, 0))

        self._current_report: BenchmarkReport | None = None

    def load_report(self, report: BenchmarkReport):
        self._current_report = report
        self._cluster_lb.delete(0, tk.END)
        for cr in report.cluster_results:
            sim_tag = "✓" if cr.avg_semantic_similarity > 0.4 else "~"
            self._cluster_lb.insert(tk.END,
                                     f" {sim_tag} {cr.cluster_id}  {cr.topic[:22]}")
        self._loaded_lbl.config(
            text=f"Run {report.run_id}  ·  {report.total_clusters} clusters",
            fg=TEXT_SECONDARY
        )
        self._show_summary(report)

    def _show_summary(self, report: BenchmarkReport):
        d = self._detail
        d.clear()
        d.append("BENCHMARK REPORT SUMMARY\n", "heading")
        d.append(f"Run ID:    {report.run_id}\n", "mono")
        d.append(f"Model:     {report.model_id}\n", "mono")
        d.append(f"Timestamp: {report.timestamp}\n", "mono")
        d.append(f"Clusters:  {report.total_clusters}  ·  Prompts: {report.total_prompts}\n\n", "mono")

        d.append("CACHE EFFICIENCY\n", "subheading")
        d.append(f"  Raw prefix hit rate:       {report.simulated_cache_hit_rate_raw:.1%}\n", "warn")
        d.append(f"  Canonical prefix hit rate: {report.simulated_cache_hit_rate_canonical:.1%}\n", "good")
        hit_lift = (report.simulated_cache_hit_rate_canonical - report.simulated_cache_hit_rate_raw) * 100
        d.append(f"  Cache hit rate lift:       +{hit_lift:.1f} pp\n\n", "good")

        d.append("LATENCY\n", "subheading")
        d.append(f"  Avg raw latency:           {report.avg_latency_raw_ms:.1f} ms\n", "value")
        d.append(f"  Avg canonical latency:     {report.avg_latency_canonical_ms:.1f} ms\n", "value")
        d.append(f"  Improvement:               {report.overall_latency_improvement_pct:+.1f}%\n\n", "good")

        d.append("TOKEN EFFICIENCY\n", "subheading")
        d.append(f"  Total tokens (raw):        {report.total_tokens_raw}\n", "value")
        d.append(f"  Total tokens (canonical):  {report.total_tokens_canonical}\n", "value")
        d.append(f"  Token reduction:           {report.token_reduction_pct:.1f}%\n\n", "good")

        d.append("QUALITY\n", "subheading")
        d.append(f"  Avg semantic similarity:   {report.avg_semantic_similarity:.4f}\n", "info")
        d.append(f"  Avg quality score:         {report.avg_quality_score:.4f}\n", "info")
        d.append(f"  Errors:                    {report.errors}\n\n", "bad" if report.errors else "muted")
        d.append("Click a cluster on the left for per-cluster details.\n", "muted")

    def _on_cluster_select(self, event):
        sel = self._cluster_lb.curselection()
        if not sel or not self._current_report:
            return
        idx = sel[0]
        if idx >= len(self._current_report.cluster_results):
            return
        cr = self._current_report.cluster_results[idx]
        d = self._detail
        d.clear()
        d.append(f"CLUSTER: {cr.cluster_id}  ·  {cr.topic}\n\n", "heading")
        d.append("CANONICAL PROMPT\n", "subheading")
        d.append(f"  {cr.canonical_prompt}\n\n", "prompt_can")

        d.append("RAW PROMPTS\n", "subheading")
        for rr in cr.raw_results:
            tag = "bad" if rr.error else "prompt_raw"
            d.append(f"  [{rr.prompt_type.upper()}] ", "label")
            d.append(f"{rr.prompt}\n", tag)
            d.append(f"    Latency: {rr.latency_ms:.1f} ms  |  Tokens: {rr.tokens_used}  |  Cache Hit: {rr.cache_hit_simulated}\n", "label")
            if rr.error:
                d.append(f"    ERROR: {rr.error}\n", "bad")
            elif rr.response:
                preview = rr.response[:200] + "..." if len(rr.response) > 200 else rr.response
                d.append(f"    Response: {preview}\n", "muted")
            d.append("\n", "")

        d.append("CANONICAL RESPONSE\n", "subheading")
        if cr.canonical_result:
            cr2 = cr.canonical_result
            d.append(f"  Latency: {cr2.latency_ms:.1f} ms  |  Tokens: {cr2.tokens_used}  |  Cache Hit: {cr2.cache_hit_simulated}\n", "label")
            if cr2.error:
                d.append(f"  ERROR: {cr2.error}\n", "bad")
            elif cr2.response:
                d.append(f"  {cr2.response[:400]}{'...' if len(cr2.response)>400 else ''}\n", "value")

        d.append("\nMETRICS\n", "subheading")
        d.append(f"  Avg Raw Latency:    {cr.avg_raw_latency_ms:.1f} ms\n", "value")
        d.append(f"  Canonical Latency:  {cr.canonical_latency_ms:.1f} ms\n", "value")
        d.append(f"  Latency Δ:          {cr.latency_improvement_pct:+.1f}%\n", "good" if cr.latency_improvement_pct > 0 else "warn")
        d.append(f"  Semantic Similarity:{cr.avg_semantic_similarity:.4f}\n", "info")
        d.append(f"  Quality Score:      {cr.quality_score:.4f}\n", "info")

    def _refresh_last(self):
        if self.app._last_report:
            self.load_report(self.app._last_report)

    def _load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            initialdir=str(RESULTS_DIR),
        )
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            # Reconstruct a lightweight report object for display
            from core.benchmark import BenchmarkReport, ClusterResult, PromptResult
            report = BenchmarkReport(
                run_id=data.get("run_id", "?"),
                model_id=data.get("model_id", "?"),
                timestamp=data.get("timestamp", ""),
                total_clusters=data["summary"]["total_clusters"],
                total_prompts=data["summary"]["total_prompts"],
            )
            s = data["summary"]
            report.avg_latency_raw_ms = s["avg_latency_raw_ms"]
            report.avg_latency_canonical_ms = s["avg_latency_canonical_ms"]
            report.overall_latency_improvement_pct = s["latency_improvement_pct"]
            report.simulated_cache_hit_rate_raw = s["simulated_cache_hit_rate_raw"]
            report.simulated_cache_hit_rate_canonical = s["simulated_cache_hit_rate_canonical"]
            report.avg_semantic_similarity = s["avg_semantic_similarity"]
            report.avg_quality_score = s["avg_quality_score"]
            report.total_tokens_raw = s["total_tokens_raw"]
            report.total_tokens_canonical = s["total_tokens_canonical"]
            report.token_reduction_pct = s["token_reduction_pct"]
            report.errors = s["errors"]

            for c in data.get("clusters", []):
                cr = ClusterResult(
                    cluster_id=c["cluster_id"],
                    topic=c["topic"],
                    canonical_prompt=c["canonical_prompt"],
                )
                cr.avg_raw_latency_ms = c["avg_raw_latency_ms"]
                cr.canonical_latency_ms = c["canonical_latency_ms"]
                cr.latency_improvement_pct = c["latency_improvement_pct"]
                cr.avg_semantic_similarity = c["avg_semantic_similarity"]
                cr.quality_score = c["quality_score"]

                for rp in c.get("raw_prompts", []):
                    cr.raw_results.append(PromptResult(
                        cluster_id=c["cluster_id"], topic=c["topic"],
                        prompt=rp["prompt"], prompt_type="raw",
                        response=rp.get("response_preview", ""),
                        latency_ms=rp["latency_ms"],
                        tokens_used=rp.get("tokens_used", 0),
                        cache_hit_simulated=rp.get("cache_hit", False),
                        error=rp.get("error"),
                    ))

                can = c.get("canonical", {})
                cr.canonical_result = PromptResult(
                    cluster_id=c["cluster_id"], topic=c["topic"],
                    prompt=c["canonical_prompt"], prompt_type="canonical",
                    response=can.get("response_preview", ""),
                    latency_ms=can.get("latency_ms", 0),
                    tokens_used=can.get("tokens_used", 0),
                    cache_hit_simulated=can.get("cache_hit", False),
                    error=can.get("error"),
                )
                report.cluster_results.append(cr)

            self.load_report(report)
        except Exception as e:
            messagebox.showerror("Load Error", str(e))


# ─────────────────────────────────────────────────────────────────────────────
#  SETTINGS TAB
# ─────────────────────────────────────────────────────────────────────────────

class SettingsTab(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_DEEP, **kwargs)
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG_DEEP, pady=PAD_LG)
        hdr.pack(fill=tk.X, padx=PAD_LG)
        tk.Label(hdr, text="Settings & Connection", font=FONT_TITLE,
                 fg=TEXT_PRIMARY, bg=BG_DEEP).pack(anchor="w")
        tk.Label(hdr, text="Configure LM Studio connection and model selection",
                 font=FONT_SUBTITLE, fg=TEXT_SECONDARY, bg=BG_DEEP).pack(anchor="w")
        Separator(self).pack(fill=tk.X, padx=PAD_LG)

        # Connection card
        conn_card = tk.Frame(self, bg=BG_SURFACE,
                              highlightbackground=BG_BORDER, highlightthickness=1)
        conn_card.pack(fill=tk.X, padx=PAD_LG, pady=PAD_LG)

        tk.Label(conn_card, text="LM Studio Connection", font=FONT_BOLD,
                 fg=ACCENT_BLUE, bg=BG_SURFACE, pady=PAD).pack(anchor="w", padx=PAD)
        Separator(conn_card).pack(fill=tk.X)

        # Host / Port
        row1 = tk.Frame(conn_card, bg=BG_SURFACE, pady=PAD_SM)
        row1.pack(fill=tk.X, padx=PAD)

        tk.Label(row1, text="Host:", font=FONT_BOLD, fg=TEXT_SECONDARY,
                 bg=BG_SURFACE, width=10, anchor="w").pack(side=tk.LEFT)
        self._host_var = tk.StringVar(value="127.0.0.1")
        tk.Entry(row1, textvariable=self._host_var, font=FONT_MONO_SM,
                 fg=TEXT_PRIMARY, bg=BG_RAISED, insertbackground=ACCENT_BLUE,
                 relief="flat", width=20).pack(side=tk.LEFT, padx=(0, PAD))

        tk.Label(row1, text="Port:", font=FONT_BOLD, fg=TEXT_SECONDARY,
                 bg=BG_SURFACE, width=6, anchor="w").pack(side=tk.LEFT)
        self._port_var = tk.StringVar(value="1234")
        tk.Entry(row1, textvariable=self._port_var, font=FONT_MONO_SM,
                 fg=TEXT_PRIMARY, bg=BG_RAISED, insertbackground=ACCENT_BLUE,
                 relief="flat", width=8).pack(side=tk.LEFT)

        # Auto-detect button
        row2 = tk.Frame(conn_card, bg=BG_SURFACE, pady=PAD_SM)
        row2.pack(fill=tk.X, padx=PAD)
        self._detect_btn = StyledButton(row2, "⚡  Auto-Detect LM Studio",
                                         command=self._auto_detect, style="primary")
        self._detect_btn.pack(side=tk.LEFT, padx=(0, PAD_SM))
        StyledButton(row2, "Connect Manually", command=self._manual_connect,
                     style="secondary").pack(side=tk.LEFT, padx=(0, PAD_SM))
        StyledButton(row2, "Disconnect", command=self._disconnect, style="danger").pack(side=tk.LEFT)

        # Status display
        self._conn_status = tk.Label(conn_card, text="Status: Not connected",
                                      font=FONT_SANS_SM, fg=ACCENT_RED,
                                      bg=BG_SURFACE, pady=PAD_SM)
        self._conn_status.pack(anchor="w", padx=PAD)

        # Model selection card
        model_card = tk.Frame(self, bg=BG_SURFACE,
                               highlightbackground=BG_BORDER, highlightthickness=1)
        model_card.pack(fill=tk.X, padx=PAD_LG, pady=(0, PAD_LG))
        tk.Label(model_card, text="Model Selection", font=FONT_BOLD,
                 fg=ACCENT_BLUE, bg=BG_SURFACE, pady=PAD).pack(anchor="w", padx=PAD)
        Separator(model_card).pack(fill=tk.X)

        m_row = tk.Frame(model_card, bg=BG_SURFACE, pady=PAD_SM)
        m_row.pack(fill=tk.X, padx=PAD)
        tk.Label(m_row, text="Active Model:", font=FONT_BOLD, fg=TEXT_SECONDARY,
                 bg=BG_SURFACE, width=14, anchor="w").pack(side=tk.LEFT)
        self._model_var = tk.StringVar(value="—")
        self._model_dropdown = ttk.Combobox(m_row, textvariable=self._model_var,
                                             font=FONT_SANS, width=50, state="readonly")
        self._model_dropdown.pack(side=tk.LEFT)
        self._model_dropdown.bind("<<ComboboxSelected>>", self._on_model_change)
        StyledButton(m_row, "↻ Refresh", command=self._refresh_models,
                     style="secondary").pack(side=tk.LEFT, padx=PAD_SM)

        # Inference settings card
        inf_card = tk.Frame(self, bg=BG_SURFACE,
                             highlightbackground=BG_BORDER, highlightthickness=1)
        inf_card.pack(fill=tk.X, padx=PAD_LG, pady=(0, PAD_LG))
        tk.Label(inf_card, text="Inference Parameters", font=FONT_BOLD,
                 fg=ACCENT_BLUE, bg=BG_SURFACE, pady=PAD).pack(anchor="w", padx=PAD)
        Separator(inf_card).pack(fill=tk.X)

        inf_row = tk.Frame(inf_card, bg=BG_SURFACE, pady=PAD_SM)
        inf_row.pack(fill=tk.X, padx=PAD)

        tk.Label(inf_row, text="Max Tokens:", font=FONT_SANS, fg=TEXT_SECONDARY,
                 bg=BG_SURFACE, width=12, anchor="w").pack(side=tk.LEFT)
        self._max_tokens = tk.IntVar(value=512)
        tk.Spinbox(inf_row, from_=64, to=4096, increment=64,
                   textvariable=self._max_tokens,
                   font=FONT_SANS, fg=TEXT_PRIMARY, bg=BG_RAISED,
                   relief="flat", width=6).pack(side=tk.LEFT, padx=(0, PAD_LG))

        tk.Label(inf_row, text="Temperature:", font=FONT_SANS, fg=TEXT_SECONDARY,
                 bg=BG_SURFACE, width=12, anchor="w").pack(side=tk.LEFT)
        self._temperature = tk.DoubleVar(value=0.3)
        tk.Spinbox(inf_row, from_=0.0, to=2.0, increment=0.1,
                   textvariable=self._temperature,
                   format="%.1f",
                   font=FONT_SANS, fg=TEXT_PRIMARY, bg=BG_RAISED,
                   relief="flat", width=6).pack(side=tk.LEFT)

        # Info box
        info_card = tk.Frame(self, bg=BG_RAISED,
                              highlightbackground=BG_BORDER, highlightthickness=1)
        info_card.pack(fill=tk.X, padx=PAD_LG)
        tk.Label(info_card,
                 text="ℹ  LM Studio must be running with a model loaded and the local server enabled.\n"
                      "   Default server: http://127.0.0.1:1234  ·  Auto-detect probes ports 1234, 1235, 8080.",
                 font=FONT_SANS_SM, fg=TEXT_SECONDARY, bg=BG_RAISED,
                 justify="left", pady=PAD, padx=PAD).pack(anchor="w")

    def _auto_detect(self):
        self._conn_status.config(text="Status: Detecting…", fg=ACCENT_AMBER)
        self._detect_btn.config(state=tk.DISABLED)
        self.update_idletasks()

        def worker():
            ok = self.app.client.auto_detect()
            self.after(0, self._on_detect_done, ok)

        threading.Thread(target=worker, daemon=True).start()

    def _on_detect_done(self, ok: bool):
        self._detect_btn.config(state=tk.NORMAL)
        if ok:
            url = self.app.client.base_url
            model = self.app.client.active_model or "?"
            self._conn_status.config(
                text=f"Status: Connected  ·  {url}  ·  {model}",
                fg=ACCENT_GREEN,
            )
            models = [m["id"] for m in self.app.client.models]
            self._model_dropdown["values"] = models
            self._model_var.set(model)
            # Parse host/port
            try:
                parts = url.replace("http://", "").split(":")
                self._host_var.set(parts[0])
                self._port_var.set(parts[1])
            except Exception:
                pass
            self.app.on_connected(url, model)
        else:
            self._conn_status.config(
                text="Status: Auto-detect failed — is LM Studio running?",
                fg=ACCENT_RED,
            )
            self.app.on_disconnected()

    def _manual_connect(self):
        host = self._host_var.get().strip()
        port = self._port_var.get().strip()
        url = f"http://{host}:{port}"
        self._conn_status.config(text=f"Status: Connecting to {url}…", fg=ACCENT_AMBER)
        self.update_idletasks()

        def worker():
            import requests as rq
            try:
                resp = rq.get(f"{url}/v1/models", timeout=5)
                if resp.status_code == 200:
                    models = resp.json().get("data", [])
                    self.app.client.base_url = url
                    self.app.client.models = models
                    self.app.client.active_model = models[0]["id"] if models else None
                    self.after(0, self._on_detect_done, True)
                else:
                    self.after(0, self._on_detect_done, False)
            except Exception:
                self.after(0, self._on_detect_done, False)

        threading.Thread(target=worker, daemon=True).start()

    def _disconnect(self):
        self.app.client.base_url = None
        self.app.client.active_model = None
        self._conn_status.config(text="Status: Disconnected", fg=ACCENT_RED)
        self._model_var.set("—")
        self.app.on_disconnected()

    def _refresh_models(self):
        models = self.app.client.refresh_models()
        if models:
            self._model_dropdown["values"] = models
            if self.app.client.active_model:
                self._model_var.set(self.app.client.active_model)

    def _on_model_change(self, event):
        selected = self._model_var.get()
        self.app.client.active_model = selected
        self.app.on_model_changed(selected)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APP WINDOW
# ─────────────────────────────────────────────────────────────────────────────

class CanonCacheApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CanonCache — KV-Cache Research Tool")
        self.geometry("1280x820")
        self.minsize(960, 640)
        self.configure(bg=BG_DEEP)

        # Set icon (skip if file missing)
        try:
            self.iconbitmap(str(ROOT / "assets" / "icon.ico"))
        except Exception:
            pass

        self.client = LMStudioClient()
        self._last_report: BenchmarkReport | None = None
        self._run_count = 0
        # Must be set BEFORE _build() because Sidebar.__init__ calls _on_nav
        self._active_tab = None
        self._tabs: dict = {}

        self._build()
        self._load_cluster_count()

    def _build(self):
        # Top header bar
        self._header = tk.Frame(self, bg=BG_SURFACE, height=HEADER_H,
                                 highlightbackground=BG_BORDER, highlightthickness=1)
        self._header.pack(fill=tk.X, side=tk.TOP)
        self._header.pack_propagate(False)

        tk.Label(self._header, text="CanonCache", font=("Segoe UI", 13, "bold"),
                 fg=ACCENT_BLUE, bg=BG_SURFACE).pack(side=tk.LEFT, padx=PAD_LG, pady=PAD_SM)
        tk.Label(self._header, text="Semantic KV-Cache Canonicalization Research Platform",
                 font=FONT_SANS_SM, fg=TEXT_SECONDARY, bg=BG_SURFACE).pack(side=tk.LEFT)

        self._header_model = tk.Label(self._header, text="",
                                       font=FONT_SANS_SM, fg=TEXT_DISABLED, bg=BG_SURFACE)
        self._header_model.pack(side=tk.RIGHT, padx=PAD_LG)

        # Main area: sidebar + content
        main = tk.Frame(self, bg=BG_DEEP)
        main.pack(fill=tk.BOTH, expand=True)

        self.sidebar = Sidebar(main, on_select=self._on_nav)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Thin vertical separator
        tk.Frame(main, bg=BG_BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        # Content area
        self._content = tk.Frame(main, bg=BG_DEEP)
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Build tabs
        self.tab_dashboard  = DashboardTab(self._content, self)
        self.tab_benchmark  = BenchmarkTab(self._content, self)
        self.tab_chat       = ChatTab(self._content, self)
        self.tab_results    = ResultsTab(self._content, self)
        self.tab_settings   = SettingsTab(self._content, self)

        self._tabs = {
            "Dashboard": self.tab_dashboard,
            "Benchmark": self.tab_benchmark,
            "Chat":      self.tab_chat,
            "Results":   self.tab_results,
            "Settings":  self.tab_settings,
        }
        self._active_tab = None
        self._on_nav("Dashboard")

    def _on_nav(self, name: str):
        if not self._tabs:
            return  # called during sidebar init before tabs exist
        if self._active_tab:
            self._active_tab.pack_forget()
        tab = self._tabs.get(name)
        if tab is None:
            return
        tab.pack(fill=tk.BOTH, expand=True)
        self._active_tab = tab

    def _load_cluster_count(self):
        try:
            count = sum(1 for _ in open(DATA_PATH))
        except Exception:
            count = 0
        self._cluster_count = count
        self.tab_dashboard.refresh("—", count, 0, "—")

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_connected(self, url: str, model: str):
        self.sidebar.set_connection(True, model)
        self._header_model.config(
            text=f"⬤  {model[:40]}", fg=ACCENT_GREEN
        )
        self.tab_dashboard.refresh(model, self._cluster_count, self._run_count, "—")

    def on_disconnected(self):
        self.sidebar.set_connection(False)
        self._header_model.config(text="", fg=TEXT_DISABLED)
        self.tab_dashboard.refresh("—", self._cluster_count, self._run_count, "—")

    def on_model_changed(self, model: str):
        self.sidebar.set_connection(bool(self.client.base_url), model)
        self._header_model.config(text=f"⬤  {model[:40]}", fg=ACCENT_GREEN)
        self.tab_dashboard.refresh(model, self._cluster_count, self._run_count, "—")

    def on_benchmark_done(self, report: BenchmarkReport):
        self._last_report = report
        self._run_count += 1
        hit_pct = f"{report.simulated_cache_hit_rate_canonical:.0%}"
        self.tab_dashboard.refresh(
            self.client.active_model or "—",
            self._cluster_count,
            self._run_count,
            hit_pct,
        )
        self.tab_results.load_report(report)
