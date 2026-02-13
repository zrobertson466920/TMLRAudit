import openreview

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# The pattern 'TMLR/Paper6/.*' worked with get_notes but let's check get_all_notes
print("Test 1: get_notes with regex wildcard")
r1 = client.get_notes(invitation='TMLR/Paper6/.*', limit=5)
print(f"  get_notes TMLR/Paper6/.*: {len(r1)}")

print("\nTest 2: get_all_notes with regex wildcard")
r2 = client.get_all_notes(invitation='TMLR/Paper6/.*')
print(f"  get_all_notes TMLR/Paper6/.*: {len(r2)}")

print("\nTest 3: get_notes with TMLR/Paper.*/-/Review")
r3 = client.get_notes(invitation='TMLR/Paper.*/-/Review', limit=5)
print(f"  get_notes TMLR/Paper.*/-/Review: {len(r3)}")

print("\nTest 4: get_all_notes with broader pattern")
r4 = client.get_all_notes(invitation='TMLR/Paper6/-/Review')
print(f"  get_all_notes TMLR/Paper6/-/Review: {len(r4)}")

# Check if there's a content.venue or similar
print("\nTest 5: get_notes with content search")
r5 = client.get_notes(invitation='TMLR/Paper6/-/Review', limit=5)
print(f"  get_notes TMLR/Paper6/-/Review: {len(r5)}")
for n in r5[:2]:
    print(f"    invitations: {n.invitations}  cdate: {n.cdate}")

# Maybe the API needs invitation (singular)?
# Check method signature
print("\nTest 6: Trying 'invitations' parameter")
try:
    r6 = client.get_notes(invitations=['TMLR/Paper6/-/Review'], limit=5)
    print(f"  invitations param: {len(r6)}")
except Exception as e:
    print(f"  Failed: {e}")