import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = list(client.get_all_notes(invitation='TMLR/-/Submission', details='replies'))
print(f"Found {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', [])
    
    # Find review timestamps (invitations is a list, check if any contains 'Review')
    review_times = []
    decision_times = []
    
    for r in replies:
        invitations = r.get('invitations', [])
        inv_str = ' '.join(invitations)
        
        # Check for reviews (exclude Revision)
        if '/Review' in inv_str and 'Revision' not in inv_str:
            review_times.append(r['cdate'])
        
        # Check for decisions
        if '/Decision' in inv_str:
            decision_times.append(r['cdate'])
    
    # Use earliest review and earliest decision
    t_reviews = min(review_times) if review_times else None
    t_decision = min(decision_times) if decision_times else None
    
    records.append({
        'id': note.id,
        't_reviews': t_reviews,
        't_decision': t_decision,
        'censored': t_decision is None
    })

df = pd.DataFrame(records)

# Compute gap in days (timestamps are in ms)
df['gap_days'] = (df['t_decision'] - df['t_reviews']) / (1000 * 60 * 60 * 24)

# Filter to uncensored submissions with valid data
valid = df[(~df['censored']) & (df['t_reviews'].notna()) & (df['gap_days'].notna())]
gaps = valid['gap_days']

n = len(gaps)
quantiles = gaps.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
pct_gt_28 = (gaps > 28).mean() * 100
pct_gt_35 = (gaps > 35).mean() * 100
pct_gt_42 = (gaps > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored): {n}

Quantiles (days from first review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 4 weeks":
  Share > 28 days: {pct_gt_28:.1f}% (violates stated max)
  Share > 35 days: {pct_gt_35:.1f}%
  Share > 42 days: {pct_gt_42:.1f}%

Note: Censored submissions (no decision yet): {df['censored'].sum()}
      Submissions with reviews but no decision: {((df['t_reviews'].notna()) & df['censored']).sum()}
""")