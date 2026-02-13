import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Found {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', [])
    
    # Find review timestamps - check 'invitations' list for '/-/Review'
    review_times = []
    decision_times = []
    
    for r in replies:
        invs = r.get('invitations', [])
        inv_str = ' '.join(invs)
        
        if '/-/Review' in inv_str and 'Official' not in inv_str:
            review_times.append(r['cdate'])
        elif '/-/Decision' in inv_str:
            decision_times.append(r['cdate'])
    
    # We want the THIRD review (when discussion begins), not the first
    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    t_decision = min(decision_times) if decision_times else None
    
    records.append({
        'id': note.id,
        'n_reviews': len(review_times),
        't_third_review': t_third_review,
        't_decision': t_decision,
        'censored': t_decision is None
    })

df = pd.DataFrame(records)

# Compute gap in days (timestamps are in ms)
df['gap_days'] = (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24)

# Filter to uncensored submissions with valid data
valid = df[(~df['censored']) & (df['t_third_review'].notna()) & (df['gap_days'].notna())]
gaps = valid['gap_days']

n = len(gaps)
quantiles = gaps.quantile([0.5, 0.75, 0.9, 0.95, 0.99])
share_28 = (gaps > 28).mean() * 100
share_35 = (gaps > 35).mean() * 100
share_42 = (gaps > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored with 3+ reviews): {n}

Quantiles (days from 3rd review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.9]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated timelines:
  Share > 28 days: {share_28:.1f}% (violates "no later than 4 weeks")
  Share > 35 days: {share_35:.1f}% (violates 5-week total)
  Share > 42 days: {share_42:.1f}%

Context:
  Censored (no decision): {df['censored'].sum()}
  Fewer than 3 reviews: {(df['n_reviews'] < 3).sum()}
""")