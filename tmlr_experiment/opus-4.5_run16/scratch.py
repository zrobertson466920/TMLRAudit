import openreview
import pandas as pd
from collections import defaultdict

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Try to get ALL notes from TMLR venue at once
print("Fetching all TMLR notes (this may take a while)...")
all_notes = client.get_all_notes(content={'venueid': 'TMLR'})
print(f"Found {len(all_notes)} notes with TMLR venueid")

# If that doesn't work well, let's check what we got
if len(all_notes) < 100:
    print("Trying alternative: fetch by domain...")
    all_notes = client.get_all_notes(domain='TMLR')
    print(f"Found {len(all_notes)} notes with TMLR domain")

# Group by forum and categorize
reviews_by_forum = defaultdict(list)
decisions_by_forum = {}

for note in all_notes:
    invs = getattr(note, 'invitations', [])
    inv_str = ' '.join(invs) if invs else ''
    
    if '/-/Review' in inv_str and 'Comment' not in inv_str:
        reviews_by_forum[note.forum].append(note.cdate)
    elif '/-/Decision' in inv_str:
        if note.forum not in decisions_by_forum:
            decisions_by_forum[note.forum] = note.cdate

print(f"Forums with reviews: {len(reviews_by_forum)}")
print(f"Forums with decisions: {len(decisions_by_forum)}")

# Build dataset
records = []
for forum, review_times in reviews_by_forum.items():
    review_times_sorted = sorted(review_times)
    t_third = review_times_sorted[2] if len(review_times_sorted) >= 3 else None
    t_dec = decisions_by_forum.get(forum)
    records.append({
        'forum': forum, 'n_reviews': len(review_times),
        't_third': t_third, 't_dec': t_dec, 'censored': t_dec is None
    })

df = pd.DataFrame(records)
if len(df) > 0:
    df['gap'] = (df['t_dec'] - df['t_third']) / (1000*60*60*24)
    valid = df[(~df['censored']) & df['t_third'].notna() & (df['gap'] > 0)]
    gap = valid['gap']
    
    print(f"\n=== TMLR Audit Results ===")
    print(f"N: {len(valid)}")
    print(f"Median: {gap.quantile(0.5):.1f}, 90th: {gap.quantile(0.9):.1f}, 99th: {gap.quantile(0.99):.1f}")
    print(f">28d: {100*(gap>28).mean():.1f}%, >35d: {100*(gap>35).mean():.1f}%, >42d: {100*(gap>42).mean():.1f}%")
else:
    print("No data collected")