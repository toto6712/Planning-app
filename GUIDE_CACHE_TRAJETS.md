# 🗺️ Système de Cache des Trajets - Mode d'emploi

## 📋 Vue d'ensemble

Le système a été optimisé pour éviter les calculs répétitifs de temps de trajet. Au lieu d'appeler l'API OpenStreetMap à chaque upload, l'application utilise maintenant un **cache persistant** des temps de trajet.

## 🔄 Processus de fonctionnement

### 1. Upload des fichiers CSV
- Vous uploadez vos fichiers `interventions.csv` et `intervenants.csv` comme d'habitude
- Le système extrait toutes les adresses des fichiers

### 2. Vérification du cache
- ✅ **Si tous les trajets sont dans le cache** → Planning généré immédiatement
- ❌ **Si des trajets manquent** → Erreur avec liste des trajets manquants

### 3. Gestion des trajets manquants
Si des trajets manquent, vous avez plusieurs options :

#### Option A : Fichier template automatique
1. Un fichier `trajets_manquants.csv` est automatiquement créé dans `/app/data/`
2. Complétez les temps de trajet manquants dans ce fichier
3. Importez-le via l'endpoint `/api/travel-cache/import`

#### Option B : Fichier manuel
Créez un fichier CSV avec les colonnes :
```csv
adresse_depart,adresse_arrivee,temps_minutes,date_calcul
1 rue de la Paix 67000 Strasbourg,15 avenue des Vosges 67000 Strasbourg,10,2025-01-01T12:00:00
15 avenue des Vosges 67000 Strasbourg,1 rue de la Paix 67000 Strasbourg,12,2025-01-01T12:00:00
```

## 🛠️ Endpoints de gestion du cache

### 📊 Statistiques du cache
```
GET /api/travel-cache/stats
```
Retourne les statistiques du cache (nombre de trajets, adresses uniques, etc.)

### 📥 Import de trajets
```
POST /api/travel-cache/import
```
Importe des temps de trajet depuis un fichier CSV

### 🗑️ Vider le cache
```
POST /api/travel-cache/clear
```
Vide complètement le cache (attention : supprime tous les trajets !)

### 📋 Télécharger template
```
GET /api/travel-cache/download-template/trajets_manquants.csv
```
Télécharge le fichier template des trajets manquants

## 📂 Structure du fichier de cache

**Fichier :** `/app/data/travel_times_cache.csv`

**Format :**
```csv
adresse_depart,adresse_arrivee,temps_minutes,date_calcul
Adresse complète de départ,Adresse complète d'arrivée,Temps en minutes,Date ISO
```

**Exemple :**
```csv
adresse_depart,adresse_arrivee,temps_minutes,date_calcul
1 rue de la Paix 67000 Strasbourg,15 avenue des Vosges 67000 Strasbourg,10,2025-01-01T12:00:00
15 avenue des Vosges 67000 Strasbourg,1 rue de la Paix 67000 Strasbourg,12,2025-01-01T12:00:00
8 place Kléber 67000 Strasbourg,1 rue de la Paix 67000 Strasbourg,15,2025-01-01T12:00:00
```

## ⚡ Avantages du système

1. **Performance** : Plus de calculs API à chaque upload
2. **Réutilisation** : Les trajets sont conservés entre les sessions
3. **Accumulation** : La base de trajets s'enrichit au fil du temps
4. **Contrôle** : Vous maîtrisez les temps de trajet utilisés
5. **Flexibilité** : Possibilité d'ajuster les temps selon vos connaissances terrain

## 🔧 Workflow recommandé

1. **Premier upload** : Des trajets manqueront, c'est normal
2. **Compléter le template** : Ajoutez les temps de trajet manquants
3. **Importer** : Utilisez l'endpoint d'import
4. **Réessayer** : Relancez la génération de planning
5. **Accumulation** : Au fil des uploads, de moins en moins de trajets manqueront

## 💡 Conseils

- **Cohérence des adresses** : Utilisez toujours le même format d'adresse
- **Bidirectionnel** : N'oubliez pas les trajets dans les deux sens (A→B et B→A)
- **Temps réalistes** : Tenez compte des conditions de circulation de votre zone
- **Sauvegarde** : Le fichier `/app/data/travel_times_cache.csv` peut être sauvegardé

## 🚨 Messages d'erreur

Si vous voyez :
```
❌ TRAJETS MANQUANTS dans le cache (X trajets):
• Adresse1 → Adresse2
• Adresse3 → Adresse4
...
📋 Un fichier template a été créé: /app/data/trajets_manquants.csv
```

Cela signifie que des trajets manquent dans votre cache. Suivez les instructions pour les ajouter.

## 🔄 Migration depuis l'ancien système

L'ancien système qui calculait automatiquement via OpenStreetMap a été remplacé. Les avantages du nouveau système :
- Plus rapide
- Plus fiable
- Économise les appels API
- Vous avez le contrôle total