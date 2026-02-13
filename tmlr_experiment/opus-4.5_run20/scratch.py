import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions with directReplies...")
submissions = client.get_all_notes(
    invitation='TMLR/-/Submission', 
    details='directReplies'
)
print(f"Found {len(submissions)} submissions")

records = []
for sub in submissions:
    replies = sub.details.get('directReplies', []) if sub.details else []
    
    review_times = []
    decision_time = None
    
    for r in replies:
        invs = r.get('invitations', [])
        inv_str = ' '.join(invs)
        
        # Look for reviews (but not comments)
        if '/Review' in inv_str and 'Comment' not in inv_str:
            review_times.append(r['cdate'])
        # Look for decisions
        if '/Decision' in inv_str:
            if decision_time is None or r['cdate'] < decision_time:
                decision_time = r['cdate']
    
    # Sort reviews and get the third one
    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    
    records.append({
        'id': sub.id,
        'n_reviews': len(review_times),
        't_third_review': t_third_review,
        't_decision': decision_time,
        'censored': decision_time is None
    })

df = pd.DataFrame(records)

# Compute gap: decision - third review (in days)
df['gap_days'] = (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24)

# Filter to uncensored with valid third review
valid = df[(~df['censored']) & (df['t_third_review'].notna()) & (df['gap_days'].notna())]
gap = valid['gap_days']

n = len(valid)
quantiles = gap.quantile([0.5, 0.75, 0.90, 0.95, 0.99])

share_28 = (gap > 28).mean() * 100
share_35 = (gap > 35).mean() * 100
share_42 = (gap > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored with 3+ reviews): {n}

Quantiles (days from third review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 5 weeks" (35 days):
  Share > 28 days: {share_28:.1f}%
  Share > 35 days: {share_35:.1f}% (violates 5-week target)
  Share > 42 days: {share_42:.1f}%

Additional context:
  Total submissions: {len(df)}
  With decision: {(~df['censored']).sum()}
  With 3+ reviews: {(df['n_reviews'] >= 3).sum()}
""")