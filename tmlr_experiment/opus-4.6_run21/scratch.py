import openreview
import pandas as pd
import numpy as np
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Fetch all TMLR submissions
print("Fetching all TMLR submissions...")
t0 = time.time()
submissions = client.get_all_notes(invitation='TMLR/-/Submission')
print(f"Fetched {len(submissions)} submissions in {time.time()-t0:.1f}s")

# For each submission, fetch forum notes and extract review/decision times
records = []
t0 = time.time()
for i, sub in enumerate(submissions):
    if (i+1) % 500 == 0:
        elapsed = time.time() - t0
        eta = elapsed / (i+1) * (len(submissions) - i - 1)
        print(f"  Processing {i+1}/{len(submissions)} ({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")
    
    try:
        notes = client.get_all_notes(forum=sub.forum)
    except Exception:
        continue
    
    review_times = []
    decision_time = None
    
    for note in notes:
        if note.id == sub.id:
            continue  # skip the submission itself
        invs = note.invitations
        inv_str = ' '.join(invs)
        
        if '/Review' in inv_str and '/Decision' not in inv_str:
            review_times.append(note.cdate)
        elif '/Decision' in inv_str:
            if decision_time is None or note.cdate < decision_time:
                decision_time = note.cdate
    
    if not review_times:
        continue
    
    review_times.sort()
    t_third = review_times[2] if len(review_times) >= 3 else None
    t_first = review_times[0]
    censored = decision_time is None
    
    rec = {
        'forum': sub.forum,
        'n_reviews': len(review_times),
        't_first_review': t_first,
        't_third_review': t_third,
        't_decision': decision_time,
        'censored': censored,
    }
    
    if not censored and t_third is not None:
        rec['gap_from_third'] = (decision_time - t_third) / (1000*60*60*24)
    if not censored:
        rec['gap_from_first'] = (decision_time - t_first) / (1000*60*60*24)
    
    records.append(rec)

elapsed = time.time() - t0
print(f"Processed all submissions in {elapsed:.0f}s")

df = pd.DataFrame(records)
print(f"\nTotal submissions with reviews: {len(df)}")
print(f"  With 3+ reviews: {(df['n_reviews'] >= 3).sum()}")
print(f"  Censored (no decision): {df['censored'].sum()}")
print(f"  Uncensored with 3+ reviews: {((~df['censored']) & (df['n_reviews'] >= 3)).sum()}")

# Filter: uncensored with 3+ reviews (so gap_from_third exists)
unc = df[(~df['censored']) & (df['n_reviews'] >= 3)].copy()
gap = unc['gap_from_third']

print(f"\n=== TMLR Audit Results ===")
print(f"N (uncensored, 3+ reviews): {len(unc)}")
print(f"\nQuantiles (days from 3rd review to decision):")
for q, label in [(0.50, 'Median'), (0.75, '75th'), (0.90, '90th'), (0.95, '95th'), (0.99, '99th')]:
    print(f"  {label:8s}: {gap.quantile(q):6.1f}")

print(f"\nCompliance with stated 'no later than 4 weeks' (from 3rd review):")
print(f"  Share > 28 days: {100*(gap > 28).mean():5.1f}%  (violates stated max)")
print(f"  Share > 35 days: {100*(gap > 35).mean():5.1f}%")
print(f"  Share > 42 days: {100*(gap > 42).mean():5.1f}%")

# Also show from first review
gap2 = df[~df['censored']]['gap_from_first'].dropna()
print(f"\nQuantiles (days from 1st review to decision):")
for q, label in [(0.50, 'Median'), (0.75, '75th'), (0.90, '90th'), (0.95, '95th'), (0.99, '99th')]:
    print(f"  {label:8s}: {gap2.quantile(q):6.1f}")
print(f"\n  Share > 35 days: {100*(gap2 > 35).mean():5.1f}%")
print(f"  Share > 42 days: {100*(gap2 > 42).mean():5.1f}%")