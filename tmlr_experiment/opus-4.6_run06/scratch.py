import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions (this may take a few minutes)...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions.")

records = []
for note in submissions:
    replies = note.details.get('replies', [])
    if not replies:
        continue

    review_times = []
    decision_times = []
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate', None)
        if cdate is None:
            continue
        inv_str = ' '.join(invs)
        if '/-/Review' in inv_str and '/-/Decision' not in inv_str:
            review_times.append(cdate)
        if '/-/Decision' in inv_str:
            decision_times.append(cdate)

    t_review = min(review_times) if review_times else None
    t_decision = min(decision_times) if decision_times else None
    censored = t_decision is None

    gap = None
    if t_review and t_decision:
        gap = (t_decision - t_review) / (1000 * 60 * 60 * 24)

    records.append({
        'forum': note.forum,
        't_review': t_review,
        't_decision': t_decision,
        'n_reviews': len(review_times),
        'censored': censored,
        'gap_days': gap
    })

df = pd.DataFrame(records)
uncensored = df[(df['censored'] == False) & df['gap_days'].notna()]

N = len(uncensored)
gaps = uncensored['gap_days']

quantiles = gaps.quantile([0.50, 0.75, 0.90, 0.95, 0.99])
share_28 = (gaps > 28).mean() * 100
share_35 = (gaps > 35).mean() * 100
share_42 = (gaps > 42).mean() * 100

print(f"\n=== TMLR Audit Results ===")
print(f"N (uncensored): {N}")
print(f"\nQuantiles (days from earliest review to decision):")
print(f"  Median: {quantiles[0.50]:.1f}")
print(f"  75th:   {quantiles[0.75]:.1f}")
print(f"  90th:   {quantiles[0.90]:.1f}")
print(f"  95th:   {quantiles[0.95]:.1f}")
print(f"  99th:   {quantiles[0.99]:.1f}")
print(f"\nCompliance with stated 'no later than 4 weeks':")
print(f"  Share > 28 days: {share_28:.1f}% (violates stated max)")
print(f"  Share > 35 days: {share_35:.1f}%")
print(f"  Share > 42 days: {share_42:.1f}%")

print(f"\n--- Context ---")
print(f"Total submissions fetched: {len(submissions)}")
print(f"With at least one reply:   {len(df)}")
print(f"Censored (no decision):    {df['censored'].sum()}")
print(f"Uncensored with valid gap: {N}")
print(f"Mean gap (days):           {gaps.mean():.1f}")
print(f"Std gap (days):            {gaps.std():.1f}")