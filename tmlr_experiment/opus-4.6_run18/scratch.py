import openreview
import time

# Try V1 API with details='replies'
client_v1 = openreview.Client(baseurl='https://api.openreview.net')

print("Fetching 5 TMLR submissions via V1 with details='replies'...")
subs = client_v1.get_notes(invitation='TMLR/-/Submission', details='replies', limit=5, sort='cdate:asc')
print(f"Got {len(subs)} submissions")

for s in subs[:3]:
    print(f"\n--- Paper number={getattr(s,'number','?')}, forum={s.forum} ---")
    det = s.details
    if det and 'replies' in det:
        reps = det['replies']
        print(f"  {len(reps)} replies")
        for r in reps[:5]:
            print(f"    invitation={r.get('invitation','?')}, cdate={r.get('cdate','?')}")
    else:
        print(f"  details keys: {list(det.keys()) if det else 'None'}")