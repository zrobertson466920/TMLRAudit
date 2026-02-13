import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions with replies...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Found {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', []) if note.details else []
    
    # Find review timestamps (invitations containing 'Review' but not 'Official_Comment')
    review_times = []
    for r in replies:
        invs = r.get('invitations', [])
        if any('/-/Review' in inv for inv in invs):
            review_times.append(r.get('cdate'))
    
    # Find decision timestamp
    decision_times = []
    for r in replies:
        invs = r.get('invitations', [])
        if any('/-/Decision' in inv for inv in invs):
            decision_times.append(r.get('cdate'))
    
    # Use third review (start of discussion) per spec, or earliest if <3
    review_times = sorted([t for t in review_times if t])
    t_third_review = review_times[2] if len(review_times) >= 3 else (review_times[0] if review_times else None)
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

# Filter to uncensored with valid data (3+ reviews and positive gap)
analyzed = df[(~df['censored']) & (df['n_reviews'] >= 3) & (df['gap_days'] > 0)].copy()

n = len(analyzed)
gaps = analyzed['gap_days']

print("\n=== TMLR Audit Results ===")
print(f"N (uncensored with 3+ reviews): {n}")
print(f"\nQuantiles (days from third review to decision):")
print(f"  Median: {gaps.quantile(0.50):.1f}")
print(f"  75th:   {gaps.quantile(0.75):.1f}")
print(f"  90th:   {gaps.quantile(0.90):.1f}")
print(f"  95th:   {gaps.quantile(0.95):.1f}")
print(f"  99th:   {gaps.quantile(0.99):.1f}")

print(f"\nCompliance with stated 'no later than 5 weeks' (35 days):")
print(f"  Share > 28 days: {100 * (gaps > 28).mean():.1f}%")
print(f"  Share > 35 days: {100 * (gaps > 35).mean():.1f}% (violates 5-week guideline)")
print(f"  Share > 42 days: {100 * (gaps > 42).mean():.1f}%")

print(f"\nAdditional context:")
print(f"  Total submissions: {len(df)}")
print(f"  With decision: {(~df['censored']).sum()}")
print(f"  With 3+ reviews: {(df['n_reviews'] >= 3).sum()}")
print(f"  Mean gap: {gaps.mean():.1f} days")