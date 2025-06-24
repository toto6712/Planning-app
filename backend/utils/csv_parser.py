import pandas as pd
import io
from typing import List, Tuple
from ..models import Intervention, Intervenant
import logging
import chardet
from .csv_cleaner import clean_csv_file

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
    """Essaie plusieurs encodings et options pour lire le fichier CSV"""
    # D'abord, essayer de nettoyer le fichier
    try:
        logger.info("Tentative de nettoyage du fichier CSV")
        cleaned_content = clean_csv_file(file_content)
    except Exception as e:
        logger.warning(f"Échec du nettoyage: {str(e)}")
        cleaned_content = file_content
    
    encodings_to_try = [
        'utf-8',
        'utf-8-sig',  # UTF-8 avec BOM
        'iso-8859-1',  # Latin-1
        'cp1252',  # Windows-1252
        'ascii'
    ]
    
    # Ajouter l'encodage détecté en premier
    detected_encoding = detect_encoding(cleaned_content)
    if detected_encoding and detected_encoding not in encodings_to_try:
        encodings_to_try.insert(0, detected_encoding)
    
    # Options de lecture CSV pour gérer différents cas
    csv_options_list = [
        {},  # Options par défaut
        {'sep': ';'},  # Séparateur point-virgule
        {'quotechar': '"', 'quoting': 1},  # Gestion des guillemets
        {'skipinitialspace': True},  # Ignorer les espaces initiaux
        {'on_bad_lines': 'skip'},  # Ignorer les lignes malformées (pandas récent)
    ]
    
    # Pour les versions plus anciennes de pandas
    try:
        import pandas as pd
        if hasattr(pd, '__version__') and int(pd.__version__.split('.')[0]) < 1:
            csv_options_list.append({'error_bad_lines': False, 'warn_bad_lines': True})
    except:
        pass
    
    for encoding in encodings_to_try:
        for options in csv_options_list:
            try:
                logger.info(f"Tentative avec encodage: {encoding}, options: {options}")
                
                df = pd.read_csv(io.BytesIO(cleaned_content), encoding=encoding, **options)
                
                # Vérifier que le DataFrame est valide
                if not df.empty and len(df.columns) >= 3:
                    logger.info(f"✅ Lecture réussie avec {encoding} et options {options}")
                    return df
                else:
                    logger.warning(f"DataFrame invalide avec {encoding}")
                    
            except Exception as e:
                logger.debug(f"Échec avec {encoding} et {options}: {str(e)}")
                continue
    
    # Dernière tentative avec nettoyage manuel ligne par ligne
    try:
        logger.info("Tentative de nettoyage manuel avancé")
        content_str = cleaned_content.decode('utf-8', errors='ignore')
        
        lines = content_str.split('\n')
        if not lines:
            raise ValueError("Fichier vide")
        
        # Analyser l'en-tête
        header = lines[0].strip()
        if not header:
            raise ValueError("En-tête manquant")
        
        expected_columns = len(header.split(','))
        logger.info(f"En-tête: {header}, colonnes attendues: {expected_columns}")
        
        # Construire un CSV valide
        valid_lines = [header]
        for i, line in enumerate(lines[1:], start=2):
            if line.strip():
                # Essayer de corriger la ligne
                parts = line.split(',')
                if len(parts) != expected_columns:
                    logger.warning(f"Ligne {i}: {len(parts)} champs au lieu de {expected_columns}")
                    # Correction simple: prendre les premières colonnes et fusionner le reste
                    if len(parts) > expected_columns:
                        corrected_parts = parts[:expected_columns-1]
                        corrected_parts.append(','.join(parts[expected_columns-1:]))
                        line = ','.join(corrected_parts)
                
                valid_lines.append(line.strip())
        
        # Créer le DataFrame à partir du contenu corrigé
        corrected_content = '\n'.join(valid_lines)
        df = pd.read_csv(io.StringIO(corrected_content))
        
        if not df.empty:
            logger.info("✅ Lecture réussie après correction manuelle")
            return df
            
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage manuel: {str(e)}")
    
    raise ValueError(
        "❌ Impossible de lire le fichier CSV. Vérifiez que :\n"
        "1. Le fichier est bien au format CSV\n"
        "2. Les colonnes sont séparées par des virgules\n"
        "3. Il n'y a pas de virgules dans les données (utilisez des guillemets si nécessaire)\n"
        "4. Toutes les lignes ont le même nombre de colonnes\n"
        "5. L'encodage est UTF-8"
    )

