# 📋 Guide de Préparation des Fichiers CSV

## 🎯 Problème Résolu

J'ai amélioré le système pour gérer **tous les types d'encodage** de fichiers CSV. Le système détecte automatiquement l'encodage et essaie plusieurs formats.

## 📁 Fichiers d'Exemple Créés

J'ai créé deux fichiers d'exemple parfaitement formatés :
- `/app/interventions_exemple.csv`
- `/app/intervenants_exemple.csv`

## 🛠️ Comment Préparer Vos Fichiers CSV

### ✅ Option 1 : Utiliser les Fichiers d'Exemple
1. Téléchargez les fichiers d'exemple depuis le serveur
2. Modifiez-les avec vos données réelles
3. Conservez exactement la même structure

### ✅ Option 2 : Créer Vos Fichiers

#### 📊 Format interventions.csv
```csv
Client,Date,Durée,Adresse,Intervenant
Martin Dubois,29/06/2025 08:00,01:00,1 rue des Lilas Strasbourg,
Sophie Bernard,29/06/2025 14:30,00:45,5 avenue des Roses Strasbourg,Dupont
```

**Colonnes obligatoires :**
- `Client` : Nom du client
- `Date` : Format JJ/MM/AAAA HH:MM
- `Durée` : Format HH:MM
- `Adresse` : Adresse complète
- `Intervenant` : Nom imposé ou vide

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

## 🔧 Améliorations Techniques

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

### 🛡️ Gestion d'Erreurs Robuste
- Ignore les lignes avec erreurs
- Continue le traitement même avec des caractères spéciaux
- Messages d'erreur détaillés avec numéro de ligne

## 💡 Conseils pour Excel/LibreOffice

### ✅ Méthode Recommandée :
1. **Ouvrir Excel/LibreOffice**
2. **Entrer vos données** dans les colonnes
3. **Enregistrer sous** → Format CSV
4. **Choisir l'encodage UTF-8** si proposé

### ✅ Alternative si Problèmes :
1. **Exporter en CSV**
2. **Ouvrir avec Notepad++**
3. **Encodage** → **Convertir en UTF-8**
4. **Sauvegarder**

## 🚀 Test Rapide

Vous pouvez tester immédiatement avec les fichiers d'exemple que j'ai créés !

Le système devrait maintenant accepter **tous vos fichiers CSV** quel que soit leur encodage d'origine.