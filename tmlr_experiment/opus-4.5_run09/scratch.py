import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions (this takes ~20s)...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Found {len(submissions)} submissions")

records = []
for sub in submissions:
    replies = sub.details.get('replies', []) if sub.details else []
    
    # Find review timestamps - look for 'Review' in invitations list
    review_times = []
    decision_times = []
    
    for r in replies:
        invitations = r.get('invitations', [])
        inv_str = ' '.join(invitations)
        
        # Reviews: contain 'Review' but not 'Meta' or 'Revision' 
        if 'Review' in inv_str and 'Meta' not in inv_str and 'Revision' not in inv_str:
            review_times.append(r['cdate'])
        
        # Decisions: contain 'Decision'
        if 'Decision' in inv_str:
            decision_times.append(r['cdate'])
    
    # We want the THIRD review (start of discussion) per spec
    review_times_sorted = sorted(review_times)
    t_third_review = review_times_sorted[2] if len(review_times_sorted) >= 3 else None
    t_decision = min(decision_times) if decision_times else None
    
    records.append({
        'id': sub.id,
        'n_reviews': len(review_times),
        't_third_review': t_third_review,
        't_decision': t_decision,
        'censored': t_decision is None
    })

df = pd.DataFrame(records)

# Compute gap in days (timestamps are in ms)
df['gap_days'] = (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24)

# Filter to uncensored submissions with valid data (>=3 reviews, has decision, positive gap)
analyzed = df[(~df['censored']) & (df['t_third_review'].notna()) & (df['gap_days'] > 0)].copy()

n = len(analyzed)
quantiles = analyzed['gap_days'].quantile([0.5, 0.75, 0.90, 0.95, 0.99])
share_28 = (analyzed['gap_days'] > 28).mean() * 100
share_35 = (analyzed['gap_days'] > 35).mean() * 100
share_42 = (analyzed['gap_days'] > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored with >=3 reviews): {n}

Quantiles (days from third review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 5 weeks" (35 days):
  Share > 28 days: {share_28:.1f}%
  Share > 35 days: {share_35:.1f}% (violates stated max)
  Share > 42 days: {share_42:.1f}%
""")

# Context
print(f"Context:")
print(f"  {df['censored'].sum()} submissions still pending decision")
print(f"  {(df['n_reviews'] < 3).sum()} submissions with <3 reviews")
print(f"  {len(df) - n - df['censored'].sum()} other exclusions (e.g., decision before 3rd review)")