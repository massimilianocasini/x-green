import requests

API_KEY  = 
BASE_URL = "https://monitoringapi.solaredge.com"

def impact_icon(value):
    if value == 0:   return "✅"
    if value <= 2:   return "⚪"  # basso
    if value <= 6:   return "🟡"  # medio
    if value <= 9:   return "🔴"  # alto
    return "❓"

def impact_label(value):
    if value == 0:   return "nessuno"
    if value <= 2:   return "basso"
    if value <= 6:   return "medio"
    if value <= 9:   return "alto"
    return "?"

def get_all_sites():
    all_sites = []
    start = 0
    size  = 100
    while True:
        resp = requests.get(f"{BASE_URL}/sites/list", params={
            "api_key":      API_KEY,
            "size":         size,
            "startIndex":   start,
            "status":       "Active,Pending,Disabled",
            "sortProperty": "name",
            "sortOrder":    "ASC"
        })
        sites_data = resp.json()['sites']
        batch = sites_data['site']
        all_sites.extend(batch)
        total = sites_data['count']
        start += size
        if start >= total:
            break
    return all_sites, total

# --- Recupera siti ---
sites, total = get_all_sites()
print(f"Trovati {total} siti\n")

# --- Stampa tabella ---
print("=" * 95)
print(f"{'ID':<12} {'Nome':<35} {'Stato':<12} {'Alert':>6}  {'Impatto'}")
print("-" * 95)

for s in sites:
    impact = s.get('highestImpact', 0)
    icon   = impact_icon(impact)
    label  = impact_label(impact)
    print(f"{s['id']:<12} "
          f"{s['name']:<35} "
         # f"{s['accountId']:<12} "
          f"{s['status']:<12} "
          f"{s.get('alertQuantity', 0):>6}  "
          f"{icon} {impact} ({label})")

print("=" * 95)

# --- Riepilogo ---
con_alert = [s for s in sites if s.get('alertQuantity', 0) > 0]
alti      = [s for s in sites if s.get('highestImpact', 0) >= 7]
medi      = [s for s in sites if 3 <= s.get('highestImpact', 0) <= 6]
bassi     = [s for s in sites if 1 <= s.get('highestImpact', 0) <= 2]

print(f"\nSiti con alert aperti: {len(con_alert)}/{len(sites)}")
print(f"  🔴 impatto alto  (7-9): {len(alti)}")
print(f"  🟡 impatto medio (3-6): {len(medi)}")
print(f"  ⚪ impatto basso (1-2): {len(bassi)}")

if alti or medi:
    prioritari = sorted(con_alert,
                        key=lambda x: (x.get('highestImpact', 0), x.get('alertQuantity', 0)),
                        reverse=True)
    print("\nSiti da gestire per priorità:")
    print("-" * 65)
    for s in prioritari:
        impact = s.get('highestImpact', 0)
        print(f"  {impact_icon(impact)} [{impact}] {s['name']:<35} | "
              f"{s.get('alertQuantity', 0)} alert | {s['status']}")
