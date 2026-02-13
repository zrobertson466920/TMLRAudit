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
    
    # Extract review timestamps (look for 'Review' but not 'Review_Release' alone)
    review_times = []
    decision_time = None
    
    for r in replies:
        invs = r.get('invitations', [])
        inv_types = [i.split('/-/')[-1] for i in invs]
        cdate = r.get('cdate')
        
        if 'Review' in inv_types and cdate:
            review_times.append(cdate)
        if 'Decision' in inv_types and cdate:
            if decision_time is None or cdate < decision_time:
                decision_time = cdate
    
    # Per spec: measure from THIRD review (when discussion begins)
    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    
    records.append({
        'id': note.id,
        'n_reviews': len(review_times),
        't_third_review': t_third_review,
        't_decision': decision_time,
        'censored': decision_time is None
    })

df = pd.DataFrame(records)

# Compute gap: days from third review to decision
df['gap_days'] = np.where(
    ~df['censored'] & df['t_third_review'].notna(),
    (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24),
    np.nan
)

# Filter to uncensored with valid data
analyzed = df[~df['censored'] & df['gap_days'].notna()]['gap_days']

n = len(analyzed)
quantiles = analyzed.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
share_gt_28 = (analyzed > 28).mean() * 100
share_gt_35 = (analyzed > 35).mean() * 100
share_gt_42 = (analyzed > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored): {n}

Quantiles (days from third review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 5 weeks" (4 wks reviewer + 1 wk AE):
  Share > 28 days: {share_gt_28:.1f}%
  Share > 35 days: {share_gt_35:.1f}% (violates 5-week target)
  Share > 42 days: {share_gt_42:.1f}%

Summary:
  Total submissions: {len(df)}
  With 3+ reviews: {(df['n_reviews'] >= 3).sum()}
  With decisions: {(~df['censored']).sum()}
  Analyzed (3+ reviews + decision): {n}
""")