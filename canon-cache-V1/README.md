# CanonCache

> Semantic KV-Cache Canonicalization for Multi-Tenant LLM Inference

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/license-CC--BY--NC--SA%204.0-blue.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Status](https://img.shields.io/badge/status-research--prototype-orange.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()

CanonCache is a research prototype and benchmarking platform for evaluating **semantic prompt canonicalization** as a strategy to improve KV-cache prefix reuse in large language model (LLM) serving systems.

The core idea is simple:

> Semantically equivalent prompts often fail to share KV-cache prefixes because they differ syntactically.  
> CanonCache rewrites them into deterministic canonical forms to maximize exact-prefix cache reuse.

---

# Research Paper

**CanonCache: Semantic KV-Cache Canonicalization as a Strategy for LLM Inference Efficiency in Multi-Tenant Environments**

**Author:** Masoomul Haque Choudhury  
**License:** CC BY-NC-SA 4.0  
**Status:** Research Preprint — May 2026

GitHub Repository:  
https://github.com/masoomul786/canon-cache

Project Folder:  
https://github.com/masoomul786/canon-cache/tree/main/canon-cache-V1

---

# Core Hypothesis

Traditional prefix caching systems such as:
- vLLM
- SGLang
- RadixAttention

require **exact token-prefix matches**.

This fails for real-world user traffic:

| Prompt A | Prompt B |
|---|---|
| What is machine learning? | Can you explain ML to me? |

Semantically identical.  
Token prefixes completely different.

CanonCache introduces a semantic canonicalization layer:

```text
Raw Prompt
    ↓
Canonicalization
    ↓
Deterministic Canonical Prompt
    ↓
Exact Prefix Cache Reuse
```

---

# Benchmark Results (Run 522b16c2)

| Metric | Raw | Canonical |
|---|---|---|
| Cache Hit Rate | 5% | 37.5% |
| Token Reduction | — | 47.5% |
| SCAR | — | 7.5× |
| SCE | — | 0.475 |
| Avg Semantic Similarity | — | 0.399 |
| Latency Δ | — | -1.3% |

### Key Findings

- **+32.5 percentage-point cache hit lift**
- **47.5% prompt token reduction**
- **7.5× cache amplification (SCAR)**
- Minimal latency overhead on a cold-start single-node setup

⚠️ Current results are based on:
- simulated prefix-cache evaluation
- single-node LM Studio inference
- no active GPU-level prefix caching

These benchmarks validate the **semantic canonicalization premise**, not full production deployment behavior.

---

# Architecture

```text
Users
  ↓
Semantic Canonicalizer
  ↓
Canonical Prompt
  ↓
Prefix Cache Layer
  ↓
LLM Inference Engine
(LM Studio / vLLM / SGLang)
  ↓
Responses
```

---

# Features

- Semantic prompt canonicalization
- Prefix cache benchmarking
- Real-time benchmark execution
- LM Studio integration
- JSON/CSV export
- GUI benchmark runner
- Per-cluster analysis
- Semantic similarity evaluation
- Cache amplification metrics (SCAR)
- Compression efficiency metrics (SCE)

---

# Project Structure

```text
canon-cache-V1/
├── main.py
├── requirements.txt
├── README.md
│
├── core/
│   ├── benchmark.py
│   └── lm_studio.py
│
├── ui/
│   ├── app.py
│   ├── theme.py
│   └── widgets.py
│
├── data/
│   └── sample_clusters.jsonl
│
├── results/
│   ├── reports/
│   └── exports/
│
└── docs/
    └── preprint/
```

---

# Installation

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| LM Studio | v0.3+ |
| requests | latest |
| tkinter | bundled |

---

# Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/masoomul786/canon-cache.git
cd canon-cache/canon-cache-V1
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Start LM Studio

1. Open LM Studio
2. Load a model
3. Enable Local Server
4. Default endpoint:
   http://127.0.0.1:1234

Recommended model:
- Qwen/Qwen3.5-9B
- 4-bit quantized

---

## 4. Run CanonCache

```bash
python main.py
```

---

# Benchmark Dataset Format

Example cluster:

```json
{
  "cluster_id": "c001",
  "topic": "machine_learning",
  "prompts": [
    "What is machine learning?",
    "Can you explain ML to me?"
  ],
  "canonical": "Explain the concept of machine learning clearly and concisely.",
  "source": "handcrafted"
}
```

---

# Formal Metrics

## Prefix Cache Hit Rate

```math
H = N_hit / N_total
```

---

## Token Reduction

```math
R_token = (T_raw - T_canon) / T_raw × 100
```

---

## Semantic Similarity

```math
Sim(u,v) = (u·v)/(||u|| ||v||)
```

---

## Semantic Cache Amplification Ratio (SCAR)

```math
SCAR = H_canon / H_raw
```

---

## Semantic Compression Efficiency (SCE)

```math
SCE = (T_raw - T_canon) / T_raw
```

---

# Research Positioning

CanonCache is designed as:
- a middleware optimization layer
- not a new transformer architecture
- not a new foundation model

It is intended to complement:
- prefix caching
- continuous batching
- speculative decoding
- disaggregated prefill architectures

---

# Current Limitations

- Single-node benchmark only
- Simulated cache evaluation
- Small dataset (10 clusters)
- Canonicalizer uses same model as inference
- Semantic fidelity still requires improvement
- No real vLLM integration yet

---

# Future Work

- vLLM integration
- SGLang integration
- Dedicated lightweight canonicalizer
- Large-scale ShareGPT/LMSYS evaluation
- Multi-turn conversation support
- BERTScore / LLM-as-judge evaluation
- Real GPU KV-cache benchmarking

---

# Citation

```bibtex
@misc{choudhury2026canoncache,
  title={CanonCache: Semantic KV-Cache Canonicalization for LLM Inference Efficiency in Multi-Tenant Environments},
  author={Masoomul Haque Choudhury},
  year={2026},
  note={Research Preprint},
  license={CC BY-NC-SA 4.0}
}
```

---

# License

This project is licensed under the:

## CC BY-NC-SA 4.0
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International

You are free to:
- Share
- Remix
- Adapt

Under the following conditions:
- Attribution required
- Non-commercial use only
- Derivative works must use the same license

Full License:
https://creativecommons.org/licenses/by-nc-sa/4.0/

---

# Author

**Masoomul Haque Choudhury**  
Independent Researcher — Assam, India

Research Areas:
- LLM Inference Optimization
- KV-Cache Systems
- Semantic Caching
- AI Infrastructure
- Token Efficiency

---

# Acknowledgement

CanonCache builds upon ideas and prior systems research from:
- vLLM
- SGLang
- PagedAttention
- RadixAttention
- Sentence-BERT
- Prefix Caching Systems

This project is an independent research exploration into semantic canonicalization for inference efficiency.
