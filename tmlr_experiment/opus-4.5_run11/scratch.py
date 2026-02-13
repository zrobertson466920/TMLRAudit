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
    
    # Each review has a unique ID - collect review timestamps by unique review IDs
    review_times = []
    decision_times = []
    
    for r in replies:
        invs = r.get('invitations', [])
        
        # Check if this is a review (has /-/Review in invitations list)
        is_review = any(inv.endswith('/-/Review') for inv in invs)
        is_decision = any(inv.endswith('/-/Decision') for inv in invs)
        
        if is_review:
            review_times.append(r['cdate'])
        if is_decision:
            decision_times.append(r['cdate'])
    
    # Sort to get third review
    review_times.sort()
    n_reviews = len(review_times)
    t_third_review = review_times[2] if n_reviews >= 3 else None
    t_first_review = review_times[0] if n_reviews >= 1 else None
    t_decision = min(decision_times) if decision_times else None
    
    gap_from_third = None
    gap_from_first = None
    if t_third_review and t_decision:
        gap_from_third = (t_decision - t_third_review) / (1000 * 60 * 60 * 24)
    if t_first_review and t_decision:
        gap_from_first = (t_decision - t_first_review) / (1000 * 60 * 60 * 24)
    
    records.append({
        'id': note.id,
        'n_reviews': n_reviews,
        't_third_review': t_third_review,
        't_decision': t_decision,
        'gap_from_third': gap_from_third,
        'gap_from_first': gap_from_first,
        'has_decision': t_decision is not None
    })

df = pd.DataFrame(records)

print(f"\nData summary:")
print(f"  Total submissions: {len(df)}")
print(f"  With 1+ reviews: {(df['n_reviews'] >= 1).sum()}")
print(f"  With 3+ reviews: {(df['n_reviews'] >= 3).sum()}")
print(f"  With decisions: {df['has_decision'].sum()}")

# Filter to papers with 3+ reviews and a decision, positive gap
valid = df[(df['has_decision']) & (df['gap_from_third'].notna()) & (df['gap_from_third'] > 0)]
gap = valid['gap_from_third']

n = len(valid)
if n > 0:
    quantiles = gap.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
    pct_gt_28 = (gap > 28).mean() * 100
    pct_gt_35 = (gap > 35).mean() * 100
    pct_gt_42 = (gap > 42).mean() * 100

    print(f"""
=== TMLR Audit Results ===
N (uncensored, 3+ reviews): {n}

Quantiles (days from THIRD review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "within 5 weeks of third review":
  Share > 28 days: {pct_gt_28:.1f}%
  Share > 35 days: {pct_gt_35:.1f}% (violates 5-week guideline)
  Share > 42 days: {pct_gt_42:.1f}%
""")

    # Also from first review
    gap_first = valid['gap_from_first']
    print(f"For reference (days from FIRST review to decision):")
    print(f"  Median: {gap_first.median():.1f}")
    print(f"  Share > 35 days: {(gap_first > 35).mean() * 100:.1f}%")
else:
    print("No valid data found!")
    # Debug: show review count distribution
    print("\nReview count distribution:")
    print(df['n_reviews'].value_counts().sort_index().head(10))