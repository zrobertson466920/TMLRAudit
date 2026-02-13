import openreview
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

# Connect to OpenReview API
client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Fetch all Review_Release notes in bulk
print("Fetching all TMLR Review_Release notes...")
review_releases = client.get_all_notes(invitation='TMLR/Paper.*/-/Review_Release', regex=True)
print(f"Found {len(review_releases)} review releases")

# Fetch all Decision notes in bulk
print("Fetching all TMLR Decision notes...")
decisions = client.get_all_notes(invitation='TMLR/Paper.*/-/Decision', regex=True)
print(f"Found {len(decisions)} decisions")

# Group by forum
review_times_by_forum = defaultdict(list)
for r in review_releases:
    review_times_by_forum[r.forum].append(r.cdate)

decision_times_by_forum = {}
for d in decisions:
    if d.forum not in decision_times_by_forum or d.cdate < decision_times_by_forum[d.forum]:
        decision_times_by_forum[d.forum] = d.cdate

# Build records
records = []
for forum, review_times in review_times_by_forum.items():
    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    t_decision = decision_times_by_forum.get(forum)
    
    if t_third_review:
        gap_days = None
        if t_decision:
            gap_days = (t_decision - t_third_review) / (1000 * 60 * 60 * 24)
        
        records.append({
            'forum': forum,
            't_third_review': t_third_review,
            't_decision': t_decision,
            'gap_days': gap_days,
            'censored': t_decision is None
        })

df = pd.DataFrame(records)
print(f"\nSubmissions with 3+ reviews: {len(df)}")
print(f"Submissions with decisions: {(~df['censored']).sum()}")

# Filter to uncensored (have decisions)
uncensored = df[~df['censored']].copy()
gaps = uncensored['gap_days']

# Print results
print("\n=== TMLR Audit Results ===")
print(f"N (uncensored): {len(uncensored)}")

print("\nQuantiles (days from 3rd review to decision):")
print(f"  Median: {gaps.median():.1f}")
print(f"  75th:   {gaps.quantile(0.75):.1f}")
print(f"  90th:   {gaps.quantile(0.90):.1f}")
print(f"  95th:   {gaps.quantile(0.95):.1f}")
print(f"  99th:   {gaps.quantile(0.99):.1f}")

print("\nCompliance with stated timelines:")
print(f"  Share > 28 days: {(gaps > 28).mean()*100:.1f}% (violates 4-week max)")
print(f"  Share > 35 days: {(gaps > 35).mean()*100:.1f}% (violates 5-week guideline)")
print(f"  Share > 42 days: {(gaps > 42).mean()*100:.1f}%")

print(f"\nNote: {df['censored'].sum()} submissions still awaiting decisions (censored)")