def parse_interventions_csv(file_content: bytes) -> List[Intervention]:
    """Parse le fichier interventions.csv et retourne une liste d'Intervention"""
    try:
        # Lire le CSV avec détection d'encodage
        df = try_multiple_encodings(file_content)
        
        # Nettoyer les noms de colonnes (enlever les espaces et caractères invisibles)
        df.columns = df.columns.str.strip()
        
        # Supprimer les lignes complètement vides
        df = df.dropna(how='all')
        
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
                # Vérifier que les colonnes critiques ne sont pas vides
                client = str(row[column_mapping['Client']]).strip()
                date = str(row[column_mapping['Date']]).strip()
                duree = str(row[column_mapping['Durée']]).strip()
                adresse_base = str(row[column_mapping['Adresse']]).strip()
                
                # Ignorer les lignes avec des valeurs manquantes critiques
                if (pd.isna(row[column_mapping['Client']]) or 
                    pd.isna(row[column_mapping['Date']]) or 
                    pd.isna(row[column_mapping['Durée']]) or 
                    pd.isna(row[column_mapping['Adresse']]) or
                    client.lower() in ['nan', ''] or 
                    date.lower() in ['nan', ''] or
                    duree.lower() in ['nan', ''] or
                    adresse_base.lower() in ['nan', '']):
                    logger.warning(f"Ligne {index + 2} ignorée : données manquantes critiques")
                    continue
                
                # Construire l'adresse complète
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
                
                # Récupérer l'intervenant (peut être vide)
                intervenant = ""
                if intervenant_col and pd.notna(row.get(intervenant_col)):
                    intervenant = str(row[intervenant_col]).strip()
                    if intervenant.lower() == 'nan':
                        intervenant = ""
                
                intervention = Intervention(
                    client=client,
                    date=date,
                    duree=duree,
                    adresse=adresse_complete,
                    intervenant=intervenant
                )
                interventions.append(intervention)
                
                logger.debug(f"Intervention créée: {intervention.client} le {intervention.date} à {adresse_complete}")
                
            except Exception as e:
                logger.warning(f"Erreur ligne {index + 2}: {str(e)} - Ligne ignorée")
                continue
        
        if not interventions:
            raise ValueError("Aucune intervention valide trouvée dans le fichier")
        
        logger.info(f"Parsed {len(interventions)} interventions valides")
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
        
        # Supprimer les lignes complètement vides
        df = df.dropna(how='all')
        
        # Vérifier les colonnes obligatoires (flexible)
        required_columns = ['Nom', 'Adresse', 'Jours_travail', 'Horaires', 'Week-end']
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
        noms_vus = set()  # Pour détecter les doublons
        
        for index, row in df.iterrows():
            try:
                # Vérifier que les colonnes critiques ne sont pas vides
                nom = str(row[column_mapping['Nom']]).strip()
                adresse = str(row[column_mapping['Adresse']]).strip()
                disponibilites = str(row[column_mapping['Disponibilités']]).strip()
                weekend = str(row[column_mapping['Week-end']]).strip()
                
                # Ignorer les lignes avec des valeurs manquantes critiques
                if (pd.isna(row[column_mapping['Nom']]) or 
                    pd.isna(row[column_mapping['Adresse']]) or 
                    pd.isna(row[column_mapping['Disponibilités']]) or
                    pd.isna(row[column_mapping['Week-end']]) or
                    nom.lower() in ['nan', ''] or 
                    adresse.lower() in ['nan', ''] or
                    disponibilites.lower() in ['nan', ''] or
                    weekend.lower() in ['nan', '']):
                    logger.warning(f"Ligne {index + 2} ignorée : données manquantes critiques")
                    continue
                
                # Vérifier les doublons par nom (insensible à la casse)
                nom_lower = nom.lower()
                if nom_lower in noms_vus:
                    logger.warning(f"Ligne {index + 2} ignorée : intervenant '{nom}' déjà présent (doublon détecté)")
                    continue
                
                # Récupérer les repos (peut être vide)
                repos = ""
                if repos_col and pd.notna(row.get(repos_col)):
                    repos = str(row[repos_col]).strip()
                    if repos.lower() == 'nan':
                        repos = ""
                
                intervenant = Intervenant(
                    nom=nom,
                    adresse=adresse,
                    disponibilites=disponibilites,
                    repos=repos,
                    weekend=weekend
                )
                intervenants.append(intervenant)
                noms_vus.add(nom_lower)
                
                logger.debug(f"Intervenant créé: {intervenant.nom}")
                
            except Exception as e:
                logger.warning(f"Erreur ligne {index + 2}: {str(e)} - Ligne ignorée")
                continue
        
        if not intervenants:
            raise ValueError("Aucun intervenant valide trouvé dans le fichier")
        
        logger.info(f"Parsed {len(intervenants)} intervenants valides")
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
        
        # Vérifier les doublons dans les intervenants
        noms_intervenants = [i.nom for i in intervenants]
        noms_uniques = set(noms_intervenants)
        if len(noms_intervenants) != len(noms_uniques):
            doublons = [nom for nom in noms_uniques if noms_intervenants.count(nom) > 1]
            logger.warning(f"Doublons détectés dans les intervenants : {doublons}")
            return False, f"Doublons détectés dans les intervenants : {', '.join(doublons)}"
        
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