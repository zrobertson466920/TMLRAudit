import openreview
import pandas as pd
import numpy as np
from collections import defaultdict
import random

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = list(client.get_all_notes(invitation='TMLR/-/Submission'))
print(f"Found {len(submissions)} total")

# Very small sample for speed
random.seed(42)
SAMPLE_SIZE = 50
sampled = random.sample(submissions, SAMPLE_SIZE)

print(f"Processing {SAMPLE_SIZE} samples...")

records = []
for i, sub in enumerate(sampled):
    print(f"{i+1}/{SAMPLE_SIZE}", end=" ", flush=True)
    
    replies = list(client.get_all_notes(forum=sub.forum))
    
    review_times = []
    decision_time = None
    
    for r in replies:
        invs = getattr(r, 'invitations', []) or []
        for inv in invs:
            if '/-/Review' in inv:
                review_times.append(r.cdate)
                break
        for inv in invs:
            if '/-/Decision' in inv:
                decision_time = r.cdate
                break
    
    review_times.sort()
    t3 = review_times[2] if len(review_times) >= 3 else None
    
    gap = None
    if t3 and decision_time:
        gap = (decision_time - t3) / (1000 * 60 * 60 * 24)
    
    records.append({'gap': gap, 'censored': decision_time is None, 'n_rev': len(review_times)})

print("\n")
df = pd.DataFrame(records)
unc = df[(~df['censored']) & (df['gap'].notna()) & (df['gap'] > 0)]

if len(unc) > 0:
    gaps = unc['gap']
    q = gaps.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
    print(f"=== TMLR Audit (n={SAMPLE_SIZE} sample) ===")
    print(f"Uncensored: {len(unc)}")
    print(f"Median: {q[0.5]:.1f} days")
    print(f"75th: {q[0.75]:.1f}, 90th: {q[0.90]:.1f}, 95th: {q[0.95]:.1f}")
    print(f">28 days: {(gaps>28).mean()*100:.0f}%")
    print(f">35 days: {(gaps>35).mean()*100:.0f}%")
    print(f">42 days: {(gaps>42).mean()*100:.0f}%")
else:
    print("No uncensored samples found")
print(f"Censored: {df['censored'].sum()}, <3 reviews: {(df['n_rev']<3).sum()}")