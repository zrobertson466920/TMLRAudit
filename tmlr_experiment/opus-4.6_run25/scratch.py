import openreview
import time

# v1 API supports prefix regex for invitation
client_v1 = openreview.Client(baseurl='https://api.openreview.net')

print("=== Test: v1 prefix regex for reviews ===")
try:
    # Prefix regex: everything starting with "TMLR/Paper"
    notes = client_v1.get_all_notes(invitation='TMLR/Paper.*/Review')
    print(f"  TMLR/Paper.*/Review: {len(notes)}")
    if notes:
        n = notes[0]
        print(f"  Sample: forum={n.forum}, invitation={n.invitation}, cdate={n.cdate}")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Test: v1 prefix regex for decisions ===")
try:
    notes = client_v1.get_all_notes(invitation='TMLR/Paper.*/Decision')
    print(f"  TMLR/Paper.*/Decision: {len(notes)}")
    if notes:
        n = notes[0]
        print(f"  Sample: forum={n.forum}, invitation={n.invitation}, cdate={n.cdate}")
except Exception as e:
    print(f"  Error: {e}")