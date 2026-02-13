import openreview
import pandas as pd
import numpy as np

# Connect to OpenReview API
client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

print("Fetching TMLR submissions...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Found {len(submissions)} submissions")

# Extract timing data
data = []
for note in submissions:
    replies = note.details.get('replies', [])
    
    review_times = []
    decision_times = []
    
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        for inv in invs:
            inv_type = inv.split('/')[-1]
            if inv_type == 'Review':
                review_times.append(cdate)
            elif inv_type == 'Decision':
                decision_times.append(cdate)
    
    # Sort review times to get third review (when discussion begins per TMLR policy)
    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    t_first_review = review_times[0] if review_times else None
    t_decision = min(decision_times) if decision_times else None
    
    gap_from_third = None
    gap_from_first = None
    if t_decision:
        if t_third_review:
            gap_from_third = (t_decision - t_third_review) / (1000 * 60 * 60 * 24)
        if t_first_review:
            gap_from_first = (t_decision - t_first_review) / (1000 * 60 * 60 * 24)
    
    data.append({
        'id': note.id,
        'n_reviews': len(review_times),
        'gap_from_third': gap_from_third,
        'gap_from_first': gap_from_first,
        'censored': t_decision is None
    })

df = pd.DataFrame(data)

# Analysis 1: From THIRD review (TMLR's stated policy baseline)
unc_third = df[(~df['censored']) & (df['gap_from_third'].notna())]
gaps_third = unc_third['gap_from_third']

# Analysis 2: From FIRST review (more conservative)
unc_first = df[(~df['censored']) & (df['gap_from_first'].notna())]
gaps_first = unc_first['gap_from_first']

def print_stats(gaps, label):
    n = len(gaps)
    q = np.percentile(gaps, [50, 75, 90, 95, 99])
    print(f"\n--- {label} ---")
    print(f"N: {n}")
    print(f"Quantiles (days):")
    print(f"  Median: {q[0]:.1f}")
    print(f"  75th:   {q[1]:.1f}")
    print(f"  90th:   {q[2]:.1f}")
    print(f"  95th:   {q[3]:.1f}")
    print(f"  99th:   {q[4]:.1f}")
    print(f"Compliance:")
    print(f"  > 28 days: {(gaps > 28).mean()*100:.1f}%")
    print(f"  > 35 days: {(gaps > 35).mean()*100:.1f}%")
    print(f"  > 42 days: {(gaps > 42).mean()*100:.1f}%")
    print(f"Range: {gaps.min():.1f} to {gaps.max():.1f} days")

print("\n=== TMLR Audit Results ===")
print(f"Total submissions: {len(df)}")
print(f"Censored (pending): {df['censored'].sum()}")
print(f"With <3 reviews: {(df['n_reviews'] < 3).sum()}")

print_stats(gaps_third, "From THIRD review (TMLR policy baseline)")
print_stats(gaps_first, "From FIRST review (conservative)")