# 🚀 Installation OSRM Local - Guide Rapide

## Pourquoi OSRM Local ?
- **Performance ultra-rapide** : Calculs en millisecondes au lieu de minutes
- **Pas de limites de requêtes** : Calculs parallèles illimités
- **Fiabilité** : Pas de dépendance aux API externes
- **Économies** : Pas de frais d'API

## 📋 Prérequis VPS
- **RAM** : 4 GB minimum (8 GB recommandé)
- **Disque** : 20 GB d'espace libre minimum
- **Docker** : installé et fonctionnel
- **Docker Compose** : version 1.27+

## ⚡ Installation Express (5 minutes)

### 1. Télécharger le fichier de configuration
```bash
# Sur votre VPS, placez le fichier docker-compose.osrm.yml
wget https://votre-serveur.com/docker-compose.osrm.yml
# OU copiez le contenu du fichier fourni
```

### 2. Lancer OSRM (automatique)
```bash
# Démarrage avec téléchargement automatique des cartes
docker-compose -f docker-compose.osrm.yml up -d

# Suivre les logs d'installation (première fois ~15-20 min)
docker-compose -f docker-compose.osrm.yml logs -f osrm
```

### 3. Vérifier le fonctionnement
```bash
# Test simple
curl "http://localhost:5000/route/v1/driving/2.3522,48.8566;2.2945,48.8583?overview=false"

# Doit retourner un JSON avec la route Paris -> Paris
```

## 🔧 Configuration Optimisée

### Variables d'environnement dans docker-compose.osrm.yml
```yaml
environment:
  - OSRM_THREADS=4        # Nombre de threads (ajustez selon votre CPU)
  - OSRM_MEMORY=4g        # Mémoire allouée
```

### Ajustements selon votre VPS :
- **CPU 2 cores** : `OSRM_THREADS=2`
- **CPU 4+ cores** : `OSRM_THREADS=4`
- **RAM 8GB+** : `mem_limit: 6g`

## 🏁 Après Installation

### Votre application est automatiquement configurée pour :
- **URL OSRM** : `http://localhost:5000`
- **Calculs parallèles** : 20 requêtes simultanées
- **Timeout** : 10 secondes (généreux)
- **Performance** : ~100x plus rapide qu'avant

### Temps de calcul attendus :
- **50 trajets** : ~2-3 secondes
- **500 trajets** : ~15-30 secondes  
- **1500+ trajets** : ~1-2 minutes (au lieu de 15 minutes)

## 🚨 Dépannage

### OSRM ne démarre pas
```bash
# Vérifier les logs
docker-compose -f docker-compose.osrm.yml logs osrm

# Redémarrer si nécessaire
docker-compose -f docker-compose.osrm.yml restart osrm
```

### Erreur de mémoire
```bash
# Augmenter la limite mémoire dans docker-compose.osrm.yml
mem_limit: 6g  # au lieu de 4g
```

### Test de performance
```bash
# Tester les calculs multiples
time curl "http://localhost:5000/route/v1/driving/2.3522,48.8566;2.2945,48.8583?overview=false"
# Doit retourner en < 100ms
```

## 📊 Monitoring

### Vérifier l'état d'OSRM
```bash
# Status des containers
docker ps | grep osrm

# Utilisation des ressources
docker stats osrm-local

# Health check
curl http://localhost:5000/health
```

## 🔄 Maintenance

### Mise à jour des cartes (optionnel, 1x/mois)
```bash
docker-compose -f docker-compose.osrm.yml down
docker volume rm osrm-data
docker-compose -f docker-compose.osrm.yml up -d
# Retélécharge les dernières cartes
```

## ✅ Validation Finale

Une fois OSRM installé et fonctionnel :
1. **Upload vos CSV** dans l'application
2. **Performance** : calculs 50-100x plus rapides
3. **Fiabilité** : plus de timeouts
4. **Logs** : surveillez les logs pour vérifier `OSRM LOCAL PARALLÈLE`

---

**Note** : Le code de l'application a été pré-configuré pour utiliser OSRM local sur `localhost:5000` avec calculs parallèles optimisés.