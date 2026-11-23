# Evaluation Protocol & Scoring Framework

## Benchmark Overview
The Catalist evaluation consists of 35 total test questions:
- **25 Assessment Questions**: Supplied in `questions.json` across 13 AMI teams.
- **10 Independently Authored Questions**: Manually curated by the author with ground-truth citations to test specific cross-meeting challenges.

## Scoring Criteria per Question
1. **Answer Correctness (0 or 1)**: Correctly answers the core question in 1–3 plain sentences.
2. **Citation Count (0 or 1)**: Backed by 1 to 3 valid citations.
3. **Exact Quote Check (0 or 1)**: Every quote is >= 6 words, verbatim from transcript, and located in a single speaker turn.
4. **Meeting ID Match (0 or 1)**: Quoted words actually belong to the attributed `meeting_id`.

Overall Question Score = $\text{Correctness} \times \text{Citation Valid}$.

