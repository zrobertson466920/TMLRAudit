import openreview
import pandas as pd
import numpy as np
import re
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Get submissions
print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission')
print(f"Found {len(submissions)} submissions")

# Extract paper numbers
paper_data = []
for s in submissions:
    for inv in s.invitations:
        match = re.search(r'TMLR/Paper(\d+)/', inv)
        if match:
            paper_data.append((int(match.group(1)), s.forum))
            break

# Sample ~500 papers spread across the range for efficiency
paper_data = sorted(set(paper_data))
sample_size = min(500, len(paper_data))
indices = np.linspace(0, len(paper_data)-1, sample_size, dtype=int)
sampled = [paper_data[i] for i in indices]
print(f"Sampling {len(sampled)} papers across range {sampled[0][0]}-{sampled[-1][0]}")

# Fetch data with rate limiting
results = []
for i, (paper_num, forum) in enumerate(sampled):
    if i % 50 == 0:
        print(f"Progress: {i}/{len(sampled)}")
    try:
        reviews = client.get_notes(invitation=f'TMLR/Paper{paper_num}/-/Review')
        decisions = client.get_notes(invitation=f'TMLR/Paper{paper_num}/-/Decision')
        
        review_times = sorted([r.cdate for r in reviews])
        t_third = review_times[2] if len(review_times) >= 3 else None
        t_decision = decisions[0].cdate if decisions else None
        
        results.append({'paper_num': paper_num, 'n_reviews': len(reviews),
                       't_third_review': t_third, 't_decision': t_decision})
    except Exception as e:
        if 'RateLimit' in str(e):
            time.sleep(25)
        continue

df = pd.DataFrame(results)
df['censored'] = df['t_decision'].isna()
mask = ~df['censored'] & df['t_third_review'].notna()
df.loc[mask, 'gap_days'] = (df.loc[mask, 't_decision'] - df.loc[mask, 't_third_review']) / (1000*60*60*24)

analyzed = df.loc[mask & (df['gap_days'] > 0), 'gap_days']
n = len(analyzed)
q = analyzed.quantile([0.5, 0.75, 0.90, 0.95, 0.99])

print(f"""
=== TMLR Audit Results (Sample of {len(sampled)} papers) ===
N (with decision & 3+ reviews): {n}

Quantiles (days from third review to decision):
  Median: {q[0.5]:.1f}
  75th:   {q[0.75]:.1f}
  90th:   {q[0.90]:.1f}
  95th:   {q[0.95]:.1f}
  99th:   {q[0.99]:.1f}

Compliance:
  Share > 28 days: {(analyzed > 28).mean()*100:.1f}%
  Share > 35 days: {(analyzed > 35).mean()*100:.1f}% (violates 5-week target)
  Share > 42 days: {(analyzed > 42).mean()*100:.1f}%
""")