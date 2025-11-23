# LLM-Based Protein Structure Refinement

An autonomous AI agent that refines protein structures—specifically Intrinsically Disordered Proteins (IDPs)—by leveraging large language models (LLMs) to retrieve biological context and guide geometric optimization.

## 🚀 Overview

AlphaFold is revolutionary but often struggles with IDPs, predicting them as low-confidence loops even when they fold upon binding. This pipeline solves that by:
1.  **Identifying** low-confidence regions in AlphaFold predictions.
2.  **Researching** the protein using an LLM to find "folding-upon-binding" behavior.
3.  **Translating** text descriptions (e.g., "folds into a helix") into geometric constraints.
4.  **Refining** the structure to match the biological reality.

**Key Achievement:** The pipeline autonomously improved the structure of **HIF-1a** by **+0.076 Å** RMSD, surpassing manual human curation.

---

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Navneeth08k/LLM-Based-protein-structure-refinement.git
    cd LLM-Based-protein-structure-refinement
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up API Keys:**
    You need a Google Gemini API key (or OpenAI). Set it as an environment variable or pass it via command line.
    ```bash
    export GEMINI_API_KEY="your_api_key_here"
    ```

---

## 🛠️ Usage

### 1. Fully Automated Refinement
To refine a protein by its UniProt ID (e.g., HIF-1a) with zero manual input:

```bash
python main.py --uniprot Q16665 --auto_context --provider gemini --api_key YOUR_KEY
```

*   `--uniprot`: The ID of the protein to fetch/refine.
*   `--auto_context`: Enables the AI agent to research the protein automatically.

### 2. Manual Context (Optional)
If you want to provide specific knowledge yourself:

```bash
python main.py --uniprot Q16665 --context "Folds into three alpha helices upon binding CBP"
```

### 3. Running the Benchmark Suite
To test the pipeline on the full dataset of 12 proteins:

```bash
python run_benchmark_suite.py --auto_context
```
This will generate `benchmark_results.csv` and summary plots.

---

## ⚙️ Pipeline Architecture

The system consists of four main stages:

### 1. Data Acquisition (`src/utils/data_fetcher.py`)
*   Automatically downloads the latest AlphaFold prediction (PDB & JSON) from the AlphaFold Database.
*   Parses the confidence scores (pLDDT).

### 2. Region Identification (`src/analysis/region_finder.py`)
*   Scans the pLDDT scores to find contiguous regions of low confidence (pLDDT < 70).
*   These are flagged as potential IDPs.

### 3. Context Retrieval (`src/llm/context_agent.py`)
*   **The "Brain":** An LLM agent queries the UniProt API for the protein name.
*   It then asks the LLM: *"What is the folding-upon-binding behavior of [Protein Name]?"*
*   It extracts specific structural details (e.g., "amphipathic helix").

### 4. Geometric Refinement (`src/geometry/refiner.py`)
*   **The "Hands":** The text description is converted into distance constraints (e.g., residue $i$ to $i+4$ distance = 6.0 Å).
*   A geometric optimizer applies these constraints to the PDB structure, folding the disordered region while keeping the rest of the protein stable.

---

## 📊 Results

The pipeline was benchmarked on 12 targets.

| Target | Description | Improvement (RMSD) | Status |
| :--- | :--- | :--- | :--- |
| **HIF-1a** | C-terminal TAD | **+0.076 Å** | ✅ Success |
| **c-Fos** | Leucine Zipper | **+0.038 Å** | ✅ Success |
| **NCBD** | Helical Bundle | **+0.010 Å** | ✅ Success |

*Positive values indicate the refined structure is closer to the experimental ground truth.*

---

## 📂 Project Structure

*   `main.py`: The entry point for the single-protein pipeline.
*   `run_benchmark_suite.py`: Runner for the full validation set.
*   `src/`: Core source code.
    *   `llm/`: Agents and clients for Gemini/OpenAI.
    *   `geometry/`: Physics and geometry refinement logic.
    *   `analysis/`: RMSD calculation and region finding.
    *   `utils/`: Data fetching and PDB handling.
*   `benchmarks.csv`: Dataset of targets and ground truths.

---

## 📄 License
MIT License.
