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
    replies = note.details.get('replies', [])
    if not replies:
        continue

    review_times = []
    decision_times = []

    for reply in replies:
        invs = reply.get('invitations', [])
        cdate = reply.get('cdate')
        if cdate is None:
            continue
        for inv in invs:
            if '/-/Review' in inv and 'Release' not in inv:
                review_times.append(cdate)
            if '/-/Decision' in inv and 'Release' not in inv:
                decision_times.append(cdate)

    t_first_review = min(review_times) if review_times else None
    t_decision = min(decision_times) if decision_times else None
    censored = t_decision is None
    has_reviews = t_first_review is not None

    gap = None
    if t_first_review and t_decision:
        gap = (t_decision - t_first_review) / MS_PER_DAY

    records.append({
        'forum': note.forum,
        't_first_review': t_first_review,
        't_decision': t_decision,
        'gap_days': gap,
        'censored': censored,
        'has_reviews': has_reviews,
        'n_reviews': len(review_times),
    })

df = pd.DataFrame(records)
uncensored = df[(~df['censored']) & df['has_reviews']].copy()
gaps = uncensored['gap_days'].dropna()

print(f"\n=== TMLR Audit Results ===")
print(f"N (total submissions):    {len(df)}")
print(f"N (with reviews):         {df['has_reviews'].sum()}")
print(f"N (uncensored, with gap): {len(gaps)}")
print(f"N (censored / pending):   {df['censored'].sum()}")

quantiles = [0.50, 0.75, 0.90, 0.95, 0.99]
labels = ['Median', '75th', '90th', '95th', '99th']
print(f"\nQuantiles (days from first review to decision):")
for label, q in zip(labels, quantiles):
    print(f"  {label:8s}: {gaps.quantile(q):.1f}")

print(f"\nCompliance with stated timelines:")
for threshold, note in [(28, " (4 weeks: reviewer recommendations due)"),
                         (35, " (5 weeks: AE decision due)"),
                         (42, " (6 weeks)")]:
    share = (gaps > threshold).mean() * 100
    print(f"  Share > {threshold} days: {share:.1f}%{note}")

neg = (gaps < 0).sum()
if neg > 0:
    print(f"\n⚠ {neg} submissions have decision BEFORE first review (data anomaly)")

print(f"\nMean gap: {gaps.mean():.1f} days | Std: {gaps.std():.1f} days")
print(f"Min: {gaps.min():.1f} | Max: {gaps.max():.1f}")