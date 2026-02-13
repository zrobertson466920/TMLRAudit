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
    
    # Find review timestamps (any invitation containing '/-/Review')
    review_times = []
    decision_times = []
    
    for r in replies:
        invitations = r.get('invitations', [])
        cdate = r.get('cdate')
        if not cdate:
            continue
        
        inv_str = ' '.join(invitations)
        if '/-/Review' in inv_str and '/-/Review_Release' not in inv_str.replace('/-/Review,', ''):
            # Check if it's a review (not just release)
            if any('/-/Review' in inv and 'Release' not in inv for inv in invitations):
                review_times.append(cdate)
        if '/-/Decision' in inv_str:
            decision_times.append(cdate)
    
    t_reviews = min(review_times) if review_times else None
    t_decision = min(decision_times) if decision_times else None
    
    records.append({
        'id': note.id,
        't_reviews': t_reviews,
        't_decision': t_decision,
        'censored': t_decision is None
    })

df = pd.DataFrame(records)

# Compute gap in days for uncensored submissions
df['gap_days'] = np.where(
    ~df['censored'] & df['t_reviews'].notna(),
    (df['t_decision'] - df['t_reviews']) / (1000 * 60 * 60 * 24),
    np.nan
)

# Filter to uncensored with valid gap
uncensored = df[~df['censored'] & df['gap_days'].notna()]['gap_days']

# Compute statistics
n = len(uncensored)
quantiles = uncensored.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
share_28 = (uncensored > 28).mean() * 100
share_35 = (uncensored > 35).mean() * 100
share_42 = (uncensored > 42).mean() * 100

# Print results
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
  Share > 28 days: {share_28:.1f}% (violates stated max)
  Share > 35 days: {share_35:.1f}%
  Share > 42 days: {share_42:.1f}%
""")