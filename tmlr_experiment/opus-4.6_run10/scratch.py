import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
print("Fetching TMLR submissions (this may take a few minutes)...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions. Processing...")

records = []
for note in submissions:
    replies = note.details.get('replies', [])
    if not replies:
        records.append({'id': note.id, 't_third_review': None, 't_decision': None, 'censored': True})
        continue

    review_times = []
    decision_time = None
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if cdate is None:
            continue
        inv_str = ' '.join(invs)
        # Reviews: has /-/Review but not /-/Review_Release alone
        if any(i.endswith('/-/Review') or '/-/Official_Review' in i for i in invs):
            review_times.append(cdate)
        if any('/-/Decision' in i for i in invs):
            if decision_time is None or cdate < decision_time:
                decision_time = cdate

    review_times.sort()
    t_third = review_times[2] if len(review_times) >= 3 else None
    censored = decision_time is None
    records.append({
        'id': note.id,
        'n_reviews': len(review_times),
        't_third_review': t_third,
        't_decision': decision_time,
        'censored': censored,
    })

df = pd.DataFrame(records)
df['gap_days'] = (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24)

# Filter to uncensored with valid gap
unc = df[(~df['censored']) & (df['gap_days'].notna())].copy()
N = len(unc)
g = unc['gap_days']

print(f"\n=== TMLR Audit Results ===")
print(f"Total submissions fetched: {len(df)}")
print(f"  With >=3 reviews: {df['t_third_review'].notna().sum()}")
print(f"  With decision:    {(~df['censored']).sum()}")
print(f"N (uncensored, valid gap): {N}\n")

quantiles = [0.5, 0.75, 0.90, 0.95, 0.99]
labels = ['Median', '75th', '90th', '95th', '99th']
print("Quantiles (days from 3rd review to decision):")
for lbl, q in zip(labels, quantiles):
    print(f"  {lbl:>6s}: {g.quantile(q):6.1f}")

print(f"\nCompliance with stated 'no later than 4 weeks':")
for threshold, tag in [(28, "violates stated max"), (35, ""), (42, "")]:
    share = (g > threshold).mean() * 100
    suffix = f" ({tag})" if tag else ""
    print(f"  Share > {threshold} days: {share:5.1f}%{suffix}")

print(f"\nMean gap: {g.mean():.1f} days")
print(f"Std gap:  {g.std():.1f} days")
print(f"Min gap:  {g.min():.1f} days")
print(f"Max gap:  {g.max():.1f} days")