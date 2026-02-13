import openreview
import pandas as pd
import numpy as np

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching all TMLR submissions with replies (this may take several minutes)...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions")

records = []
for note in submissions:
    replies = note.details.get('replies', []) if note.details else []
    
    review_times = []
    decision_times = []
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if not cdate:
            continue
        inv_str = ' '.join(invs)
        if '/-/Review' in inv_str and 'Decision' not in inv_str and 'Review_Release' not in inv_str.replace('/-/Review_Release','').replace('/-/Review ','/-/Review '):
            # Count any invitation that is exactly /-/Review or /-/Review plus Release
            # The key: check if any invitation ends with /-/Review
            for inv in invs:
                if inv.endswith('/-/Review'):
                    review_times.append(cdate)
                    break
        for inv in invs:
            if inv.endswith('/-/Decision'):
                decision_times.append(cdate)
                break

    # Sort review times to get the 3rd review
    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    t_first_review = review_times[0] if review_times else None
    t_dec = min(decision_times) if decision_times else None
    n_reviews = len(review_times)
    
    records.append({
        'forum': note.id,
        'n_reviews': n_reviews,
        't_first_review': t_first_review,
        't_third_review': t_third_review,
        't_decision': t_dec,
    })

df = pd.DataFrame(records)
print(f"With ≥1 review: {(df['n_reviews'] >= 1).sum()}")
print(f"With ≥3 reviews: {(df['n_reviews'] >= 3).sum()}")
print(f"With decisions: {df['t_decision'].notna().sum()}")

# Gap from 3rd review to decision
df['gap_from_3rd'] = (df['t_decision'] - df['t_third_review']) / (1000 * 60 * 60 * 24)
# Gap from 1st review to decision (for comparison)
df['gap_from_1st'] = (df['t_decision'] - df['t_first_review']) / (1000 * 60 * 60 * 24)

# Uncensored: has decision AND has 3rd review AND positive gap
unc3 = df[df['t_decision'].notna() & df['t_third_review'].notna() & (df['gap_from_3rd'] > 0)].copy()
N3 = len(unc3)
g3 = unc3['gap_from_3rd']

unc1 = df[df['t_decision'].notna() & df['t_first_review'].notna() & (df['gap_from_1st'] > 0)].copy()
N1 = len(unc1)
g1 = unc1['gap_from_1st']

def print_stats(label, gaps, N):
    print(f"\n--- {label} (N={N}) ---")
    print(f"  Median: {gaps.median():.1f}")
    print(f"  75th:   {gaps.quantile(0.75):.1f}")
    print(f"  90th:   {gaps.quantile(0.90):.1f}")
    print(f"  95th:   {gaps.quantile(0.95):.1f}")
    print(f"  99th:   {gaps.quantile(0.99):.1f}")
    print(f"  Share > 28 days: {(gaps > 28).mean()*100:.1f}%")
    print(f"  Share > 35 days: {(gaps > 35).mean()*100:.1f}%")
    print(f"  Share > 42 days: {(gaps > 42).mean()*100:.1f}%")

print(f"\n=== TMLR Audit Results ===")
print_stats("Days from THIRD review to decision (TMLR policy: ≤35 days)", g3, N3)
print_stats("Days from FIRST review to decision (for comparison)", g1, N1)

# Review count distribution
print(f"\n--- Review count distribution ---")
print(df['n_reviews'].value_counts().sort_index().to_string())

# How long between 1st and 3rd review?
df['review_spread'] = (df['t_third_review'] - df['t_first_review']) / (1000 * 60 * 60 * 24)
has_spread = df[df['review_spread'].notna() & (df['review_spread'] >= 0)]
print(f"\n--- Days between 1st and 3rd review (N={len(has_spread)}) ---")
print(f"  Median: {has_spread['review_spread'].median():.1f}")
print(f"  75th:   {has_spread['review_spread'].quantile(0.75):.1f}")
print(f"  90th:   {has_spread['review_spread'].quantile(0.90):.1f}")