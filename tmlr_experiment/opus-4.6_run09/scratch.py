import openreview
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Test regex patterns for bulk fetching
print("=== Testing regex/wildcard patterns ===")
patterns = [
    'TMLR/Paper.*/Decision',
    'TMLR/Paper.*/.-/Decision', 
    'TMLR/Paper.*/-/Decision',
    'TMLR/Paper[0-9]+/-/Decision',
    'TMLR/.*/Decision',
]
for p in patterns:
    t0 = time.time()
    try:
        notes = client.get_notes(invitation=p, limit=5)
        print(f"  '{p}': {len(notes)} notes ({time.time()-t0:.1f}s)")
    except Exception as e:
        print(f"  '{p}': Error: {str(e)[:80]}")

# Test: how fast is per-forum fetching?
print("\n=== Timing per-forum fetch ===")
subs = client.get_notes(invitation='TMLR/-/Submission', sort='cdate:asc', limit=20)
t0 = time.time()
for sub in subs:
    replies = client.get_all_notes(forum=sub.id)
elapsed = time.time() - t0
print(f"20 forum fetches in {elapsed:.1f}s = {elapsed/20:.2f}s per paper")
print(f"Estimated time for 5900 papers: {5900 * elapsed/20 / 60:.0f} minutes")

# Alternative: what about using select to minimize data transferred?
print("\n=== Testing select parameter ===")
t0 = time.time()
replies = client.get_all_notes(forum=subs[0].id, select='id,invitations,cdate,forum')
print(f"With select: {len(replies)} replies in {time.time()-t0:.2f}s")
for r in replies:
    print(f"  invitations={getattr(r,'invitations',[])}, cdate={r.cdate}")