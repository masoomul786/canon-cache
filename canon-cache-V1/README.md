# CanonCache
### Semantic KV-Cache Canonicalization Research Platform

> A research tool for benchmarking prompt canonicalization as a strategy to improve KV-cache prefix hit rates in multi-tenant LLM inference environments.

---

## Overview

CanonCache evaluates the core hypothesis of the **SemCache** research paper:

> *By rewriting semantically equivalent but syntactically diverse prompts into a canonical form, we can dramatically increase prefix cache hit rates — reducing GPU-hours per request without degrading output quality.*

It provides a professional GUI (Python Tkinter) connected to a local **LM Studio** inference server, with:

- **Benchmark Runner** — runs raw vs. canonical prompt pairs against your model, measures latency, token efficiency, semantic similarity, and simulated cache hit rates
- **Chat Interface** — direct streaming chat for qualitative evaluation
- **Results Viewer** — per-cluster detailed analysis and export
- **Auto-Detection** — automatically finds your running LM Studio instance

---

## Quick Start

### 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | `python --version` |
| `requests` | `pip install requests` |
| `tkinter` | Bundled with Python on Windows/Mac; `sudo apt install python3-tk` on Linux |
| LM Studio | [lmstudio.ai](https://lmstudio.ai) — run the local server on port 1234 |

### 2. Install & Run

```bash
# Clone or extract the project
cd CanonCache

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### 3. Connect to LM Studio

1. Open LM Studio → Load a model → Enable the local server (Settings → Local Server)
2. In CanonCache, go to **Settings** tab → click **⚡ Auto-Detect LM Studio**
3. The status bar will turn green when connected

### 4. Run a Benchmark

1. Go to **Benchmark** tab
2. Select number of clusters (default: 10 from the 20 included)
3. Click **▶ Run Benchmark**
4. Watch real-time progress and metrics update live

---

## Project Structure

```
CanonCache/
├── main.py                  # Entry point
├── requirements.txt
├── README.md
│
├── core/
│   ├── lm_studio.py         # LM Studio API client (auto-detect + streaming)
│   └── benchmark.py         # Benchmark engine, metrics, export
│
├── ui/
│   ├── theme.py             # Dark theme constants
│   ├── widgets.py           # Reusable UI components
│   └── app.py               # Main application window + all tabs
│
├── data/
│   └── sample_clusters.jsonl  # 20 benchmark prompt clusters
│
└── results/                 # Auto-saved JSON/CSV reports
```

---

## Benchmark Dataset Format

The benchmark dataset (`data/sample_clusters.jsonl`) is JSONL — one cluster per line:

```json
{
  "cluster_id": "c001",
  "topic": "machine_learning_definition",
  "prompts": [
    "What is machine learning?",
    "Can you explain ML to me?",
    "Define machine learning in simple terms",
    "What does machine learning mean?"
  ],
  "canonical": "Explain the concept of machine learning clearly and concisely.",
  "source": "handcrafted"
}
```

| Field | Description |
|-------|-------------|
| `cluster_id` | Unique identifier |
| `topic` | Topic label for grouping |
| `prompts` | 2–4 semantically equivalent but syntactically diverse prompts |
| `canonical` | The canonicalized form — the single form all prompts map to |
| `source` | `handcrafted` / `lmsys` / `synthetic` |

---

## Metrics Explained

| Metric | Description |
|--------|-------------|
| **Cache Hit Rate (Raw)** | Simulated exact-prefix cache hit rate (~5%) — represents baseline vLLM/SGLang performance on diverse traffic |
| **Cache Hit Rate (Canonical)** | Simulated hit rate after canonicalization — target is 35–65% with real traffic |
| **Latency Δ** | Percentage change in avg response latency: raw → canonical |
| **Token Reduction %** | Total tokens consumed: sum(raw prompts) vs sum(canonical prompts) |
| **Semantic Similarity** | Jaccard overlap between canonical and raw responses — measures quality preservation |
| **Quality Score** | Composite similarity of canonical response vs all raw responses in the cluster |

---

## Research Context

This tool supports the **SemCache** research paper:

> *SemCache: Semantic KV-Cache Merging for Multi-Tenant LLM Inference*
>
> Core contributions:
> 1. **Prompt Canonicalizer** — rewrites semantically equivalent prompts to a single canonical form to maximize exact prefix match
> 2. **KV-Cache Adapter** — low-rank LoRA-style adapter that transforms one prompt's KV-cache to approximate another's
> 3. **Merge Feasibility Predictor** — binary gate that ensures only high-confidence pairs are merged

**Phase 1 validation (this tool):** Demonstrates that canonicalization alone produces a measurable prefix cache hit rate lift, validating the core premise before implementing the full KV-cache adapter.

**Target venues:** MLSys, OSDI, SOSP

---

## Extending the Dataset

Add more clusters to `data/sample_clusters.jsonl`:

```bash
echo '{"cluster_id":"c021","topic":"my_topic","prompts":["Prompt A?","Prompt B?"],"canonical":"Canonical form.","source":"custom"}' >> data/sample_clusters.jsonl
```

Or create a new JSONL file and load it via the **Browse** button in the Benchmark tab.

---

## Exporting Results

After a benchmark run:
- **Auto-save:** Reports are automatically saved to `results/report_<run_id>_<timestamp>.json`
- **Manual export:** Use **📥 Export JSON** or **📥 Export CSV** in the Benchmark tab
- **Load previous:** Use **📂 Load JSON Report** in the Results tab

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Auto-detect failed" | Ensure LM Studio is running and the local server is enabled (default port 1234) |
| "Request timed out" | Model may be loading; try again or increase timeout in `core/lm_studio.py` |
| Tkinter not found | `sudo apt install python3-tk` (Linux) or reinstall Python (Windows/Mac) |
| Empty responses | Check LM Studio model is loaded and responding in LM Studio's chat UI first |

---

## License

For research use. Based on original SemCache research concept.
