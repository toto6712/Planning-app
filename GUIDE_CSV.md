# 📋 Guide de Préparation des Fichiers CSV

## 🎯 Problème Résolu

J'ai amélioré le système pour gérer **tous les types d'encodage** de fichiers CSV et **la colonne Code Postal séparée**. Le système détecte automatiquement l'encodage, reconstitue l'adresse complète en combinant l'adresse et le code postal.

## 📁 Fichiers d'Exemple Créés

J'ai créé deux fichiers d'exemple parfaitement formatés :
- `/app/interventions_exemple.csv` (avec colonne Code Postal)
- `/app/intervenants_exemple.csv`

## 🛠️ Comment Préparer Vos Fichiers CSV

### ✅ Option 1 : Utiliser les Fichiers d'Exemple
1. Téléchargez les fichiers d'exemple depuis le serveur
2. Modifiez-les avec vos données réelles
3. Conservez exactement la même structure

### ✅ Option 2 : Créer Vos Fichiers

#### 📊 Format interventions.csv (AVEC Code Postal séparé)
```csv
Client,Date,Durée,Adresse,Code Postal,Intervenant
Martin Dubois,29/06/2025 08:00,01:00,1 rue des Lilas Strasbourg,67000,
Sophie Bernard,29/06/2025 14:30,00:45,5 avenue des Roses Strasbourg,67100,Dupont
```

**Colonnes obligatoires :**
- `Client` : Nom du client
- `Date` : Format JJ/MM/AAAA HH:MM
- `Durée` : Format HH:MM
- `Adresse` : Adresse sans le code postal
- `Code Postal` : Code postal séparé (optionnel mais recommandé)
- `Intervenant` : Nom imposé ou vide

**💡 Le système combine automatiquement "Adresse" + "Code Postal" pour former l'adresse complète !**

#### 📊 Format interventions.csv (SANS Code Postal séparé - aussi supporté)
```csv
Client,Date,Durée,Adresse,Intervenant
Martin Dubois,29/06/2025 08:00,01:00,1 rue des Lilas 67000 Strasbourg,
Sophie Bernard,29/06/2025 14:30,00:45,5 avenue des Roses 67100 Strasbourg,Dupont
```

#### 👥 Format intervenants.csv
```csv
Nom,Adresse,Disponibilités,Repos,Week-end
Dupont,12 avenue des Vosges Strasbourg,L-M-M-J-V 07-14,2025-07-01,A
Martin,8 rue du Commerce Strasbourg,L-M-M-J-V-S 14-22,,B
```

**Colonnes obligatoires :**
- `Nom` : Nom de l'intervenant
- `Adresse` : Domicile de l'intervenant
- `Disponibilités` : Jours et heures (L-M-M-J-V-S-D HH-HH)
- `Repos` : Date de congé (AAAA-MM-JJ) ou vide
- `Week-end` : Type A ou B

## 🔧 Nouvelles Améliorations

### 🏠 Gestion Intelligente des Adresses
- **Détection automatique** de la colonne Code Postal (CP, Code Postal, Postal, ZIP)
- **Combinaison automatique** Adresse + Code Postal
- **Évite les doublons** si le code postal est déjà dans l'adresse
- **Support flexible** avec ou sans colonne séparée

### 📝 Détection Automatique d'Encodage
Le système essaie automatiquement :
- UTF-8 (standard)
- UTF-8 avec BOM
- ISO-8859-1 (Latin-1)
- Windows-1252
- ASCII

### 🎯 Mapping Flexible des Colonnes
- Ignore les accents (é, è deviennent e)
- Ignore la casse (majuscules/minuscules)
- Recherche partielle des noms de colonnes
- Nettoie automatiquement les espaces
- **Détecte "Code Postal", "CP", "Code_Postal", "ZIP"**

### 🛡️ Gestion d'Erreurs Robuste
- Ignore les lignes avec erreurs
- Continue le traitement même avec des caractères spéciaux
- Messages d'erreur détaillés avec numéro de ligne

## 💡 Conseils pour Excel/LibreOffice

### ✅ Méthode Recommandée avec Code Postal :
1. **Colonne A** : Client
2. **Colonne B** : Date  
3. **Colonne C** : Durée
4. **Colonne D** : Adresse (sans code postal)
5. **Colonne E** : Code Postal
6. **Colonne F** : Intervenant

### ✅ Export :
1. **Enregistrer sous** → Format CSV
2. **Choisir l'encodage UTF-8** si proposé

### ✅ Alternative si Problèmes :
1. **Exporter en CSV**
2. **Ouvrir avec Notepad++**
3. **Encodage** → **Convertir en UTF-8**
4. **Sauvegarder**

## 🚀 Test Rapide

Vous pouvez tester immédiatement avec les fichiers d'exemple que j'ai créés !

Le système :
- ✅ **Détecte automatiquement** la colonne Code Postal
- ✅ **Combine intelligemment** Adresse + Code Postal  
- ✅ **Accepte tous les encodages** de fichiers
- ✅ **Fonctionne** avec ou sans colonne Code Postal séparée