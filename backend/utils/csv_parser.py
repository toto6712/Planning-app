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
    
    # Options de lecture CSV pour gérer différents cas
    csv_options = [
        {},  # Options par défaut
        {'sep': ';'},  # Séparateur point-virgule
        {'quotechar': '"', 'quoting': 1},  # Gestion des guillemets
        {'skipinitialspace': True},  # Ignorer les espaces initiaux
        {'on_bad_lines': 'skip'},  # Ignorer les lignes malformées
        {'error_bad_lines': False, 'warn_bad_lines': True},  # Pour anciennes versions pandas
    ]
    
    for encoding in encodings_to_try:
        for options in csv_options:
            try:
                logger.info(f"Tentative de lecture avec l'encodage: {encoding} et options: {options}")
                
                # Essayer avec les options spécifiques
                df = pd.read_csv(io.BytesIO(file_content), encoding=encoding, **options)
                
                # Vérifier que le DataFrame n'est pas vide et a au moins 3 colonnes
                if not df.empty and len(df.columns) >= 3:
                    logger.info(f"Lecture réussie avec l'encodage: {encoding} et options: {options}")
                    return df
                else:
                    logger.warning(f"DataFrame vide ou pas assez de colonnes avec {encoding}")
                    
            except Exception as e:
                logger.warning(f"Échec avec l'encodage {encoding} et options {options}: {str(e)}")
                continue
    
    # Si tous les encodages échouent, essayer de nettoyer le contenu ligne par ligne
    try:
        logger.info("Tentative de nettoyage du contenu ligne par ligne")
        content_str = file_content.decode('utf-8', errors='ignore')
        
        # Nettoyer le contenu ligne par ligne
        lines = content_str.split('\n')
        cleaned_lines = []
        
        # Garder l'en-tête
        if lines:
            cleaned_lines.append(lines[0])
        
        # Nettoyer chaque ligne de données
        for i, line in enumerate(lines[1:], start=2):
            if line.strip():
                # Compter les virgules pour détecter les problèmes
                comma_count = line.count(',')
                
                # Si trop de virgules, essayer de corriger
                if comma_count > 6:  # Plus de colonnes que prévu
                    # Essayer de détecter les virgules dans les adresses et les remplacer
                    corrected_line = fix_csv_line(line)
                    cleaned_lines.append(corrected_line)
                    logger.info(f"Ligne {i} corrigée: {line} -> {corrected_line}")
                else:
                    cleaned_lines.append(line)
        
        # Créer un nouveau contenu CSV nettoyé
        cleaned_content = '\n'.join(cleaned_lines)
        df = pd.read_csv(io.StringIO(cleaned_content))
        
        if not df.empty:
            logger.info("Lecture réussie après nettoyage ligne par ligne")
            return df
            
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {str(e)}")
    
    raise ValueError("Impossible de lire le fichier avec tous les encodages et options testés. Vérifiez le format de votre fichier CSV.")

def fix_csv_line(line: str) -> str:
    """Tente de corriger une ligne CSV malformée"""
    try:
        # Si la ligne contient des guillemets, essayer de les équilibrer
        if '"' in line:
            # Compter les guillemets
            quote_count = line.count('"')
            if quote_count % 2 != 0:
                # Nombre impair de guillemets, ajouter un guillemet à la fin
                line += '"'
        
        # Séparer par virgules
        parts = line.split(',')
        
        # Si on a plus de 6 parties (Client,Date,Durée,Adresse,CodePostal,Intervenant)
        if len(parts) > 6:
            # Les 3 premières parties sont probablement Client, Date, Durée
            client = parts[0]
            date = parts[1] 
            duree = parts[2]
            
            # L'intervenant est probablement la dernière partie (peut être vide)
            intervenant = parts[-1] if parts[-1].strip() else ""
            
            # Le code postal pourrait être avant-dernier s'il existe
            code_postal = ""
            if len(parts) > 4 and parts[-2].strip().isdigit():
                code_postal = parts[-2]
                # L'adresse est tout ce qui est entre durée et code postal
                adresse_parts = parts[3:-2]
            else:
                # L'adresse est tout ce qui est entre durée et intervenant
                adresse_parts = parts[3:-1]
            
            # Reconstituer l'adresse
            adresse = ','.join(adresse_parts).strip()
            
            # Reconstituer la ligne
            if code_postal:
                corrected_line = f"{client},{date},{duree},{adresse},{code_postal},{intervenant}"
            else:
                corrected_line = f"{client},{date},{duree},{adresse},{intervenant}"
            
            return corrected_line
        
        return line
        
    except Exception:
        # Si la correction échoue, retourner la ligne originale
        return line

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
        
        # Rechercher la colonne Intervenant
        intervenant_col = None
        for col in available_columns:
            if 'intervenant' in col.lower():
                intervenant_col = col
                break
        
        # Rechercher la colonne Code Postal
        code_postal_col = None
        for col in available_columns:
            col_lower = col.lower().replace(' ', '').replace('_', '').replace('-', '')
            if any(term in col_lower for term in ['codepostal', 'cp', 'postal', 'zip']):
                code_postal_col = col
                break
        
        logger.info(f"Colonnes mappées: {column_mapping}")
        if intervenant_col:
            logger.info(f"Colonne intervenant trouvée: {intervenant_col}")
        if code_postal_col:
            logger.info(f"Colonne code postal trouvée: {code_postal_col}")
        
        interventions = []
        for index, row in df.iterrows():
            try:
                # Construire l'adresse complète
                adresse_base = str(row[column_mapping['Adresse']]).strip()
                
                # Ajouter le code postal s'il existe
                if code_postal_col and pd.notna(row.get(code_postal_col)):
                    code_postal = str(row[code_postal_col]).strip()
                    if code_postal and code_postal.lower() != 'nan':
                        # Vérifier si le code postal n'est pas déjà dans l'adresse
                        if code_postal not in adresse_base:
                            adresse_complete = f"{adresse_base}, {code_postal}"
                        else:
                            adresse_complete = adresse_base
                    else:
                        adresse_complete = adresse_base
                else:
                    adresse_complete = adresse_base
                
                intervention = Intervention(
                    client=str(row[column_mapping['Client']]).strip(),
                    date=str(row[column_mapping['Date']]).strip(),
                    duree=str(row[column_mapping['Durée']]).strip(),
                    adresse=adresse_complete,
                    intervenant=str(row.get(intervenant_col, '')).strip() if intervenant_col else ''
                )
                interventions.append(intervention)
                
                logger.debug(f"Intervention créée: {intervention.client} à {adresse_complete}")
                
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