# TMLR Decision Timeline Audit

**How long do TMLR decisions actually take?**

TMLR's [Action Editor guidelines](https://jmlr.org/tmlr/ae-guide.html) state that decisions should be submitted within 5 weeks of the third review. This script audits every decided TMLR submission on OpenReview to check whether that timeline holds in practice.

**Companion blog post:** [How Long Do TMLR Decisions Actually Take? An OpenReview Audit](https://zrobertson466920.github.io/TMLRAudit/)

## Key Findings (as of February 6, 2025)

| Metric | Days |
|--------|------|
| Median | **45.2** |
| 75th percentile | 57.0 |
| 90th percentile | 72.5 |

- **82.5%** of decisions exceed the 5-week (35-day) target
- **95.7%** exceed the 4-week (28-day) reviewer recommendation window
- The median has been stable at ~45 days since 2023
- Rejection rate is flat at ~28% across all wait times — longer waits don't predict worse outcomes

## Usage

```bash
pip install openreview-py pandas numpy matplotlib
python tmlr_audit.py
```

No API credentials required — all data is public. The script takes ~30 seconds to fetch all submissions and produces:

- **Console output:** Summary statistics, compliance rates, and rejection rates by wait time
- **`images/tmlr_histogram.png`:** Distribution of decision times by week
- **`images/tmlr_yearly.png`:** Median decision time by year
- **`images/tmlr_rejection_by_wait.png`:** Rejection rate vs. decision wait time

## What the script does

1. Fetches all TMLR submissions via the [OpenReview API](https://docs.openreview.net/)
2. For each submission, extracts the **third review timestamp** (when the review clock starts per TMLR's own author communications) and the **decision timestamp**
3. Computes the gap in days and reports quantiles and compliance rates

**Scope:** Papers with ≥3 reviews and a posted decision (N ≈ 4,865). Desk rejects, withdrawals, and papers still under review are excluded. No paper in the dataset has more than one decision.

## Citation

```bibtex
@misc{robertson2025tmlraudit,
  title={How Long Do TMLR Decisions Actually Take? An OpenReview Audit},
  author={Robertson, Zachary},
  year={2025},
  institution={Stanford University},
  url={https://zrobertson466920.github.io/TMLRAudit/},
  note={Blog post auditing TMLR decision timelines using OpenReview API data}
}
```