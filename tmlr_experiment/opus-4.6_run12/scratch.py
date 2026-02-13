import openreview
import pandas as pd
import numpy as np
from collections import defaultdict

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Bulk fetch ALL notes across all TMLR papers using prefix wildcard
print("Fetching all TMLR paper notes (reviews, decisions, comments, etc.)...")
all_notes = client.get_all_notes(invitation='TMLR/Paper.*')
print(f"  Fetched {len(all_notes)} notes total")

# Classify each note by checking its invitations list
review_times_by_forum = defaultdict(list)
decision_times_by_forum = {}

for note in all_notes:
    invitations = getattr(note, 'invitations', [])
    inv_str = ' '.join(invitations)
    forum = note.forum
    cdate = note.cdate

    # Reviews: invitation contains '/-/Review' but not 'Review_Release' alone
    if any(i.endswith('/-/Review') or i.endswith('/-/Official_Review') for i in invitations):
        review_times_by_forum[forum].append(cdate)

    # Decisions: invitation contains '/-/Decision'
    if any(i.endswith('/-/Decision') for i in invitations):
        if forum not in decision_times_by_forum or cdate < decision_times_by_forum[forum]:
            decision_times_by_forum[forum] = cdate

print(f"  Forums with reviews: {len(review_times_by_forum)}")
print(f"  Forums with decisions: {len(decision_times_by_forum)}")

# Compute 3rd review time per forum
third_review = {}
for forum, times in review_times_by_forum.items():
    times.sort()
    if len(times) >= 3:
        third_review[forum] = times[2]

print(f"  Forums with 3+ reviews: {len(third_review)}")

# Build dataset
records = []
for forum in set(list(third_review.keys()) | set(decision_times_by_forum.keys())):
    t3 = third_review.get(forum)
    td = decision_times_by_forum.get(forum)
    has_both = t3 is not None and td is not None
    gap = (td - t3) / (1000 * 60 * 60 * 24) if has_both else np.nan
    records.append({'forum': forum, 't3': t3, 'td': td, 'gap_days': gap, 'has_both': has_both})

df = pd.DataFrame(records)
valid = df[df['has_both']].copy()
gaps = valid['gap_days']
N = len(gaps)

quantiles = gaps.quantile([0.5, 0.75, 0.90, 0.95, 0.99])
share_28 = (gaps > 28).mean() * 100
share_35 = (gaps > 35).mean() * 100
share_42 = (gaps > 42).mean() * 100

print(f"""
=== TMLR Audit Results ===
N (with 3+ reviews AND decision): {N}

Quantiles (days from 3rd review to decision):
  Median: {quantiles[0.50]:.1f}
  75th:   {quantiles[0.75]:.1f}
  90th:   {quantiles[0.90]:.1f}
  95th:   {quantiles[0.95]:.1f}
  99th:   {quantiles[0.99]:.1f}

Compliance with stated "no later than 5 weeks" (3rd review to decision):
  Share > 28 days: {share_28:.1f}%
  Share > 35 days: {share_35:.1f}%
  Share > 42 days: {share_42:.1f}%

Memo:
  Total paper-level notes fetched: {len(all_notes)}
  Forums with 3+ reviews: {len(third_review)}
  Forums with a decision: {len(decision_times_by_forum)}
  Censored (3+ reviews, no decision): {len(set(third_review.keys()) - set(decision_times_by_forum.keys()))}
  Negative gaps (decision before 3rd review): {(gaps < 0).sum()}
""")