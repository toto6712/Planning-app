#!/usr/bin/env python3
import sys
import os
sys.path.append('/app/backend')

from utils.csv_parser import parse_interventions_csv, parse_intervenants_csv

# Test avec le fichier d'exemple
def test_parse():
    try:
        print("=== Test parsing interventions ===")
        with open('/app/interventions_coordonnees.csv', 'rb') as f:
            content = f.read()
            print(f"Contenu du fichier (100 premiers chars): {content[:100]}")
            
        interventions = parse_interventions_csv(content)
        print(f"✅ Parsing réussi: {len(interventions)} interventions")
        
        for i, intervention in enumerate(interventions):
            print(f"  {i+1}. {intervention.client} - ({intervention.latitude}, {intervention.longitude})")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        
    try:
        print("\n=== Test parsing intervenants ===")
        with open('/app/intervenants_coordonnees.csv', 'rb') as f:
            content = f.read()
            print(f"Contenu du fichier (100 premiers chars): {content[:100]}")
            
        intervenants = parse_intervenants_csv(content)
        print(f"✅ Parsing réussi: {len(intervenants)} intervenants")
        
        for i, intervenant in enumerate(intervenants):
            print(f"  {i+1}. {intervenant.nom_prenom} - ({intervenant.latitude}, {intervenant.longitude})")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    test_parse()