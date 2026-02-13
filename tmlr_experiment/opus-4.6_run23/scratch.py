import openreview
import time

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Test 1: domain parameter for bulk fetch
print("=== Test: domain + content filter ===")
t0 = time.time()
try:
    notes = client.get_notes(domain='TMLR', limit=5)
    print(f"domain='TMLR': {len(notes)} notes, took {time.time()-t0:.1f}s")
    for n in notes[:3]:
        print(f"  invitations={n.invitations[:2]}, cdate={n.cdate}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: parent_invitations - maybe reviews have a parent invitation pattern
print("\n=== Test: parent_invitations ===")
for pi in ['TMLR/-/Review', 'TMLR/-/Official_Review']:
    try:
        notes = client.get_notes(parent_invitations=pi, limit=5)
        print(f"parent_invitations='{pi}': {len(notes)}")
    except Exception as e:
        print(f"  Error: {e}")

# Test 3: invitation with regex - the API V2 might support it differently
print("\n=== Test: invitation with regex ===")
for inv in ['TMLR/Paper.*/-/Review', 'TMLR/Paper\\d+/-/Review', '~TMLR/Paper']:
    try:
        notes = client.get_notes(invitation=inv, limit=5)
        print(f"invitation='{inv}': {len(notes)}")
    except Exception as e:
        print(f"  Error: {e}")

# Test 4: What if we use get_all_notes with signature pattern for reviewers?
print("\n=== Test: signature patterns ===")
for sig in ['TMLR/Paper4/Reviewer_.*', 'TMLR/Paper4/AnonReviewer.*']:
    try:
        notes = client.get_notes(signature=sig, limit=5)
        print(f"signature='{sig}': {len(notes)}")
        for n in notes[:2]:
            print(f"  invitations={n.invitations[:2]}")
    except Exception as e:
        print(f"  Error: {e}")

# Test 5: Use select parameter for efficiency
print("\n=== Test: forum-based with select ===")
t0 = time.time()
notes = client.get_notes(forum='sFGmQZ7GQf', select='invitations,cdate,forum,id')
print(f"select query: {len(notes)} notes in {time.time()-t0:.2f}s")
for n in notes[:3]:
    print(f"  invitations={n.invitations}")