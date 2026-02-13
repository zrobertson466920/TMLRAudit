import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Fetch ALL notes from TMLR in one call - reviews and decisions have Paper in invitation
print("Fetching all TMLR Paper notes (reviews, decisions, etc)...")
all_notes = client.get_all_notes(invitation='TMLR/Paper.*')
print(f"Found {len(all_notes)} notes")

# Categorize by forum and type
review_times = {}
decision_times = {}

for note in all_notes:
    forum = note.forum
    invs = ' '.join(note.invitations) if hasattr(note, 'invitations') else ''
    
    if '/-/Review' in invs and 'Rebuttal' not in invs:
        review_times.setdefault(forum, []).append(note.cdate)
    elif '/-/Decision' in invs:
        decision_times.setdefault(forum, []).append(note.cdate)

print(f"Forums with reviews: {len(review_times)}")
print(f"Forums with decisions: {len(decision_times)}")

# Build dataset
records = []
for forum in set(review_times.keys()) | set(decision_times.keys()):
    r_times = sorted(review_times.get(forum, []))
    d_times = decision_times.get(forum, [])
    
    records.append({
        'n_reviews': len(r_times),
        't_third': r_times[2] if len(r_times) >= 3 else None,
        't_dec': min(d_times) if d_times else None
    })

df = pd.DataFrame(records)
df['gap'] = (df['t_dec'] - df['t_third']) / (1000 * 60 * 60 * 24)
df['censored'] = df['t_dec'].isna()

analyzed = df[(~df['censored']) & (df['gap'].notna()) & (df['gap'] > 0) & (df['n_reviews'] >= 3)]
n = len(analyzed)

if n > 0:
    q = analyzed['gap'].quantile([0.5, 0.75, 0.90, 0.95, 0.99])
    print(f"""
=== TMLR Audit Results ===
N (with decision & 3+ reviews): {n}

Quantiles (days from 3rd review to decision):
  Median: {q[0.5]:.1f}
  75th:   {q[0.75]:.1f}
  90th:   {q[0.90]:.1f}
  95th:   {q[0.95]:.1f}
  99th:   {q[0.99]:.1f}

Compliance:
  Share > 28 days: {(analyzed['gap']>28).mean()*100:.1f}%
  Share > 35 days: {(analyzed['gap']>35).mean()*100:.1f}% (violates 5-week target)
  Share > 42 days: {(analyzed['gap']>42).mean()*100:.1f}%
""")
else:
    print(f"No valid data. Total forums: {len(df)}, Censored: {df['censored'].sum()}")