import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions (this may take a few minutes)...")
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
        if cdate is None:
            continue
        inv_str = ' '.join(invs)
        # Match reviews: contains /-/Review but not Decision
        if '/-/Review' in inv_str and '/-/Decision' not in inv_str:
            review_times.append(cdate)
        # Match decisions
        if '/-/Decision' in inv_str:
            if decision_time is None or cdate < decision_time:
                decision_time = cdate

    review_times.sort()
    # Use 3rd review as start of discussion period (per TMLR policy)
    t_third_review = review_times[2] if len(review_times) >= 3 else None

    records.append({
        'id': note.id,
        't_third_review': t_third_review,
        't_decision': decision_time,
        'n_reviews': len(review_times),
    })

df = pd.DataFrame(records)
df['censored'] = df['t_decision'].isna() | df['t_third_review'].isna()
mask = ~df['censored']
df.loc[mask, 'gap_days'] = (
    (df.loc[mask, 't_decision'] - df.loc[mask, 't_third_review']) / (1000 * 60 * 60 * 24)
)

unc = df.loc[mask, 'gap_days'].dropna()

print(f"\n=== TMLR Audit Results ===")
print(f"N (total submissions): {len(df)}")
print(f"N (with >=3 reviews): {(df['n_reviews'] >= 3).sum()}")
print(f"N (censored / no decision or <3 reviews): {df['censored'].sum()}")
print(f"N (uncensored): {len(unc)}")

quantiles = [0.50, 0.75, 0.90, 0.95, 0.99]
labels = ['Median', '75th', '90th', '95th', '99th']
print(f"\nQuantiles (days from 3rd review to decision):")
for label, q in zip(labels, quantiles):
    print(f"  {label:8s}: {unc.quantile(q):6.1f}")

print(f"\nCompliance with stated 'no later than 4 weeks':")
for threshold, note in [(28, " (violates stated max for recommendations)"),
                         (35, " (5 weeks: recommendations + AE decision)"),
                         (42, "")]:
    share = (unc > threshold).mean() * 100
    print(f"  Share > {threshold} days: {share:5.1f}%{note}")

print(f"\nMean gap: {unc.mean():.1f} days")
print(f"Std gap:  {unc.std():.1f} days")
print(f"Min gap:  {unc.min():.1f} days")
print(f"Max gap:  {unc.max():.1f} days")