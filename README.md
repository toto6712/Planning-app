# Planning Tournées AVS Autonomie

Application de planification automatisée des tournées d'intervenants à domicile avec optimisation IA et calculs ultra-rapides via OSRM local.

## 🚀 Fonctionnalités

- **Upload CSV** : Interventions et intervenants avec coordonnées GPS
- **Calculs ultra-rapides** : OSRM local (50-100x plus rapide qu'API externe)
- **Optimisation IA** : Planification automatique via OpenAI GPT-4o-mini
- **Cache intelligent** : Stockage persistant des temps de trajet
- **Export multi-format** : CSV et PDF du planning généré
- **Interface moderne** : React avec progression temps réel

## 📋 Prérequis

- Docker & Docker Compose
- Traefik (pour HTTPS)
- Clé API OpenAI
- OSRM local (recommandé pour performance)

## ⚡ Installation

### 1. Cloner le projet
```bash
git clone https://github.com/votre-username/planning-avs.git
cd planning-avs
```

### 2. Configuration
```bash
# Variables d'environnement
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Modifier avec votre vraie clé OpenAI
nano backend/.env
```

### 3. DNS (Important)
Configurez vos domaines pour pointer vers votre VPS :
```
api.avs-autonomie.fr           →  VOTRE_IP_VPS
planning-avs-autonomie.fr      →  VOTRE_IP_VPS
```

### 4. Déploiement
```bash
docker-compose build
docker-compose up -d
```

## 🔧 Structure du Projet

```
planning-avs/
├── backend/                 # API FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── server.py
│   ├── models.py
│   ├── routes.py
│   ├── .env.example
│   └── utils/
│       ├── csv_parser.py    # Parsing CSV coordonnées
│       ├── travel_cache_service.py  # Cache trajets
│       ├── osrm_service.py  # Calculs OSRM parallèles
│       ├── openai_client.py # Génération planning IA
│       └── export_service.py # Export CSV/PDF
├── frontend/                # Interface React
│   ├── Dockerfile
│   ├── package.json
│   ├── .env.example
│   └── src/
│       └── components/
│           └── PlanningGenerator.jsx
├── data/                    # Cache persistent
│   └── travel_times_cache.csv
└── docker-compose.yml       # Configuration Docker
```

## 🌐 URLs

- **Application** : https://planning-avs-autonomie.fr
- **API** : https://api.avs-autonomie.fr/api/health

## 📊 Format CSV Attendu

### Interventions
```csv
Client,Date,Duree,Latitude,Longitude,Secteur
"Dupont Jean","2024-06-24","60",48.5734,7.7521,"Strasbourg"
```

### Intervenants
```csv
Nom_Prenom,Latitude,Longitude,Heure_hebdomadaire,Heure_Mensuel,Roulement_weekend
"Martin Sophie",48.5856,7.7507,35,152,"Oui"
```

## ⚡ Performance OSRM Local

Pour une performance optimale, installez OSRM local :

```bash
# Exemple pour données Alsace
docker run -d --name osrm-local \
  -p 5000:5000 \
  -v /path/to/osrm-data:/data \
  osrm/osrm-backend \
  osrm-routed --algorithm mld /data/alsace-latest.osrm --port 5000 --ip 0.0.0.0
```

**Performance attendue :**
- Sans OSRM local : 10-15 minutes (1000 trajets)
- Avec OSRM local : 1-2 minutes (1000 trajets)

## 🔧 Variables d'Environnement

### Backend (.env)
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr
```

## 🧪 Test

```bash
# Test API
curl https://api.avs-autonomie.fr/api/health

# Test cache
curl https://api.avs-autonomie.fr/api/travel-cache/stats
```

## 📈 Monitoring

```bash
# Logs services
docker-compose logs -f planning-backend
docker-compose logs -f planning-frontend

# Status
docker-compose ps
```

## 🛠️ Développement

```bash
# Mode développement
docker-compose -f docker-compose.dev.yml up

# Rebuild après modifications
docker-compose build planning-backend
docker-compose up -d planning-backend
```

## 🏗️ Architecture

- **Backend** : FastAPI + cache CSV + OSRM + OpenAI
- **Frontend** : React + progression temps réel
- **Proxy** : Traefik + HTTPS Let's Encrypt
- **Cache** : Persistant via volumes Docker

## 📄 Licence

Projet privé AVS Autonomie

---

**Développé pour AVS Autonomie - Optimisation des tournées d'intervention** 🚀