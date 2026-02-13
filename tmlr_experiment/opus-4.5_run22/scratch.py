import openreview
import pandas as pd
import numpy as np

# Connect to OpenReview API
client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Fetch all TMLR submissions with replies
print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Found {len(submissions)} submissions")

# Extract timing data
records = []
for note in submissions:
    replies = note.details.get('replies', [])
    
    review_times = []
    decision_times = []
    
    for r in replies:
        invitations = r.get('invitations', [])
        cdate = r.get('cdate')
        
        for inv in invitations:
            if '/Review' in inv and 'Revision' not in inv:
                review_times.append(cdate)
                break
            if '/Decision' in inv:
                decision_times.append(cdate)
                break
    
    # Sort review times to get 1st and 3rd
    review_times_sorted = sorted(review_times) if review_times else []
    t_first_review = review_times_sorted[0] if len(review_times_sorted) >= 1 else None
    t_third_review = review_times_sorted[2] if len(review_times_sorted) >= 3 else None
    t_decision = min(decision_times) if decision_times else None
    
    records.append({
        'id': note.id,
        'n_reviews': len(review_times),
        't_first_review': t_first_review,
        't_third_review': t_third_review,
        't_decision': t_decision,
        'censored': t_decision is None
    })

df = pd.DataFrame(records)

# Compute gaps in days
df['gap_from_first'] = (df['t_decision'] - df['t_first_review']) / (1000 * 60 * 60 * 24)
df['gap_from_third'] = (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24)

# Filter to uncensored with valid data (has 3+ reviews and decision)
uncensored = df[(~df['censored']) & (df['t_third_review'].notna()) & (df['gap_from_third'] > 0)]

n = len(uncensored)
gap = uncensored['gap_from_third']

quantiles = gap.quantile([0.5, 0.75, 0.9, 0.95, 0.99])
share_gt_28 = (gap > 28).mean() * 100
share_gt_35 = (gap > 35).mean() * 100
share_gt_42 = (gap > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (uncensored with 3+ reviews): {n}

Quantiles (days from THIRD review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.9]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 5 weeks after 3rd review":
  Share > 28 days: {share_gt_28:.1f}%
  Share > 35 days: {share_gt_35:.1f}% (violates stated 5-week max)
  Share > 42 days: {share_gt_42:.1f}%

Additional stats:
  Total submissions: {len(df)}
  With 3+ reviews: {(df['n_reviews'] >= 3).sum()}
  Pending decision (3+ reviews): {(df['t_third_review'].notna() & df['censored']).sum()}
""")