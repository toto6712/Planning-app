import pandas as pd
import io

# Test CSV content
csv_content = """Nom,Adresse,Jours_travail,Horaires,Repos,Week-end
Dupont,12 avenue des Vosges Strasbourg,Lundi Mardi Mercredi Jeudi Vendredi,07h00-14h00,2025-07-01,A
Martin,8 rue du Commerce Strasbourg,Lundi Mardi Mercredi Jeudi Vendredi Samedi,14h00-22h00,,B"""

# Read the CSV
df = pd.read_csv(io.StringIO(csv_content))

# Print the DataFrame
print("DataFrame:")
print(df)
print("\nColumns:", df.columns.tolist())

# Try to access the columns
for index, row in df.iterrows():
    print(f"\nRow {index}:")
    print(f"Nom: {row['Nom']}")
    print(f"Adresse: {row['Adresse']}")
    print(f"Jours_travail: {row['Jours_travail']}")
    print(f"Horaires: {row['Horaires']}")
    print(f"Repos: {row['Repos']}")
    print(f"Week-end: {row['Week-end']}")