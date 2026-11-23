# Catalist Meeting Intelligence — Dataset Directory

This directory manages the raw and processed data assets for the Catalist Meeting Intelligence Agent.

## Directory Structure

```text
data/
├── raw/
│   ├── Catalist_AI_Intern_Build_Test_Data.zip   # Supplied archive containing 138 AMI transcripts
│   ├── Catalist_Agentic_AI_Intern_Build_Test.pdf # Original evaluation brief
│   ├── questions.json                           # 25 evaluation questions and submission format
│   └── CREDITS.txt                              # AMI Corpus attribution and licensing
├── processed/                                   # Cleaned, chunked, or indexed data (Phase 2+)
└── README.md
```

## Dataset Overview

- **Corpus**: AMI Meeting Corpus, CC BY 4.0 (University of Edinburgh and partners).
- **Size**: 138 meeting transcripts across 35 design teams (approx. 676,000 words / ~880,000 tokens).
- **Context**: 4-person design teams (project manager, industrial designer, user interface designer, marketing) meeting across 4 sessions (a to d) to design a remote control.
- **Evaluation Questions**: 25 cross-meeting multi-hop reasoning questions (`questions.json`).

## Phase Boundaries

- **Phase 1 (Current)**: Directory structure established, dataset integrity and structure inspected. **No transcript parsing or ingestion is performed.**
- **Phase 2 (Next)**: Resumable, idempotent ingestion into PostgreSQL 16 + pgvector with exact speaker turns preserved.

