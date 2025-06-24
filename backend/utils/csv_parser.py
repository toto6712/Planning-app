import pandas as pd
import io
from typing import List, Tuple
from ..models import Intervention, Intervenant
import logging
import chardet

logger = logging.getLogger(__name__)

def detect_encoding(file_content: bytes) -> str:
    """Détecte l'encodage du fichier CSV"""
    try:
        # Essayer de détecter l'encodage automatiquement
        detected = chardet.detect(file_content)
        encoding = detected.get('encoding', 'utf-8')
        logger.info(f"Encodage détecté: {encoding} (confiance: {detected.get('confidence', 0):.2f})")
        return encoding
    except Exception as e:
        logger.warning(f"Impossible de détecter l'encodage: {str(e)}")
        return 'utf-8'

def try_multiple_encodings(file_content: bytes) -> pd.DataFrame:
    """Essaie plusieurs encodages pour lire le fichier CSV"""
    encodings_to_try = [
        'utf-8',
        'utf-8-sig',  # UTF-8 avec BOM
        'iso-8859-1',  # Latin-1
        'cp1252',  # Windows-1252
        'ascii'
    ]
    
    # Ajouter l'encodage détecté en premier
    detected_encoding = detect_encoding(file_content)
    if detected_encoding and detected_encoding not in encodings_to_try:
        encodings_to_try.insert(0, detected_encoding)
    
    for encoding in encodings_to_try:
        try:
            logger.info(f"Tentative de lecture avec l'encodage: {encoding}")
            df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
            logger.info(f"Lecture réussie avec l'encodage: {encoding}")
            return df
        except UnicodeDecodeError as e:
            logger.warning(f"Échec avec l'encodage {encoding}: {str(e)}")
            continue
        except Exception as e:
            logger.warning(f"Erreur avec l'encodage {encoding}: {str(e)}")
            continue
    
    # Si tous les encodages échouent, essayer de nettoyer le contenu
    try:
        logger.info("Tentative de nettoyage du contenu avec erreurs ignorées")
        content_str = file_content.decode('utf-8', errors='ignore')
        df = pd.read_csv(io.StringIO(content_str))
        logger.info("Lecture réussie après nettoyage")
        return df
    except Exception as e:
        raise ValueError(f"Impossible de lire le fichier avec tous les encodages testés. Erreur: {str(e)}")

def parse_interventions_csv(file_content: bytes) -> List[Intervention]:
    """Parse le fichier interventions.csv et retourne une liste d'Intervention"""
    try:
        # Lire le CSV avec détection d'encodage
        df = try_multiple_encodings(file_content)
        
        # Nettoyer les noms de colonnes (enlever les espaces et caractères invisibles)
        df.columns = df.columns.str.strip()
        
        # Vérifier les colonnes obligatoires (flexible sur les accents)
        required_columns = ['Client', 'Date', 'Durée', 'Adresse']
        available_columns = df.columns.tolist()
        
        # Mapping flexible des colonnes
        column_mapping = {}
        for req_col in required_columns:
            found = False
            for avail_col in available_columns:
                # Comparaison flexible (sans accents et casse)
                if (req_col.lower().replace('é', 'e').replace('è', 'e') == 
                    avail_col.lower().replace('é', 'e').replace('è', 'e')):
                    column_mapping[req_col] = avail_col
                    found = True
                    break
            if not found:
                # Recherche partielle
                for avail_col in available_columns:
                    if req_col.lower().replace('é', 'e') in avail_col.lower().replace('é', 'e'):
                        column_mapping[req_col] = avail_col
                        found = True
                        break
            if not found:
                raise ValueError(f"Colonne manquante dans interventions.csv: '{req_col}'. Colonnes disponibles: {available_columns}")
        
        # Ajouter la colonne Intervenant si elle existe
        intervenant_col = None
        for col in available_columns:
            if 'intervenant' in col.lower():
                intervenant_col = col
                break
        
        logger.info(f"Colonnes mappées: {column_mapping}")
        if intervenant_col:
            logger.info(f"Colonne intervenant trouvée: {intervenant_col}")
        
        interventions = []
        for index, row in df.iterrows():
            try:
                intervention = Intervention(
                    client=str(row[column_mapping['Client']]).strip(),
                    date=str(row[column_mapping['Date']]).strip(),
                    duree=str(row[column_mapping['Durée']]).strip(),
                    adresse=str(row[column_mapping['Adresse']]).strip(),
                    intervenant=str(row.get(intervenant_col, '')).strip() if intervenant_col else ''
                )
                interventions.append(intervention)
            except Exception as e:
                logger.warning(f"Erreur ligne {index + 2}: {str(e)}")
                continue
        
        logger.info(f"Parsed {len(interventions)} interventions")
        return interventions
        
    except Exception as e:
        logger.error(f"Erreur parsing interventions.csv: {str(e)}")
        raise ValueError(f"Erreur lors du parsing des interventions: {str(e)}")

def parse_intervenants_csv(file_content: bytes) -> List[Intervenant]:
    """Parse le fichier intervenants.csv et retourne une liste d'Intervenant"""
    try:
        # Lire le CSV avec détection d'encodage
        df = try_multiple_encodings(file_content)
        
        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip()
        
        # Vérifier les colonnes obligatoires (flexible)
        required_columns = ['Nom', 'Adresse', 'Disponibilités', 'Week-end']
        available_columns = df.columns.tolist()
        
        # Mapping flexible des colonnes
        column_mapping = {}
        for req_col in required_columns:
            found = False
            for avail_col in available_columns:
                # Comparaison flexible
                if (req_col.lower().replace('é', 'e').replace('è', 'e') == 
                    avail_col.lower().replace('é', 'e').replace('è', 'e')):
                    column_mapping[req_col] = avail_col
                    found = True
                    break
            if not found:
                # Recherche partielle
                for avail_col in available_columns:
                    if req_col.lower().replace('é', 'e') in avail_col.lower().replace('é', 'e'):
                        column_mapping[req_col] = avail_col
                        found = True
                        break
            if not found:
                raise ValueError(f"Colonne manquante dans intervenants.csv: '{req_col}'. Colonnes disponibles: {available_columns}")
        
        # Ajouter la colonne Repos si elle existe
        repos_col = None
        for col in available_columns:
            if 'repos' in col.lower():
                repos_col = col
                break
        
        logger.info(f"Colonnes mappées: {column_mapping}")
        if repos_col:
            logger.info(f"Colonne repos trouvée: {repos_col}")
        
        intervenants = []
        for index, row in df.iterrows():
            try:
                intervenant = Intervenant(
                    nom=str(row[column_mapping['Nom']]).strip(),
                    adresse=str(row[column_mapping['Adresse']]).strip(),
                    disponibilites=str(row[column_mapping['Disponibilités']]).strip(),
                    repos=str(row.get(repos_col, '')).strip() if repos_col else '',
                    weekend=str(row[column_mapping['Week-end']]).strip()
                )
                intervenants.append(intervenant)
            except Exception as e:
                logger.warning(f"Erreur ligne {index + 2}: {str(e)}")
                continue
        
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