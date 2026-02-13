import openreview
import pandas as pd
import numpy as np

MS_PER_DAY = 1000 * 60 * 60 * 24

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
print("Fetching TMLR submissions (this may take a few minutes)...")
submissions = client.get_all_notes(invitation='TMLR/-/Submission', details='replies')
print(f"Fetched {len(submissions)} submissions.")

rows = []
for note in submissions:
    replies = note.details.get('replies', [])
    if not replies:
        continue

    review_times = []
    decision_time = None
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if cdate is None:
            continue
        inv_str = ' '.join(invs)
        if '/-/Review' in inv_str and '/-/Review_Release' not in inv_str:
            review_times.append(cdate)
        elif '/-/Decision' in inv_str and '/-/Decision_Release' not in inv_str:
            # A reply can have both Decision and Decision_Release; still count it
            # But let's be precise: check if any invitation ends with /-/Decision
            if any(i.endswith('/-/Decision') for i in invs):
                if decision_time is None or cdate < decision_time:
                    decision_time = cdate

    # Actually reviews also have both /-/Review and /-/Review_Release in invitations list
    # Let me just check for any invitation ending with /-/Review
    review_times = []
    decision_time = None
    for r in replies:
        invs = r.get('invitations', [])
        cdate = r.get('cdate')
        if cdate is None:
            continue
        if any(i.endswith('/-/Review') for i in invs):
            review_times.append(cdate)
        if any(i.endswith('/-/Decision') for i in invs):
            if decision_time is None or cdate < decision_time:
                decision_time = cdate

    review_times.sort()
    t_third_review = review_times[2] if len(review_times) >= 3 else None
    censored = decision_time is None

    gap = None
    if t_third_review and decision_time:
        gap = (decision_time - t_third_review) / MS_PER_DAY

    rows.append({
        'forum': note.forum,
        'n_reviews': len(review_times),
        't_third_review': t_third_review,
        't_decision': decision_time,
        'gap_days': gap,
        'censored': censored,
    })

df = pd.DataFrame(rows)
unc = df[~df['censored'] & df['gap_days'].notna()].copy()
N = len(unc)
gaps = unc['gap_days']

print(f"\n=== TMLR Audit Results ===")
print(f"Total submissions: {len(df)}")
print(f"  With >=3 reviews: {df['t_third_review'].notna().sum()}")
print(f"  With decision:    {(~df['censored']).sum()}")
print(f"N (uncensored, >=3 reviews): {N}")

if N == 0:
    print("ERROR: No valid data found.")
else:
    qs = [0.5, 0.75, 0.9, 0.95, 0.99]
    vals = np.percentile(gaps, [q * 100 for q in qs])
    print(f"\nQuantiles (days from 3rd review to decision):")
    for label, val in zip(['Median', '75th', '90th', '95th', '99th'], vals):
        print(f"  {label:8s}: {val:6.1f}")

    print(f"\nCompliance with stated 'no later than 4 weeks':")
    for threshold, note in [(28, " (violates stated max)"), (35, ""), (42, "")]:
        share = (gaps > threshold).mean() * 100
        print(f"  Share > {threshold} days: {share:5.1f}%{note}")

    neg = (gaps < 0).sum()
    if neg:
        print(f"\nNote: {neg} submissions have decision before 3rd review (desk rejects?)")