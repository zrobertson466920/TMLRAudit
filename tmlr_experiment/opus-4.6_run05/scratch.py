import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching all TMLR submissions with replies...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', [])
    review_times = []
    decision_time = None

    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if not invs or cdate is None:
            continue
        # Extract short names
        short = [i.split('/')[-1] for i in invs]

        # Review (but not Decision)
        if 'Review' in short and 'Decision' not in short:
            review_times.append(cdate)

        # Decision
        if 'Decision' in short:
            if decision_time is None or cdate < decision_time:
                decision_time = cdate

    review_times.sort()
    records.append({
        'id': note.id,
        'n_reviews': len(review_times),
        't_first_review': review_times[0] if review_times else None,
        't_third_review': review_times[2] if len(review_times) >= 3 else None,
        't_decision': decision_time,
    })

df = pd.DataFrame(records)
df['censored'] = df['t_decision'].isna()
df['gap_from_3rd'] = (df['t_decision'] - df['t_third_review']) / (1000*60*60*24)
df['gap_from_1st'] = (df['t_decision'] - df['t_first_review']) / (1000*60*60*24)

print(f"\nParsed {len(df)} submissions")
print(f"  With >=1 review:  {(df['n_reviews'] >= 1).sum()}")
print(f"  With >=3 reviews: {(df['n_reviews'] >= 3).sum()}")
print(f"  With decision:    {df['t_decision'].notna().sum()}")
print(f"  Censored (no decision yet): {df['censored'].sum()}")

# Uncensored with >=3 reviews and positive gap
unc = df[(~df['censored']) & df['t_third_review'].notna() & (df['gap_from_3rd'] > 0)].copy()
N = len(unc)
g = unc['gap_from_3rd']

q = g.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
s28 = (g > 28).mean() * 100
s35 = (g > 35).mean() * 100
s42 = (g > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored, >=3 reviews): {N}

Quantiles (days from 3rd review to decision):
  Median: {q[0.5]:.1f}
  75th:   {q[0.75]:.1f}
  90th:   {q[0.90]:.1f}
  95th:   {q[0.95]:.1f}
  99th:   {q[0.99]:.1f}

Compliance with stated "no later than 5 weeks" (from 3rd review to decision):
  Share > 28 days: {s28:.1f}%
  Share > 35 days: {s35:.1f}% (violates 5-week guideline)
  Share > 42 days: {s42:.1f}%

Mean: {g.mean():.1f} days
Std:  {g.std():.1f} days
Min:  {g.min():.1f} days
Max:  {g.max():.1f} days
""")

# Also report from first review (as in spec's original framing)
unc1 = df[(~df['censored']) & df['t_first_review'].notna() & (df['gap_from_1st'] > 0)].copy()
g1 = unc1['gap_from_1st']
q1 = g1.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
print(f"=== Alternative: from 1st review to decision (N={len(unc1)}) ===")
print(f"  Median: {q1[0.5]:.1f}  75th: {q1[0.75]:.1f}  90th: {q1[0.90]:.1f}  95th: {q1[0.95]:.1f}")
print(f"  Share > 35 days: {(g1>35).mean()*100:.1f}%  Share > 42 days: {(g1>42).mean()*100:.1f}%")