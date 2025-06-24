import pandas as pd
import io
from typing import List, Tuple
from ..models import Intervention, Intervenant
import logging

logger = logging.getLogger(__name__)

def parse_interventions_csv(file_content: bytes) -> List[Intervention]:
    """Parse le fichier interventions.csv et retourne une liste d'Intervention"""
    try:
        # Lire le CSV depuis les bytes
        df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
        
        # Vérifier les colonnes obligatoires
        required_columns = ['Client', 'Date', 'Durée', 'Adresse']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colonnes manquantes dans interventions.csv: {missing_columns}")
        
        interventions = []
        for _, row in df.iterrows():
            intervention = Intervention(
                client=str(row['Client']).strip(),
                date=str(row['Date']).strip(),
                duree=str(row['Durée']).strip(),
                adresse=str(row['Adresse']).strip(),
                intervenant=str(row.get('Intervenant', '')).strip()
            )
            interventions.append(intervention)
        
        logger.info(f"Parsed {len(interventions)} interventions")
        return interventions
        
    except Exception as e:
        logger.error(f"Erreur parsing interventions.csv: {str(e)}")
        raise ValueError(f"Erreur lors du parsing des interventions: {str(e)}")

def parse_intervenants_csv(file_content: bytes) -> List[Intervenant]:
    """Parse le fichier intervenants.csv et retourne une liste d'Intervenant"""
    try:
        # Lire le CSV depuis les bytes
        df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
        
        # Vérifier les colonnes obligatoires
        required_columns = ['Nom', 'Adresse', 'Disponibilités', 'Week-end']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colonnes manquantes dans intervenants.csv: {missing_columns}")
        
        intervenants = []
        for _, row in df.iterrows():
            intervenant = Intervenant(
                nom=str(row['Nom']).strip(),
                adresse=str(row['Adresse']).strip(),
                disponibilites=str(row['Disponibilités']).strip(),
                repos=str(row.get('Repos', '')).strip(),
                weekend=str(row['Week-end']).strip()
            )
            intervenants.append(intervenant)
        
        logger.info(f"Parsed {len(intervenants)} intervenants")
        return intervenants
        
    except Exception as e:
        logger.error(f"Erreur parsing intervenants.csv: {str(e)}")
        raise ValueError(f"Erreur lors du parsing des intervenants: {str(e)}")

def validate_csv_data(interventions: List[Intervention], intervenants: List[Intervenant]) -> Tuple[bool, str]:
    """Valide la cohérence des données CSV"""
    try:
        # Vérifier qu'il y a des données
        if not interventions:
            return False, "Aucune intervention trouvée"
        
        if not intervenants:
            return False, "Aucun intervenant trouvé"
        
        # Vérifier la cohérence des intervenants imposés
        intervenant_names = {i.nom for i in intervenants}
        for intervention in interventions:
            if intervention.intervenant and intervention.intervenant not in intervenant_names:
                logger.warning(f"Intervenant '{intervention.intervenant}' non trouvé dans la liste des intervenants")
        
        # Vérifier les formats de date
        for intervention in interventions:
            try:
                # Vérifier le format de date "29/06/2025 08:00"
                if not intervention.date or len(intervention.date.split()) != 2:
                    return False, f"Format de date invalide pour {intervention.client}: {intervention.date}"
            except:
                return False, f"Erreur dans la date pour {intervention.client}"
        
        logger.info("Validation CSV réussie")
        return True, "Données CSV valides"
        
    except Exception as e:
        logger.error(f"Erreur validation CSV: {str(e)}")
        return False, f"Erreur de validation: {str(e)}"