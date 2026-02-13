import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', [])
    review_times = []
    decision_times = []
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if cdate is None:
            continue
        inv_str = ' '.join(invs)
        if '/-/Review' in inv_str and 'Decision' not in inv_str:
            review_times.append(cdate)
        if '/-/Decision' in inv_str:
            decision_times.append(cdate)
    
    review_times.sort()
    t_third = review_times[2] if len(review_times) >= 3 else None
    t_first = review_times[0] if review_times else None
    t_dec = min(decision_times) if decision_times else None
    records.append({
        'id': note.id,
        't_first_review': t_first,
        't_third_review': t_third,
        'n_reviews': len(review_times),
        't_decision': t_dec,
    })

df = pd.DataFrame(records)
df['has_decision'] = df['t_decision'].notna()
df['has_3reviews'] = df['t_third_review'].notna()

# Gap from 3rd review to decision (TMLR's "5 weeks from beginning of discussion")
df['gap_3rd'] = (df['t_decision'] - df['t_third_review']) / (1000*60*60*24)
# Gap from 1st review to decision
df['gap_1st'] = (df['t_decision'] - df['t_first_review']) / (1000*60*60*24)

# Uncensored: has decision AND has 3rd review AND positive gap
unc = df[df['has_decision'] & df['has_3reviews'] & (df['gap_3rd'] > 0)].copy()
N = len(unc)
gap = unc['gap_3rd']

med = gap.median()
p75 = gap.quantile(0.75)
p90 = gap.quantile(0.90)
p95 = gap.quantile(0.95)
p99 = gap.quantile(0.99)

s28 = (gap > 28).mean() * 100
s35 = (gap > 35).mean() * 100
s42 = (gap > 42).mean() * 100

# Also from 1st review
unc1 = df[df['has_decision'] & df['t_first_review'].notna() & (df['gap_1st'] > 0)].copy()
gap1 = unc1['gap_1st']

print(f"""
=== TMLR Audit Results ===
N (total submissions): {len(df)}
N (with decision): {df['has_decision'].sum()}
N (with ≥3 reviews + decision): {N}
N (censored / no decision): {(~df['has_decision']).sum()}

--- From 3rd review to decision (TMLR policy: ≤35 days) ---
Quantiles (days):
  Median: {med:.1f}
  75th:   {p75:.1f}
  90th:   {p90:.1f}
  95th:   {p95:.1f}
  99th:   {p99:.1f}

Compliance:
  Share > 28 days: {s28:.1f}%
  Share > 35 days: {s35:.1f}% (violates 5-week policy)
  Share > 42 days: {s42:.1f}%

--- From 1st review to decision ---
  N: {len(unc1)}
  Median: {gap1.median():.1f} days
  75th:   {gap1.quantile(0.75):.1f}
  90th:   {gap1.quantile(0.90):.1f}
  95th:   {gap1.quantile(0.95):.1f}
""")