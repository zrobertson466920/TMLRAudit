import openreview

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

# Check if parent_invitations works to fetch all reviews at once
print("--- Testing parent_invitations approach ---")
for pattern in [
    'TMLR/-/Review',
    'TMLR/-/Decision',
]:
    try:
        notes = client.get_notes(parent_invitations=pattern, limit=5)
        print(f"parent_invitations='{pattern}': {len(notes)} notes")
        for n in notes[:2]:
            print(f"  invitations={n.invitations}, cdate={n.cdate}, forum={n.forum}")
    except Exception as e:
        print(f"parent_invitations='{pattern}': ERROR - {str(e)[:200]}")

# Check submission number field
print("\n--- Checking submission number field ---")
subs = client.get_notes(invitation='TMLR/-/Submission', sort='cdate:asc', limit=5)
for s in subs:
    print(f"  id={s.id}, number={getattr(s, 'number', 'N/A')}, cdate={s.cdate}")

# Test: can we fetch all notes with signature matching TMLR?
print("\n--- Testing signature-based fetch ---")
try:
    notes = client.get_notes(signature='TMLR', limit=5)
    print(f"signature='TMLR': {len(notes)} notes")
except Exception as e:
    print(f"signature='TMLR': ERROR - {str(e)[:200]}")

# Test: invitation with tilde for prefix matching
print("\n--- Testing invitation prefix ---")
try:
    notes = client.get_notes(invitation='TMLR/Paper4/-/.*', limit=5)
    print(f"'TMLR/Paper4/-/.*': {len(notes)} notes")
except Exception as e:
    print(f"ERROR: {str(e)[:200]}")