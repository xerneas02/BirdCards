import csv

csv_filename = "europe_bird_list_updated.csv"

matching_rows = []

with open(csv_filename, mode='r', encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        french_name = row.get("French Name", "").strip()
        latin_name = row.get("Latin Name", "").strip()
        # Vérifier que les deux champs existent et que le nom latin est dans le nom français (insensible à la casse)
        if latin_name and french_name and latin_name.lower() in french_name.lower():
            matching_rows.append(row)

print("Oiseaux dont le nom français contient le nom latin :")
for row in matching_rows:
    print(row.get("French Name", ""), "-", row.get("Latin Name", ""))