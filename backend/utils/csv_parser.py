import pandas as pd
import io
import re
from typing import List, Tuple
from ..models import Intervention, Intervenant
import logging
import chardet
from .csv_cleaner import clean_csv_file

logger = logging.getLogger(__name__)

def extract_city_from_address(address: str) -> str:
    """Extrait la ville depuis une adresse pour définir le secteur"""
    try:
        # Nettoyer l'adresse
        address = address.strip()
        
        # Patterns courants pour extraire la ville
        # Ex: "12 rue des Vosges 67000 Strasbourg" -> "Strasbourg"
        # Ex: "8 avenue de la Paix, Strasbourg" -> "Strasbourg"
        
        # Essayer de détecter via code postal + ville
        postal_city_pattern = r'\b\d{5}\s+([A-ZÀ-ÿ][a-zà-ÿ\-\s]+)$'
        match = re.search(postal_city_pattern, address, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
        
        # Essayer de détecter ville après virgule
        comma_pattern = r',\s*([A-ZÀ-ÿ][a-zà-ÿ\-\s]+)$'
        match = re.search(comma_pattern, address, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
        
        # Dernière tentative : prendre les derniers mots
        words = address.split()
        if len(words) >= 2:
            # Prendre les 2 derniers mots si le dernier est une ville
            last_words = ' '.join(words[-2:])
            if not re.search(r'\d', last_words):  # Pas de chiffres
                return last_words.title()
            elif len(words) >= 1:
                # Sinon prendre juste le dernier mot
                last_word = words[-1]
                if not re.search(r'\d', last_word):
                    return last_word.title()
        
        # Par défaut, retourner une partie de l'adresse
        return "Secteur Inconnu"
        
    except Exception as e:
        logger.warning(f"Erreur extraction ville de '{address}': {str(e)}")
        return "Secteur Inconnu"

def detect_special_intervenants(nom_prenom: str) -> Tuple[List[str], str]:
    """Détecte les intervenants spéciaux et leurs contraintes"""
    specialites = []
    plage_horaire = ""
    
    nom_lower = nom_prenom.lower()
    
    # Détecter les cas spéciaux mentionnés dans le prompt
    if "castano" in nom_lower and "leslie" in nom_lower:
        specialites.append("14h-22h_only")
        plage_horaire = "14h00-22h00"
    elif "benamrouze" in nom_lower and "larbi" in nom_lower:
        specialites.append("volant")
    
    return specialites, plage_horaire

def calculate_weekend_roulement(heure_hebdomaire: str) -> str:
    """Calcule le roulement week-end selon les heures hebdomadaires"""
    try:
        # Extraire le nombre d'heures
        heures = int(re.findall(r'\d+', heure_hebdomaire)[0])
        
        if heures >= 35:
            # Les temps pleins sont en roulement A/B (à attribuer automatiquement)
            return "A"  # Par défaut, l'IA décidera du roulement
        else:
            return "exempt"
    except:
        return "exempt"

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
        
        # Vérifier les colonnes obligatoires (avec latitude/longitude)
        required_columns = ['Client', 'Date', 'Duree', 'Latitude', 'Longitude']
        available_columns = df.columns.tolist()
        
        # Mapping flexible des colonnes
        column_mapping = {}
        for req_col in required_columns:
            found = False
            for avail_col in available_columns:
                # Comparaison flexible (sans accents et casse)
                req_normalized = req_col.lower().replace('é', 'e').replace('è', 'e').replace('à', 'a').replace('ç', 'c')
                avail_normalized = avail_col.lower().replace('é', 'e').replace('è', 'e').replace('à', 'a').replace('ç', 'c').replace('ã©', 'e').replace('ã¨', 'e')
                
                if req_normalized == avail_normalized:
                    column_mapping[req_col] = avail_col
                    found = True
                    logger.info(f"Mapping flexible: {req_col} -> {avail_col}")
                    break
                    
            if not found:
                # Recherche partielle pour certains termes spéciaux
                for avail_col in available_columns:
                    avail_lower = avail_col.lower().replace('é', 'e').replace('ã©', 'e')
                    req_lower = req_col.lower().replace('é', 'e')
                    
                    if (req_lower == 'duree' and ('duree' in avail_lower or 'duree' in avail_lower or 'duration' in avail_lower)) or \
                       (req_lower in avail_lower):
                        column_mapping[req_col] = avail_col
                        found = True
                        logger.info(f"Mapping partiel: {req_col} -> {avail_col}")
                        break
            if not found:
                raise ValueError(f"Colonne manquante dans interventions.csv: '{req_col}'. Colonnes disponibles: {available_columns}")
        
        # Rechercher la colonne Intervenant
        intervenant_col = None
        for col in available_columns:
            if 'intervenant' in col.lower():
                intervenant_col = col
                break
        
        logger.info(f"Colonnes mappées: {column_mapping}")
        if intervenant_col:
            logger.info(f"Colonne intervenant trouvée: {intervenant_col}")
        
        logger.info(f"📊 PARSING INTERVENTIONS - {len(df)} lignes détectées")
        
        interventions = []
        for index, row in df.iterrows():
            try:
                if (index + 1) % 5 == 0:  # Log tous les 5 lignes
                    logger.info(f"   🔄 Traitement ligne {index + 1}/{len(df)}")
                
                logger.debug(f"Traitement ligne {index + 2}: {dict(row)}")
                
                # Vérifier que les colonnes critiques ne sont pas vides
                client = str(row[column_mapping['Client']]).strip()
                date = str(row[column_mapping['Date']]).strip()
                duree = str(row[column_mapping['Duree']]).strip()
                latitude = row[column_mapping['Latitude']]
                longitude = row[column_mapping['Longitude']]
                
                logger.debug(f"Ligne {index + 2}: Valeurs extraites - client='{client}', date='{date}', duree='{duree}', lat='{latitude}', lon='{longitude}'")
                
                # Ignorer les lignes avec des valeurs manquantes critiques
                if (pd.isna(row[column_mapping['Client']]) or 
                    pd.isna(row[column_mapping['Date']]) or 
                    pd.isna(row[column_mapping['Duree']]) or
                    pd.isna(row[column_mapping['Latitude']]) or
                    pd.isna(row[column_mapping['Longitude']]) or
                    client.lower() in ['nan', ''] or 
                    date.lower() in ['nan', ''] or
                    duree.lower() in ['nan', '']):
                    logger.warning(f"   ⚠️ Ligne {index + 2} ignorée : données manquantes critiques")
                    continue
                
                # Valider les coordonnées
                try:
                    # Gérer les virgules françaises comme séparateurs décimaux
                    lat_str = str(latitude).replace(',', '.')
                    lon_str = str(longitude).replace(',', '.')
                    
                    lat = float(lat_str)
                    lon = float(lon_str)
                    
                    logger.debug(f"   ✅ Ligne {index + 2}: Coordonnées validées - lat={lat}, lon={lon}")
                    
                    # Vérifier que les coordonnées sont valides
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        logger.warning(f"   ❌ Ligne {index + 2} ignorée : coordonnées invalides ({lat}, {lon})")
                        continue
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"   ❌ Ligne {index + 2} ignorée : coordonnées non numériques - latitude='{latitude}', longitude='{longitude}', error={str(e)}")
                    continue
                
                # Récupérer l'intervenant (peut être vide)
                intervenant = ""
                if intervenant_col and pd.notna(row.get(intervenant_col)):
                    intervenant = str(row[intervenant_col]).strip()
                    if intervenant.lower() == 'nan':
                        intervenant = ""
                
                # Déterminer le secteur (optionnel, peut être dérivé des coordonnées si nécessaire)
                secteur = ""  # Peut être ajouté plus tard via géocodage inverse si nécessaire
                
                # Détecter si c'est une intervention binôme (colonne optionnelle)
                binome = False
                if 'Binome' in df.columns or 'Binôme' in df.columns:
                    binome_col = 'Binome' if 'Binome' in df.columns else 'Binôme'
                    if pd.notna(row.get(binome_col)):
                        binome_val = str(row[binome_col]).strip().lower()
                        binome = binome_val in ['true', '1', 'oui', 'yes']
                
                # Détecter l'intervenant référent (colonne optionnelle)
                intervenant_referent = ""
                if 'Intervenant_referent' in df.columns or 'Référent' in df.columns:
                    ref_col = 'Intervenant_referent' if 'Intervenant_referent' in df.columns else 'Référent'
                    if pd.notna(row.get(ref_col)):
                        intervenant_referent = str(row[ref_col]).strip()
                        if intervenant_referent.lower() == 'nan':
                            intervenant_referent = ""

                intervention = Intervention(
                    client=client,
                    date=date,
                    duree=duree,
                    latitude=lat,
                    longitude=lon,
                    intervenant=intervenant,
                    binome=binome,
                    intervenant_referent=intervenant_referent,
                    secteur=secteur
                )
                interventions.append(intervention)
                
                logger.debug(f"Intervention créée: {intervention.client} le {intervention.date} à ({lat:.4f},{lon:.4f})")
                
            except Exception as e:
                logger.warning(f"Erreur ligne {index + 2}: {str(e)} - Ligne ignorée")
                continue
        
        if not interventions:
            raise ValueError("Aucune intervention valide trouvée dans le fichier")
        
        logger.info(f"✅ PARSING INTERVENTIONS TERMINÉ")
        logger.info(f"   • Lignes traitées: {len(df)}")
        logger.info(f"   • Interventions valides: {len(interventions)}")
        logger.info(f"   • Taux de succès: {len(interventions)/len(df)*100:.1f}%")
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
        
        # Vérifier les colonnes obligatoires (avec latitude/longitude)
        required_columns = ['Nom_Prenom', 'Latitude', 'Longitude', 'Heure_Mensuel', 'Heure_hebdomadaire']
        available_columns = df.columns.tolist()
        
        logger.info(f"Colonnes requises: {required_columns}")
        logger.info(f"Colonnes disponibles: {available_columns}")
        
        # Mapping flexible des colonnes (insensible à la casse)
        column_mapping = {}
        for req_col in required_columns:
            found = False
            for avail_col in available_columns:
                # Comparaison directe d'abord
                if req_col == avail_col:
                    column_mapping[req_col] = avail_col
                    found = True
                    logger.info(f"Mapping direct: {req_col} -> {avail_col}")
                    break
                # Comparaison insensible à la casse
                elif req_col.lower() == avail_col.lower():
                    column_mapping[req_col] = avail_col
                    found = True
                    logger.info(f"Mapping insensible à la casse: {req_col} -> {avail_col}")
                    break
                # Comparaison flexible (sans espaces, underscores, accents)
                req_normalized = req_col.lower().replace('é', 'e').replace('è', 'e').replace('_', '').replace(' ', '')
                avail_normalized = avail_col.lower().replace('é', 'e').replace('è', 'e').replace('_', '').replace(' ', '')
                if req_normalized == avail_normalized:
                    column_mapping[req_col] = avail_col
                    found = True
                    logger.info(f"Mapping flexible: {req_col} -> {avail_col}")
                    break
            if not found:
                # Recherche partielle pour compatibilité
                for avail_col in available_columns:
                    avail_lower = avail_col.lower().replace('é', 'e').replace(' ', '').replace('_', '')
                    req_lower = req_col.lower().replace('é', 'e').replace('_', '').replace(' ', '')
                    
                    # Mapping spécial pour compatibilité
                    if 'nom' in req_lower and ('nom' in avail_lower or 'prenom' in avail_lower):
                        column_mapping[req_col] = avail_col
                        found = True
                        logger.info(f"Mapping nom: {req_col} -> {avail_col}")
                        break
                    elif 'latitude' in req_lower and 'latitude' in avail_lower:
                        column_mapping[req_col] = avail_col
                        found = True
                        logger.info(f"Mapping latitude: {req_col} -> {avail_col}")
                        break
                    elif 'longitude' in req_lower and 'longitude' in avail_lower:
                        column_mapping[req_col] = avail_col
                        found = True
                        logger.info(f"Mapping longitude: {req_col} -> {avail_col}")
                        break
                    elif 'heure' in req_lower and 'heure' in avail_lower:
                        if ('mensuel' in req_lower and 'mensuel' in avail_lower) or ('hebdomaire' in req_lower and 'hebdomaire' in avail_lower):
                            column_mapping[req_col] = avail_col
                            found = True
                            logger.info(f"Mapping heure: {req_col} -> {avail_col}")
                            break
                    elif req_lower in avail_lower:
                        column_mapping[req_col] = avail_col
                        found = True
                        logger.info(f"Mapping partiel: {req_col} -> {avail_col}")
                        break
            if not found:
                logger.error(f"Colonne '{req_col}' non trouvée parmi {available_columns}")
                raise ValueError(f"Colonne manquante dans intervenants.csv: '{req_col}'. Colonnes disponibles: {available_columns}")
        
        logger.info(f"Colonnes mappées: {column_mapping}")
        
        logger.info(f"📊 PARSING INTERVENANTS - {len(df)} lignes détectées")
        
        intervenants = []
        noms_vus = set()  # Pour détecter les doublons
        
        for index, row in df.iterrows():
            try:
                if (index + 1) % 3 == 0:  # Log tous les 3 lignes
                    logger.info(f"   🔄 Traitement ligne {index + 1}/{len(df)}")
                    
                # Vérifier que les colonnes critiques ne sont pas vides
                nom = str(row[column_mapping['Nom_Prenom']]).strip()
                latitude = row[column_mapping['Latitude']]
                longitude = row[column_mapping['Longitude']]
                temps_mensuel = str(row[column_mapping['Heure_Mensuel']]).strip()
                temps_hebdo = str(row[column_mapping['Heure_hebdomadaire']]).strip()
                
                # Ignorer les lignes avec des valeurs manquantes critiques
                if (pd.isna(row[column_mapping['Nom_Prenom']]) or 
                    pd.isna(row[column_mapping['Latitude']]) or
                    pd.isna(row[column_mapping['Longitude']]) or 
                    pd.isna(row[column_mapping['Heure_Mensuel']]) or
                    pd.isna(row[column_mapping['Heure_hebdomadaire']]) or
                    nom.lower() in ['nan', ''] or 
                    temps_mensuel.lower() in ['nan', ''] or
                    temps_hebdo.lower() in ['nan', '']):
                    logger.warning(f"   ⚠️ Ligne {index + 2} ignorée : données manquantes critiques")
                    continue
                
                # Valider les coordonnées
                try:
                    # Gérer les virgules françaises comme séparateurs décimaux
                    lat_str = str(latitude).replace(',', '.')
                    lon_str = str(longitude).replace(',', '.')
                    
                    lat = float(lat_str)
                    lon = float(lon_str)
                    
                    logger.debug(f"   ✅ Ligne {index + 2}: Coordonnées validées - lat={lat}, lon={lon}")
                    
                    # Vérifier que les coordonnées sont valides
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        logger.warning(f"   ❌ Ligne {index + 2} ignorée : coordonnées invalides ({lat}, {lon})")
                        continue
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"   ❌ Ligne {index + 2} ignorée : coordonnées non numériques - latitude='{latitude}', longitude='{longitude}', error={str(e)}")
                    continue
                
                # Vérifier les doublons par nom (insensible à la casse)
                nom_lower = nom.lower()
                if nom_lower in noms_vus:
                    logger.warning(f"   🔄 Ligne {index + 2} ignorée : intervenant '{nom}' déjà présent (doublon détecté)")
                    continue
                
                # Détecter les spécialités et plages horaires spéciales
                specialites, plage_horaire_autorisee = detect_special_intervenants(nom)
                
                # Calculer le roulement week-end selon les heures
                roulement_weekend = calculate_weekend_roulement(temps_hebdo)
                
                intervenant = Intervenant(
                    nom_prenom=nom,
                    latitude=lat,
                    longitude=lon,
                    heure_hebdomaire=temps_hebdo,
                    heure_mensuel=temps_mensuel,
                    plage_horaire_autorisee=plage_horaire_autorisee,
                    specialites=specialites,
                    roulement_weekend=roulement_weekend
                )
                intervenants.append(intervenant)
                noms_vus.add(nom_lower)
                
                logger.debug(f"Intervenant créé: {intervenant.nom_prenom} à ({lat:.4f},{lon:.4f})")
                
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
        noms_intervenants = [i.nom_prenom for i in intervenants]
        noms_uniques = set(noms_intervenants)
        if len(noms_intervenants) != len(noms_uniques):
            doublons = [nom for nom in noms_uniques if noms_intervenants.count(nom) > 1]
            logger.warning(f"Doublons détectés dans les intervenants : {doublons}")
            return False, f"Doublons détectés dans les intervenants : {', '.join(doublons)}"
        
        # Vérifier la cohérence des intervenants imposés
        intervenant_names = {i.nom_prenom for i in intervenants}
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