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
    
    # Find review timestamps - invitations is a list, check if any contain 'Review'
    review_times = [r['cdate'] for r in replies 
                   if any('Official_Review' in inv or '/Review' in inv for inv in r.get('invitations', []))]
    
    # Find decision timestamp
    decision_times = [r['cdate'] for r in replies 
                     if any('Decision' in inv for inv in r.get('invitations', []))]
    
    t_reviews_public = min(review_times) if review_times else None
    t_decision = min(decision_times) if decision_times else None
    
    # Compute gap in days
    gap_days = None
    if t_reviews_public and t_decision:
        gap_days = (t_decision - t_reviews_public) / (1000 * 60 * 60 * 24)
    
    records.append({
        'id': note.id,
        't_reviews_public': t_reviews_public,
        't_decision': t_decision,
        'gap_days': gap_days,
        'censored': t_decision is None
    })
    
    # Find review timestamps (look for 'Review' in invitation)
    review_times = [r['cdate'] for r in replies if 'Review' in r.get('invitation', '') 
                   and 'Official_Review' in r.get('invitation', '')]
    
    # Find decision timestamp
    decision_times = [r['cdate'] for r in replies if 'Decision' in r.get('invitation', '')]
    
    t_reviews_public = min(review_times) if review_times else None
    t_decision = min(decision_times) if decision_times else None
    
    # Compute gap in days
    gap_days = None
    if t_reviews_public and t_decision:
        gap_days = (t_decision - t_reviews_public) / (1000 * 60 * 60 * 24)
    
    records.append({
        'id': note.id,
        't_reviews_public': t_reviews_public,
        't_decision': t_decision,
        'gap_days': gap_days,
        'censored': t_decision is None
    })

df = pd.DataFrame(records)

# Filter to uncensored (have both reviews and decision)
uncensored = df[(~df['censored']) & (df['gap_days'].notna())]
gaps = uncensored['gap_days']

# Compute statistics
n = len(gaps)
quantiles = gaps.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
share_28 = (gaps > 28).mean() * 100
share_35 = (gaps > 35).mean() * 100
share_42 = (gaps > 42).mean() * 100

# Output
print("\n=== TMLR Audit Results ===")
print(f"N (uncensored): {n}")
print(f"\nQuantiles (days from first review to decision):")
print(f"  Median: {quantiles[0.5]:.1f}")
print(f"  75th:   {quantiles[0.75]:.1f}")
print(f"  90th:   {quantiles[0.90]:.1f}")
print(f"  95th:   {quantiles[0.95]:.1f}")
print(f"  99th:   {quantiles[0.99]:.1f}")
print(f"\nCompliance with stated 'no later than 4 weeks':")
print(f"  Share > 28 days: {share_28:.1f}% (violates stated max)")
print(f"  Share > 35 days: {share_35:.1f}%")
print(f"  Share > 42 days: {share_42:.1f}%")