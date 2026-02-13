import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Fetch all submissions with replies
print("Fetching TMLR submissions with replies (paginated)...")
all_subs = []
offset = 0
batch_size = 1000
while True:
    batch = client.get_notes(
        invitation='TMLR/-/Submission', details='replies',
        limit=batch_size, offset=offset
    )
    if not batch:
        break
    all_subs.extend(batch)
    print(f"  Fetched {len(all_subs)} so far...")
    if len(batch) < batch_size:
        break
    offset += batch_size
print(f"Total submissions: {len(all_subs)}")

# Extract timing data
records = []
for note in all_subs:
    replies = (note.details or {}).get('replies', [])
    review_times = []
    decision_times = []
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if cdate is None:
            continue
        # Reviews: has /-/Review but not only Review_Release
        if any('/-/Review' in inv for inv in invs) and \
           not all('Review_Release' in inv for inv in invs):
            review_times.append(cdate)
        if any('/-/Decision' in inv for inv in invs):
            decision_times.append(cdate)
    
    review_times.sort()
    n_reviews = len(review_times)
    t_first_rev = review_times[0] if review_times else None
    t_third_rev = review_times[2] if n_reviews >= 3 else None
    t_last_rev = review_times[-1] if review_times else None
    t_dec = min(decision_times) if decision_times else None
    
    records.append({
        'id': note.id, 'number': note.number,
        'n_reviews': n_reviews,
        't_first_review': t_first_rev,
        't_third_review': t_third_rev,
        't_last_review': t_last_rev,
        't_decision': t_dec
    })

df = pd.DataFrame(records)
MS_PER_DAY = 1000 * 60 * 60 * 24

# Primary metric: third review → decision (matches TMLR policy)
mask3 = df['t_third_review'].notna() & df['t_decision'].notna()
df.loc[mask3, 'gap_3rd_to_dec'] = (df.loc[mask3, 't_decision'] - df.loc[mask3, 't_third_review']) / MS_PER_DAY

# Secondary: first review → decision
mask1 = df['t_first_review'].notna() & df['t_decision'].notna()
df.loc[mask1, 'gap_1st_to_dec'] = (df.loc[mask1, 't_decision'] - df.loc[mask1, 't_first_review']) / MS_PER_DAY

# Also: last review → decision
maskL = df['t_last_review'].notna() & df['t_decision'].notna()
df.loc[maskL, 'gap_last_to_dec'] = (df.loc[maskL, 't_decision'] - df.loc[maskL, 't_last_review']) / MS_PER_DAY

def print_stats(series, label):
    s = series.dropna()
    print(f"\n--- {label} ---")
    print(f"N: {len(s)}")
    print(f"Quantiles (days):")
    for q, ql in [(0.50,'Median'),(0.75,'75th'),(0.90,'90th'),(0.95,'95th'),(0.99,'99th')]:
        print(f"  {ql:8s}: {s.quantile(q):.1f}")
    print(f"Mean: {s.mean():.1f}  Std: {s.std():.1f}")
    print(f"Compliance:")
    for t, n in [(28,' (TMLR stated max for recommendations)'),(35,' (5-week total)'),(42,''),(56,'')]:
        print(f"  Share > {t:2d} days: {(s>t).mean()*100:.1f}%{n}")

print(f"=== TMLR Decision Timeline Audit ===")
print(f"Total submissions: {len(df)}")
print(f"With ≥3 reviews + decision: {mask3.sum()}")
print(f"With reviews, no decision yet: {(df['t_first_review'].notna() & df['t_decision'].isna()).sum()}")
print(f"No reviews yet: {df['t_first_review'].isna().sum()}")
print(f"\nReview count distribution:")
print(df['n_reviews'].value_counts().sort_index().to_string())

print_stats(df['gap_3rd_to_dec'], "3rd review → decision (TMLR policy clock)")
print_stats(df['gap_1st_to_dec'], "1st review → decision")
print_stats(df['gap_last_to_dec'], "Last review → decision")