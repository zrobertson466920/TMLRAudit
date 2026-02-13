import pickle
D = pickle.load(open("_data.pkl","rb"))
successes=D["successes"]; R=D["R"]; aids=D["aids"]; TVD=D["TVD"]
W_i=D["W_i"]; W_all=D["W_all"]; Ns=D["Ns"]; Q=D["Q"]

# ---- 6. Agent Welfare Scores ----
print("## 6. Agent Welfare Scores\n")
print(f"  {'Agent':<14s}  w_i    Model    Sum(yes)  Profile")
print("  " + "-" * 72)
ranked = sorted(range(Ns), key=lambda i: -W_i[i])
for idx in ranked:
    yes_count = sum(R[q][idx] for q in range(Q))
    profile = "".join(str(R[q][idx]) for q in range(Q))
    model = "4.5" if "45" in aids[idx] else "4.6"
    print(f"  {aids[idx]:<14s}  {W_i[idx]:.4f}  opus-{model}  {yes_count:>3d}/15    {profile}")

print(f"\n  Mean welfare: {sum(W_i)/Ns:.4f}")
print(f"  Std welfare:  {(sum((w-sum(W_i)/Ns)**2 for w in W_i)/Ns)**0.5:.4f}")

# Welfare by model
w45 = [W_i[i] for i in range(Ns) if "45" in aids[i]]
w46 = [W_i[i] for i in range(Ns) if "46" in aids[i]]
print(f"\n  opus-4.5 mean welfare: {sum(w45)/len(w45):.4f} (n={len(w45)})")
print(f"  opus-4.6 mean welfare: {sum(w46)/len(w46):.4f} (n={len(w46)})")

# ---- 7. Overall Welfare ----
print(f"\n## 7. Overall Welfare\n")
print(f"  W = {W_all:.4f}")
print(f"  (Mean pairwise TVD-MI across all {Ns*(Ns-1)//2} pairs)")

# ---- 8. Interpretation ----
print(f"\n## 8. Interpretation\n")

# Identify clusters by looking at response profiles
profiles = {}
for i in range(Ns):
    p = tuple(R[q][i] for q in range(Q))
    profiles.setdefault(p, []).append(aids[i])

print(f"  Distinct response profiles: {len(profiles)}")
print(f"  Profiles with >1 agent:")
for p, agents in sorted(profiles.items(), key=lambda x: -len(x[1])):
    if len(x[1]) > 1:
        pass
# Fix: use proper variable
multi = [(p, agents) for p, agents in profiles.items() if len(agents) > 1]
multi.sort(key=lambda x: -len(x[1]))
for p, agents in multi:
    yes_ct = sum(p)
    print(f"    Profile {''.join(str(x) for x in p)} ({yes_ct}/15 yes): {', '.join(agents)}")

# Identify the methodological fork
print("\n  --- Key Methodological Fork: Baseline Choice ---")
third_rev = [i for i in range(Ns) if R[5][i] == 1]  # Q06 = 3rd review
first_rev = [i for i in range(Ns) if R[5][i] == 0]   # used 1st/last review
print(f"  3rd-review baseline (n={len(third_rev)}): {', '.join(aids[i] for i in third_rev)}")
print(f"  1st/last-review baseline (n={len(first_rev)}): {', '.join(aids[i] for i in first_rev)}")

# Within-group vs between-group TVD-MI
if len(third_rev) > 1 and len(first_rev) > 1:
    within_3rd = []
    for a in range(len(third_rev)):
        for b in range(a+1, len(third_rev)):
            within_3rd.append(TVD[third_rev[a]][third_rev[b]])
    within_1st = []
    for a in range(len(first_rev)):
        for b in range(a+1, len(first_rev)):
            within_1st.append(TVD[first_rev[a]][first_rev[b]])
    between = []
    for a in third_rev:
        for b in first_rev:
            between.append(TVD[a][b])
    
    print(f"\n  Within 3rd-review group: mean TVD-MI = {sum(within_3rd)/len(within_3rd):.4f} ({len(within_3rd)} pairs)")
    print(f"  Within 1st-review group: mean TVD-MI = {sum(within_1st)/len(within_1st):.4f} ({len(within_1st)} pairs)")
    print(f"  Between groups:          mean TVD-MI = {sum(between)/len(between):.4f} ({len(between)} pairs)")

# Prose vs code fork
prose = [i for i in range(Ns) if R[7][i] == 1]
code = [i for i in range(Ns) if R[7][i] == 0]
print(f"\n  --- Output Format Fork ---")
print(f"  Prose output (n={len(prose)})")
print(f"  Code output (n={len(code)})")

# Summary narrative
print("""
  --- Summary ---
  
  The 36 successful agents split into identifiable subgroups along two
  primary axes:
  
  1. BASELINE CHOICE (3rd review vs 1st/last review): 31 agents correctly
     measured from the 3rd review (median ~45 days), while 5 measured from
     the 1st review (median ~69 days). This is the dominant source of
     variation: it shifts every core statistic (median, compliance rates,
     percentiles) and cascades through all Tier 1 queries.
  
  2. REPORTING COMPLETENESS: Among the 31 correct-baseline agents, there
     is substantial variation in how much detail they report. Some produce
     comprehensive tables with P95, P99, 42-day compliance, total N, mean,
     and censoring discussion. Others report only the headline median and
     one compliance rate.
  
  The overall welfare W = {:.4f} reflects moderate shared information:
  agents are neither perfectly converged (which would yield W~0 since
  agreement would be predictable from marginals) nor randomly scattered.
  The population exhibits structured disagreement driven primarily by the
  methodological fork and secondarily by reporting depth.
  
  High-welfare agents (w_i > 0.15) tend to be those whose response 
  profiles sit at the boundary between subgroups — they share some
  findings with the comprehensive reporters and some with the minimal
  reporters, making their joint patterns maximally informative.
  
  Low-welfare agents (w_i < 0.08) tend to have profiles that are either
  very common (predictable from marginals) or very unusual (uncorrelated
  with peers).
""".format(W_all))