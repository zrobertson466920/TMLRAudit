import openreview
import pandas as pd
import numpy as np

# Connect to OpenReview API
client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Fetch all TMLR submissions with replies
print("Fetching TMLR submissions...")
submissions = list(client.get_all_notes(invitation='TMLR/-/Submission', details='replies'))
print(f"Fetched {len(submissions)} submissions")

# Extract timing data
records = []
for note in submissions:
    replies = note.details.get('replies', [])
    
    review_times = []
    decision_times = []
    
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if cdate is None:
            continue
            
        if any('/-/Review' in inv and 'Release' not in inv for inv in invs):
            review_times.append(cdate)
        
        if any('/-/Decision' in inv and 'Release' not in inv for inv in invs):
            decision_times.append(cdate)
    
    # Sort reviews to get the third one (when discussion starts per TMLR guidelines)
    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    t_first_review = review_times[0] if review_times else None
    t_decision = min(decision_times) if decision_times else None
    
    # Compute gaps
    gap_from_third = None
    gap_from_first = None
    if t_decision:
        if t_third_review:
            gap_from_third = (t_decision - t_third_review) / (1000 * 60 * 60 * 24)
        if t_first_review:
            gap_from_first = (t_decision - t_first_review) / (1000 * 60 * 60 * 24)
    
    censored = t_decision is None or t_third_review is None
    
    records.append({
        'id': note.id,
        'gap_from_third': gap_from_third,
        'gap_from_first': gap_from_first,
        'censored': censored,
        'n_reviews': len(review_times),
    })

df = pd.DataFrame(records)
df_unc = df[~df['censored']].copy()

# Stats from third review (per spec)
gaps = df_unc['gap_from_third']
n = len(gaps)
q = np.percentile(gaps, [50, 75, 90, 95, 99])

print(f"""
=== TMLR Audit Results ===
N (uncensored with 3+ reviews): {n}

Quantiles (days from THIRD review to decision):
  Median: {q[0]:.1f}
  75th:   {q[1]:.1f}
  90th:   {q[2]:.1f}
  95th:   {q[3]:.1f}
  99th:   {q[4]:.1f}

Compliance with "5 weeks from discussion start":
  Share > 35 days: {(gaps > 35).mean()*100:.1f}%
  Share > 42 days: {(gaps > 42).mean()*100:.1f}%
  Share > 56 days: {(gaps > 56).mean()*100:.1f}%

Additional context:
  Total submissions: {len(df)}
  With 3+ reviews and decision: {n}
  Censored: {df['censored'].sum()}
  Mean reviews per paper: {df['n_reviews'].mean():.1f}
""")