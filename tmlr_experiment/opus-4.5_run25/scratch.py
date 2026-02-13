import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions")

def has_inv(invitations, keyword):
    return any(keyword in inv for inv in invitations)

records = []
for note in submissions:
    replies = note.details.get('replies', []) if note.details else []
    
    # Find review timestamps (look for 3rd review = start of discussion)
    review_times = sorted([r['cdate'] for r in replies if has_inv(r.get('invitations', []), 'Review')])
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    
    # Find decision timestamp
    decision_times = [r['cdate'] for r in replies if has_inv(r.get('invitations', []), 'Decision')]
    t_decision = min(decision_times) if decision_times else None
    
    if t_third_review is None:
        continue
    
    censored = t_decision is None
    gap_days = (t_decision - t_third_review) / (1000 * 60 * 60 * 24) if not censored else None
    
    records.append({'id': note.id, 'gap_days': gap_days, 'censored': censored})

df = pd.DataFrame(records)
uncensored = df[~df['censored']]
gaps = uncensored['gap_days']

n = len(uncensored)
print(f"\n=== TMLR Audit Results ===")
print(f"N (uncensored): {n}")
print(f"\nQuantiles (days from 3rd review to decision):")
print(f"  Median: {gaps.median():.1f}")
print(f"  75th:   {gaps.quantile(0.75):.1f}")
print(f"  90th:   {gaps.quantile(0.90):.1f}")
print(f"  95th:   {gaps.quantile(0.95):.1f}")
print(f"  99th:   {gaps.quantile(0.99):.1f}")
print(f"\nCompliance with stated 'no later than 5 weeks':")
print(f"  Share > 28 days: {(gaps > 28).mean() * 100:.1f}%")
print(f"  Share > 35 days: {(gaps > 35).mean() * 100:.1f}% (violates 5-week guideline)")
print(f"  Share > 42 days: {(gaps > 42).mean() * 100:.1f}%")