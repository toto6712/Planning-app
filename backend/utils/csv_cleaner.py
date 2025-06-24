import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

def clean_csv_file(file_content: bytes) -> bytes:
    """Nettoie un fichier CSV pour corriger les erreurs de format communes"""
    try:
        # Essayer de décoder avec différents encodages
        content_str = None
        for encoding in ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']:
            try:
                content_str = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content_str is None:
            content_str = file_content.decode('utf-8', errors='ignore')
        
        lines = content_str.split('\n')
        cleaned_lines = []
        
        # Analyser l'en-tête pour déterminer le nombre de colonnes attendu
        if lines:
            header = lines[0].strip()
            expected_columns = len(header.split(','))
            cleaned_lines.append(header)
            logger.info(f"En-tête détecté: {header}")
            logger.info(f"Nombre de colonnes attendu: {expected_columns}")
        
        # Nettoyer chaque ligne
        for line_num, line in enumerate(lines[1:], start=2):
            if line.strip():
                cleaned_line = clean_csv_line(line.strip(), expected_columns, line_num)
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
        
        # Reconstituer le contenu
        cleaned_content = '\n'.join(cleaned_lines)
        return cleaned_content.encode('utf-8')
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du fichier CSV: {str(e)}")
        return file_content

def clean_csv_line(line: str, expected_columns: int, line_num: int) -> str:
    """Nettoie une ligne CSV individuelle"""
    try:
        # Cas 1: Ligne avec guillemets déséquilibrés
        if line.count('"') % 2 != 0:
            logger.warning(f"Ligne {line_num}: Guillemets déséquilibrés")
            line = line.replace('"', '')
        
        # Cas 2: Trop de virgules (probablement dans l'adresse)
        parts = line.split(',')
        
        if len(parts) > expected_columns:
            logger.warning(f"Ligne {line_num}: {len(parts)} champs trouvés, {expected_columns} attendus")
            
            # Stratégie de correction basée sur le format attendu
            if expected_columns == 6:  # Client,Date,Durée,Adresse,CodePostal,Intervenant
                corrected_line = fix_line_6_columns(parts, line_num)
            elif expected_columns == 5:  # Client,Date,Durée,Adresse,Intervenant
                corrected_line = fix_line_5_columns(parts, line_num)
            else:
                # Garder les premières colonnes et fusionner le reste
                corrected_parts = parts[:expected_columns-1]
                corrected_parts.append(','.join(parts[expected_columns-1:]))
                corrected_line = ','.join(corrected_parts)
            
            logger.info(f"Ligne {line_num} corrigée: {line} -> {corrected_line}")
            return corrected_line
        
        elif len(parts) < expected_columns:
            # Pas assez de colonnes, ajouter des valeurs vides
            while len(parts) < expected_columns:
                parts.append('')
            logger.warning(f"Ligne {line_num}: Colonnes manquantes ajoutées")
            return ','.join(parts)
        
        return line
        
    except Exception as e:
        logger.error(f"Erreur ligne {line_num}: {str(e)}")
        return line

def fix_line_6_columns(parts: list, line_num: int) -> str:
    """Corrige une ligne pour 6 colonnes: Client,Date,Durée,Adresse,CodePostal,Intervenant"""
    try:
        # Les 3 premières colonnes sont fixes
        client = parts[0].strip()
        date = parts[1].strip()
        duree = parts[2].strip()
        
        # L'intervenant est la dernière colonne (peut être vide)
        intervenant = parts[-1].strip() if parts[-1].strip() else ""
        
        # Chercher le code postal (probablement numérique)
        code_postal = ""
        code_postal_index = -1
        
        # Chercher de la fin vers le début (en excluant l'intervenant)
        for i in range(len(parts) - 2, 2, -1):
            if parts[i].strip().isdigit() and len(parts[i].strip()) == 5:
                code_postal = parts[i].strip()
                code_postal_index = i
                break
        
        # L'adresse est entre durée et code postal (ou intervenant si pas de code postal)
        if code_postal_index > 0:
            adresse_parts = parts[3:code_postal_index]
        else:
            adresse_parts = parts[3:-1]
            
        adresse = ','.join(adresse_parts).strip()
        
        return f"{client},{date},{duree},{adresse},{code_postal},{intervenant}"
        
    except Exception as e:
        logger.error(f"Erreur correction ligne {line_num}: {str(e)}")
        return ','.join(parts)

def fix_line_5_columns(parts: list, line_num: int) -> str:
    """Corrige une ligne pour 5 colonnes: Client,Date,Durée,Adresse,Intervenant"""
    try:
        # Les 3 premières colonnes sont fixes
        client = parts[0].strip()
        date = parts[1].strip()
        duree = parts[2].strip()
        
        # L'intervenant est la dernière colonne
        intervenant = parts[-1].strip() if parts[-1].strip() else ""
        
        # L'adresse est tout ce qui est entre durée et intervenant
        adresse_parts = parts[3:-1]
        adresse = ','.join(adresse_parts).strip()
        
        return f"{client},{date},{duree},{adresse},{intervenant}"
        
    except Exception as e:
        logger.error(f"Erreur correction ligne {line_num}: {str(e)}")
        return ','.join(parts)