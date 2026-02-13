import openreview
import pandas as pd
import numpy as np
from datetime import datetime

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

def ms_to_days(ms):
    return ms / (1000 * 60 * 60 * 24)

# Get all papers with decisions (accepted, rejected, or decision pending that got decided)
print("Fetching TMLR papers with completed reviews...")
# Get papers that have venueid indicating completion
completed_venues = ['TMLR', 'TMLR/Rejected']  # Accepted or Rejected
all_papers = []
for venue in completed_venues:
    papers = client.get_all_notes(content={'venueid': venue})
    print(f"  venueid='{venue}': {len(papers)} papers")
    all_papers.extend(papers)

print(f"\nTotal papers to analyze: {len(all_papers)}")

# Process each paper
records = []
for i, paper in enumerate(all_papers):
    if i % 500 == 0:
        print(f"Processing {i}/{len(all_papers)}...")
    
    # Get all notes in forum
    try:
        forum_notes = client.get_all_notes(forum=paper.forum)
    except:
        continue
    
    # Find review release times
    review_times = []
    decision_time = None
    
    for note in forum_notes:
        inv = note.invitations[-1] if note.invitations else ''
        if 'Review_Release' in inv:
            review_times.append(note.cdate)
        elif 'Decision_Release' in inv:
            decision_time = note.cdate
    
    # We want the THIRD review (when discussion begins per TMLR policy)
    if len(review_times) >= 3 and decision_time:
        review_times_sorted = sorted(review_times)
        third_review = review_times_sorted[2]  # 0-indexed, so index 2 is third
        gap_days = ms_to_days(decision_time - third_review)
        records.append({'id': paper.id, 'gap_days': gap_days, 'n_reviews': len(review_times)})

print(f"\nProcessed. Found {len(records)} papers with 3+ reviews and decision.")

# Analyze
df = pd.DataFrame(records)
valid = df['gap_days']

n = len(valid)
quantiles = valid.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
pct_over_28 = (valid > 28).mean() * 100
pct_over_35 = (valid > 35).mean() * 100
pct_over_42 = (valid > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (with 3+ reviews and decision): {n}

Quantiles (days from 3rd review to decision):
  Median: {quantiles[0.5]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 5 weeks" (35 days):
  Share > 28 days: {pct_over_28:.1f}%
  Share > 35 days: {pct_over_35:.1f}% (violates 5-week max)
  Share > 42 days: {pct_over_42:.1f}%
""")