import openreview
import pandas as pd
import numpy as np
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching all TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission')
print(f"  {len(submissions)} submissions")

records = []
t0 = time.time()
for i, sub in enumerate(submissions):
    if i % 500 == 0 and i > 0:
        elapsed = time.time() - t0
        rate = i / elapsed
        eta = (len(submissions) - i) / rate
        print(f"  Processing {i}/{len(submissions)} ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")

    replies = client.get_notes(forum=sub.id)

    review_cdates = []
    decision_cdate = None
    for r in replies:
        if r.id == sub.id:
            continue
        invs = r.invitations if hasattr(r, 'invitations') else []
        inv_str = ' '.join(invs)
        if '/-/Review' in inv_str and 'Official_Comment' not in inv_str and 'Decision' not in inv_str:
            review_cdates.append(r.cdate)
        if '/-/Decision' in inv_str:
            if decision_cdate is None or r.cdate < decision_cdate:
                decision_cdate = r.cdate

    review_cdates.sort()
    records.append({
        'id': sub.id,
        'number': sub.number,
        'n_reviews': len(review_cdates),
        't_first_review': review_cdates[0] if review_cdates else None,
        't_third_review': review_cdates[2] if len(review_cdates) >= 3 else None,
        't_decision': decision_cdate,
    })

elapsed = time.time() - t0
print(f"  Done in {elapsed:.0f}s")

df = pd.DataFrame(records)
df['has_decision'] = df['t_decision'].notna()

print(f"\nTotal submissions: {len(df)}")
print(f"  With ≥1 review: {(df['n_reviews'] >= 1).sum()}")
print(f"  With ≥3 reviews: {(df['n_reviews'] >= 3).sum()}")
print(f"  With decision: {df['has_decision'].sum()}")

# Gap: 3rd review to decision
mask = df['has_decision'] & df['t_third_review'].notna()
df_unc = df[mask].copy()
df_unc['gap_days'] = (df_unc['t_decision'] - df_unc['t_third_review']) / (1000*60*60*24)

neg = (df_unc['gap_days'] < 0).sum()
if neg > 0:
    print(f"  Warning: {neg} with negative gap, excluding")
    df_unc = df_unc[df_unc['gap_days'] >= 0]

N = len(df_unc)
gap = df_unc['gap_days']

print(f"\n{'='*50}")
print(f"=== TMLR Audit Results ===")
print(f"N (uncensored, ≥3 reviews + decision): {N}")

print(f"\nQuantiles (days from 3rd review to decision):")
for q, label in [(0.50,'Median'),(0.75,'75th'),(0.90,'90th'),(0.95,'95th'),(0.99,'99th')]:
    print(f"  {label:8s}: {gap.quantile(q):.1f}")

print(f"\nCompliance with TMLR timelines:")
print(f"  (Policy: recs ≤4wk after 3rd review, decision ≤1wk after = 35 days)")
for thr, note in [(28,' (4 wk — reviewer rec deadline)'),(35,' (5 wk — decision deadline)'),(42,' (6 wk)'),(56,' (8 wk)')]:
    share = (gap > thr).mean() * 100
    print(f"  Share > {thr} days: {share:.1f}%{note}")

print(f"\nMean: {gap.mean():.1f} days, Std: {gap.std():.1f} days")