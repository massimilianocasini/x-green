import requests
import time

USER = 
PASSWORD = 
BASE_URL = "https://eu5.fusionsolar.huawei.com/thirdData"

HEALTH = {1: "🔴 disconnesso", 2: "🟠 guasto", 3: "🟢 sano"}
SEV    = {1: "🔴 CRITICO", 2: "🟠 MAGGIORE", 3: "🟡 MINORE", 4: "⚪ WARNING"}

def login():
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/login", json={"userName": USER, "systemCode": PASSWORD})
    token = resp.headers.get("xsrf-token")
    session.headers.update({"xsrf-token": token})
    return session

def get_all_stations(session):
    all_stations = []
    page = 1
    while True:
        resp = session.post(f"{BASE_URL}/stations", json={"pageNo": page})
        data = resp.json()
        if not data['success']:
            print(f"Errore stations: {data['failCode']} - {data.get('message')}")
            break
        page_data = data['data']
        all_stations.extend(page_data['list'])
        if page >= page_data['pageCount']:
            break
        page += 1
        time.sleep(1)
    return all_stations

try:
    session = login()                                           # chiamata 1

    # --- Lista impianti ---
    stations = get_all_stations(session)                       # chiamata 2
    print(f"Trovati {len(stations)} impianti\n")
    plant_codes = ",".join(s['plantCode'] for s in stations)
    name_map = {s['plantCode']: s['plantName'] for s in stations}

    # --- Real-time KPI (tutti gli impianti in una chiamata) ---
    resp = session.post(                                       # chiamata 3
        f"{BASE_URL}/getStationRealKpi",
        json={"stationCodes": plant_codes}
    )
    kpi_data = resp.json()

    # --- Allarmi attivi (ultimi 30 giorni) ---
    now_ms   = int(time.time() * 1000)
    begin_ms = now_ms - (30 * 24 * 60 * 60 * 1000)
    resp = session.post(                                       # chiamata 4
        f"{BASE_URL}/getAlarmList",
        json={
            "stationCodes": plant_codes,
            "beginTime": begin_ms,
            "endTime": now_ms,
            "language": "it_IT",
            "levels": "1,2,3,4"
        }
    )
    alarm_data = resp.json()

finally:
    session.post(f"{BASE_URL}/logout", json={})                # chiamata 5

# ── Stampa Real-time KPI ──────────────────────────────────────────────────────
print("=" * 85)
print("STATO IMPIANTI")
print("=" * 85)

if not kpi_data['success']:
    print(f"Errore getStationRealKpi: {kpi_data['failCode']}")
else:
    results = []
    for item in kpi_data['data']:
        code = item['stationCode']
        kpi  = item['dataItemMap']
        results.append({'nome': name_map.get(code, code), 'codice': code, **kpi})

    # Problemi prima, poi per nome
    results.sort(key=lambda x: (x['real_health_state'], x['nome']))

    print(f"{'Impianto':<30} {'Stato':<22} {'Oggi':>8} {'Mese':>8} {'Totale':>10}")
    print("-" * 85)
    for r in results:
        stato = HEALTH.get(r['real_health_state'], str(r['real_health_state']))
        print(f"{r['nome']:<30} {stato:<22} "
              f"{r['day_power']:>7.2f}  "
              f"{r['month_power']:>7.2f}  "
              f"{r['total_power']:>10.2f}")
    print("-" * 85)

    sani        = sum(1 for r in results if r['real_health_state'] == 3)
    guasti      = sum(1 for r in results if r['real_health_state'] == 2)
    disconnessi = sum(1 for r in results if r['real_health_state'] == 1)
    print(f"\nStato: 🟢 {sani} sani | 🟠 {guasti} guasti | 🔴 {disconnessi} disconnessi")
    print(f"Produzione oggi:   {sum(r['day_power'] for r in results):.2f} kWh")
    print(f"Produzione mese:   {sum(r['month_power'] for r in results):.2f} kWh")
    print(f"Produzione totale: {sum(r['total_power'] for r in results):.2f} kWh")

# ── Stampa Allarmi ────────────────────────────────────────────────────────────
print("\n" + "=" * 85)
print("ALLARMI ATTIVI")
print("=" * 85)

if not alarm_data['success']:
    print(f"Errore getAlarmList: {alarm_data['failCode']}")
elif not alarm_data['data']:
    print("Nessun allarme attivo. ✅")
else:
    alarms = alarm_data['data']
    alarms.sort(key=lambda x: x['lev'])
    print(f"Allarmi trovati: {len(alarms)}\n")
    for a in alarms:
        sev  = SEV.get(a['lev'], str(a['lev']))
        data = time.strftime('%d/%m/%Y %H:%M', time.localtime(a['raiseTime'] / 1000))
        print(f"{sev} [{a['stationName']}] {a['alarmName']}")
        print(f"  Device:  {a['devName']}")
        print(f"  Causa:   {a['alarmCause']}")
        print(f"  Azione:  {a['repairSuggestion']}")
        print(f"  Dal:     {data}")
        print()
