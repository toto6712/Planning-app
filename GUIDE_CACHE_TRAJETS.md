# 🗺️ Système de Cache des Trajets avec Coordonnées GPS - Mode d'emploi

## 📋 Vue d'ensemble

Le système a été optimisé pour utiliser **des coordonnées GPS** au lieu d'adresses textuelles et calculer automatiquement les temps de trajet via **OSRM (OpenStreetMap Routing Machine)**. 

## 🔄 Processus de fonctionnement

### 1. Format CSV modifié
**IMPORTANT** : Les fichiers CSV doivent maintenant utiliser des coordonnées GPS au lieu d'adresses :

#### Interventions.csv
```csv
Client,Date,Durée,Latitude,Longitude,Intervenant
Mme Martin,29/06/2025 08:00,01:00,48.5734,7.7521,
M. Dupont,29/06/2025 09:30,01:30,48.5794,7.7441,Jean Dupont
```

#### Intervenants.csv  
```csv
Nom_Prenom,Latitude,Longitude,Heure_Mensuel,Heure_hebdomadaire
Jean Dupont,48.5800,7.7500,151h,35h
Marie Durand,48.5750,7.7450,169h,39h
```

### 2. Processus automatique à l'upload
1. **Upload des fichiers** → Extraction des coordonnées GPS
2. **Vérification du cache** → Quels trajets sont déjà connus ?
3. **Calcul automatique** → Les trajets manquants sont calculés via OSRM
4. **Enrichissement du cache** → Nouveaux trajets ajoutés automatiquement
5. **Génération du planning** → L'IA utilise tous les trajets disponibles

### 3. Avantages du nouveau système
- ✅ **Calcul automatique** des trajets manquants (plus besoin de fichiers templates)
- ✅ **Précision GPS** au lieu d'adresses textuelles
- ✅ **Enrichissement continu** du cache à chaque upload
- ✅ **API gratuite OSRM** (OpenStreetMap)
- ✅ **Fallback 15min** si calcul impossible

## 🛠️ Endpoints de gestion du cache

### 📊 Statistiques du cache
```
GET /api/travel-cache/stats
```
Retourne les statistiques du cache (nombre de trajets, coordonnées uniques, etc.)

### 🗑️ Vider le cache
```
POST /api/travel-cache/clear
```
Vide complètement le cache (attention : supprime tous les trajets !)

## 📂 Structure du fichier de cache

**Fichier :** `/app/data/travel_times_cache.csv`

**Format :**
```csv
lat_depart,lon_depart,lat_arrivee,lon_arrivee,temps_minutes,date_calcul
48.5734,7.7521,48.5794,7.7441,10,2025-01-01T12:00:00
48.5794,7.7441,48.5734,7.7521,12,2025-01-01T12:00:00
```

## ⚡ Workflow recommandé

1. **Préparer vos CSV** avec coordonnées GPS (via Google ou autre géocodeur)
2. **Upload normal** via l'interface
3. **Calcul automatique** : Le système calcule les trajets manquants
4. **Génération du planning** : L'IA utilise tous les trajets
5. **Cache enrichi** : Les nouveaux trajets sont conservés pour les prochains uploads

## 🎯 Avantages par rapport à l'ancien système

| Ancien système | Nouveau système |
|----------------|-----------------|
| Adresses textuelles | Coordonnées GPS précises |
| Calcul manuel des trajets | Calcul automatique via OSRM |
| Gestion manuelle du cache | Enrichissement automatique |
| Erreurs de géocodage | Coordonnées fiables |
| Processus complexe | Processus simplifié |

## 💡 Conseils

- **Coordonnées précises** : Utilisez des coordonnées avec 4-6 décimales (ex: 48.5734)
- **Géocodage préalable** : Obtenez vos coordonnées via Google Maps ou autre service
- **Format cohérent** : Respectez le format decimal (48.5734, pas 48°34'24")
- **Sauvegarde** : Le cache `/app/data/travel_times_cache.csv` se construit automatiquement

## 🚀 Migration depuis l'ancien système

Si vous avez des fichiers avec des adresses :
1. Géocodez vos adresses pour obtenir latitude/longitude
2. Modifiez vos CSV pour utiliser le nouveau format
3. Uploadez normalement - le système calculera automatiquement les trajets

## ⚙️ Configuration OSRM

Le système utilise l'API publique gratuite d'OSRM :
- **URL** : `http://router.project-osrm.org/route/v1/driving`
- **Limites** : Délai de 100ms entre requêtes pour respecter l'usage équitable
- **Fallback** : 15 minutes si le calcul échoue
- **Gratuit** : Aucune clé API nécessaire

## 🔧 Dépannage

**Erreur "Coordonnées invalides"** : Vérifiez que vos coordonnées sont au format décimal (-90 à 90 pour latitude, -180 à 180 pour longitude)

**Temps de calcul long** : Normal au premier upload avec beaucoup de nouvelles coordonnées. Les uploads suivants seront instantanés.

**Trajets à 15min** : Indique un échec de calcul OSRM (coordonnées inaccessibles, problème réseau, etc.)