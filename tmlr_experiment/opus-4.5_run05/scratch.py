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
data = []
for note in submissions:
    replies = note.details.get('replies', [])
    
    # Find review timestamps (look for 'Review' in invitation)
    review_times = [r['cdate'] for r in replies if 'Review' in r.get('invitation', '') 
                   and 'Official_Review' in r.get('invitation', '')]
    
    # Find decision timestamp
    decision_times = [r['cdate'] for r in replies if 'Decision' in r.get('invitation', '')]
    
    t_reviews_public = min(review_times) if review_times else None
    t_decision = min(decision_times) if decision_times else None
    
    # Only include if we have at least reviews
    if t_reviews_public:
        gap_days = None
        censored = t_decision is None
        if not censored:
            gap_days = (t_decision - t_reviews_public) / (1000 * 60 * 60 * 24)
        
        data.append({
            'id': note.id,
            't_reviews_public': t_reviews_public,
            't_decision': t_decision,
            'gap_days': gap_days,
            'censored': censored
        })

df = pd.DataFrame(data)
print(f"Submissions with reviews: {len(df)}")

# Filter to uncensored only
df_uncensored = df[~df['censored']].copy()
gaps = df_uncensored['gap_days']

# Compute statistics
n = len(gaps)
quantiles = np.percentile(gaps, [50, 75, 90, 95, 99])
share_gt_28 = (gaps > 28).mean() * 100
share_gt_35 = (gaps > 35).mean() * 100
share_gt_42 = (gaps > 42).mean() * 100

# Output results
print(f"""
=== TMLR Audit Results ===
N (uncensored): {n}

Quantiles (days from first review to decision):
  Median: {quantiles[0]:.1f}
  75th:   {quantiles[1]:.1f}
  90th:   {quantiles[2]:.1f}
  95th:   {quantiles[3]:.1f}
  99th:   {quantiles[4]:.1f}

Compliance with stated "no later than 4 weeks":
  Share > 28 days: {share_gt_28:.1f}% (violates stated max)
  Share > 35 days: {share_gt_35:.1f}%
  Share > 42 days: {share_gt_42:.1f}%

Note: Gap measured from first review becoming public to decision.
Censored (no decision yet): {df['censored'].sum()} submissions
""")