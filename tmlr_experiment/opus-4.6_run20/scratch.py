import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions")

MS_PER_DAY = 1000 * 60 * 60 * 24
records = []
for note in submissions:
    replies = note.details.get('replies', []) if note.details else []
    review_times, decision_times = [], []
    for r in replies:
        invs = ' '.join(r.get('invitations', []))
        cdate = r.get('cdate')
        if cdate is None:
            continue
        if '/-/Review' in invs and 'Decision' not in invs:
            review_times.append(cdate)
        if '/-/Decision' in invs:
            decision_times.append(cdate)

    # Use the LAST (3rd) review as the start of discussion, per TMLR policy
    t_last_review = max(review_times) if review_times else None
    t_first_review = min(review_times) if review_times else None
    t_dec = min(decision_times) if decision_times else None
    records.append({
        'id': note.id, 'n_reviews': len(review_times),
        't_first_review': t_first_review, 't_last_review': t_last_review,
        't_decision': t_dec
    })

df = pd.DataFrame(records)
df['censored'] = df['t_decision'].isna()
df['gap_from_first'] = (df['t_decision'] - df['t_first_review']) / MS_PER_DAY
df['gap_from_last'] = (df['t_decision'] - df['t_last_review']) / MS_PER_DAY
df['review_spread'] = (df['t_last_review'] - df['t_first_review']) / MS_PER_DAY

# Filter: uncensored, valid gap, positive
unc = df[~df['censored'] & df['gap_from_last'].notna() & (df['gap_from_last'] > 0)].copy()
N = len(unc)

for label, col in [("last review (TMLR policy anchor)", 'gap_from_last'),
                    ("first review (for comparison)", 'gap_from_first')]:
    q = unc[col].quantile([0.5, 0.75, 0.90, 0.95, 0.99])
    s28 = (unc[col] > 28).mean() * 100
    s35 = (unc[col] > 35).mean() * 100
    s42 = (unc[col] > 42).mean() * 100
    print(f"""
=== Gap from {label} ===
N (uncensored): {N}

Quantiles (days):
  Median: {q[0.5]:.1f}
  75th:   {q[0.75]:.1f}
  90th:   {q[0.90]:.1f}
  95th:   {q[0.95]:.1f}
  99th:   {q[0.99]:.1f}

Compliance:
  Share > 28 days: {s28:.1f}%
  Share > 35 days: {s35:.1f}%
  Share > 42 days: {s42:.1f}%""")

# Bonus: review spread stats
sp = unc['review_spread'].describe()
print(f"""
=== Review spread (days between first and last review) ===
  Median: {unc['review_spread'].median():.1f}
  Mean:   {unc['review_spread'].mean():.1f}
  90th:   {unc['review_spread'].quantile(0.9):.1f}
""")