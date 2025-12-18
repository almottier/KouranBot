import json

# script to generate locality list from power outages data
# Output: districts_localities.json with format {district: [locality1, locality2, ...]}
# needs: wget https://github.com/MrSunshyne/mauritius-dataset-electricity/raw/refs/heads/main/data/power-outages.json

with open('power-outages.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

districts_localities = {}

for district, outages in data.items():
    localities = set()
    
    for outage in outages:
        if 'locality' in outage:
            localities.add(outage['locality'])

    districts_localities[district] = sorted(list(localities))

with open('districts_localities.json', 'w', encoding='utf-8') as f:
    json.dump(districts_localities, f, ensure_ascii=False, indent=2)

print("File created successfully!")
print(f"\nNumber of districts: {len(districts_localities)}")
for district, localities in districts_localities.items():
    print(f"{district}: {len(localities)} localities")
