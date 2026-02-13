import openreview

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Try different wildcard/regex patterns
patterns = [
    'TMLR/Paper.*/-/Review',
    'TMLR/Paper.*/Review',
    'TMLR/.*/Review',
    'TMLR/-/Review',
]

for p in patterns:
    try:
        notes = client.get_notes(invitation=p, limit=3)
        print(f"  '{p}': got {len(notes)}")
    except Exception as e:
        print(f"  '{p}': error - {str(e)[:100]}")

# Maybe we need to use 'content' or 'signature' based search
# Or maybe we should use get_all_notes with replyInvitation or similar
# Let's check the method signature
print("\n--- Trying invitation prefix approach ---")
try:
    invitations = client.get_all_invitations(prefix='TMLR/Paper1')
    for inv in invitations[:10]:
        print(f"  {inv.id}")
except Exception as e:
    print(f"  Error: {str(e)[:150]}")

# Try with replyForum-based approach using get_notes
print("\n--- Trying direct invitation ID from Paper4 ---")
notes = client.get_notes(invitation='TMLR/Paper4/-/Review', limit=5)
print(f"  Exact 'TMLR/Paper4/-/Review': got {len(notes)}")
for n in notes:
    print(f"    forum={n.forum}, cdate={n.cdate}")

# Try with invitation as a content search
print("\n--- Checking help on get_all_notes ---")
import inspect
sig = inspect.signature(client.get_all_notes)
print(f"  get_all_notes params: {list(sig.parameters.keys())}")
sig2 = inspect.signature(client.get_notes)
print(f"  get_notes params: {list(sig2.parameters.keys())}")