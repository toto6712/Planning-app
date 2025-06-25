# 🚀 Configuration Docker Compose + Traefik HTTPS - AVS Autonomie

## 📋 Instructions d'Intégration

### 1. **Structure des Dossiers sur votre VPS**
```
/votre-projet/
├── docker-compose.yml              # Votre compose principal
├── .env                           # Variables d'environnement
├── planning-app/                  # Nouveau dossier planning
│   ├── backend/
│   │   ├── Dockerfile            # Copier Dockerfile.backend
│   │   ├── requirements.txt      # Copier depuis /app/backend/
│   │   ├── server.py            # Copier depuis /app/backend/
│   │   ├── models.py            # Copier depuis /app/backend/
│   │   ├── routes.py            # Copier depuis /app/backend/
│   │   ├── .env                 # Variables backend
│   │   └── utils/               # Copier dossier complet
│   ├── frontend/
│   │   ├── Dockerfile           # Copier Dockerfile.frontend
│   │   ├── package.json         # Copier depuis /app/frontend/
│   │   ├── src/                 # Copier dossier complet
│   │   └── public/              # Copier dossier complet
│   └── mongo-init.js            # Script d'init MongoDB
└── traefik/                     # Votre config Traefik existante
```

### 2. **Configuration DNS AVS Autonomie**
Assurez-vous que ces sous-domaines pointent vers votre VPS :
```
planning.avs-autonomie.fr  →  IP_DE_VOTRE_VPS
api.avs-autonomie.fr       →  IP_DE_VOTRE_VPS
```

### 3. **Ajout dans votre docker-compose.yml**
```yaml
# Ajouter ces lignes dans votre docker-compose.yml existant

services:
  # Vos services existants...
  
  # === PLANNING AVS AUTONOMIE ===
  planning-api:
    build:
      context: ./planning-app/backend
    container_name: planning-api
    restart: unless-stopped
    environment:
      - MONGO_URL=mongodb://planning-mongodb:27017/planning_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DB_NAME=planning_db
    volumes:
      - ./planning-app/backend:/app
      - planning-cache:/app/data
    depends_on:
      - planning-mongodb
    networks:
      - traefik
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik"
      - "traefik.http.routers.planning-api.rule=Host(\`api.avs-autonomie.fr\`)"
      - "traefik.http.routers.planning-api.entrypoints=websecure"
      - "traefik.http.routers.planning-api.tls.certresolver=letsencrypt"
      - "traefik.http.services.planning-api.loadbalancer.server.port=8001"
      - "traefik.http.middlewares.planning-api-cors.headers.accessControlAllowOriginList=https://planning.avs-autonomie.fr"
      - "traefik.http.routers.planning-api.middlewares=planning-api-cors"

  planning-frontend:
    build:
      context: ./planning-app/frontend
    container_name: planning-frontend
    restart: unless-stopped
    environment:
      - REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr
    depends_on:
      - planning-api
    networks:
      - traefik
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik"
      - "traefik.http.routers.planning-frontend.rule=Host(\`planning.avs-autonomie.fr\`)"
      - "traefik.http.routers.planning-frontend.entrypoints=websecure"
      - "traefik.http.routers.planning-frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.planning-frontend.loadbalancer.server.port=3000"

  planning-mongodb:
    image: mongo:7.0
    container_name: planning-mongodb
    restart: unless-stopped
    environment:
      - MONGO_INITDB_DATABASE=planning_db
    volumes:
      - planning-mongodb-data:/data/db
      - ./planning-app/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    networks:
      - internal

volumes:
  planning-mongodb-data:
  planning-cache:

networks:
  traefik:
    external: true
  internal:
    driver: bridge
```

### 4. **Variables d'Environnement (.env)**
```env
# Ajouter dans votre fichier .env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 5. **Fichier .env Frontend**
```env
# Dans planning-app/frontend/.env
REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr
```

### 6. **Fichier .env Backend**
```env
# Dans planning-app/backend/.env
MONGO_URL=mongodb://planning-mongodb:27017/planning_db
OPENAI_API_KEY=sk-your-openai-api-key-here
DB_NAME=planning_db
```

### 7. **Commandes de Déploiement**
```bash
# Sur votre VPS

# 1. Copier les fichiers
scp -r /app/backend/* user@votre-vps:/votre-projet/planning-app/backend/
scp -r /app/frontend/* user@votre-vps:/votre-projet/planning-app/frontend/
scp /app/Dockerfile.backend user@votre-vps:/votre-projet/planning-app/backend/Dockerfile
scp /app/Dockerfile.frontend user@votre-vps:/votre-projet/planning-app/frontend/Dockerfile
scp /app/mongo-init.js user@votre-vps:/votre-projet/planning-app/

# 2. Construire et déployer
docker-compose build planning-api planning-frontend
docker-compose up -d planning-api planning-frontend planning-mongodb

# 3. Vérifier les services
docker-compose ps
docker-compose logs -f planning-api
```

## 🔧 **Configuration Spécifique AVS**

### **Routing Traefik - Sous-domaines Séparés**
- **Frontend** : `https://planning.avs-autonomie.fr`
- **Backend API** : `https://api.avs-autonomie.fr`
- **Certificats** : Let's Encrypt automatique pour chaque sous-domaine

### **Sécurité HTTPS**
- ✅ Headers de sécurité automatiques
- ✅ CORS configuré : `planning.avs-autonomie.fr` → `api.avs-autonomie.fr`
- ✅ MongoDB non exposé publiquement
- ✅ SSL/TLS via Let's Encrypt

### **Performance Optimisée**
- ✅ Cache persistant pour les trajets
- ✅ Health checks automatiques
- ✅ Restart policies configurées
- ✅ Networks isolés (internal/traefik)

## 🌍 **URLs Finales AVS Autonomie**
- **Application** : `https://planning.avs-autonomie.fr`
- **API Health** : `https://api.avs-autonomie.fr/api/health`
- **Upload CSV** : `https://api.avs-autonomie.fr/api/upload-csv`
- **Export CSV** : `https://api.avs-autonomie.fr/api/export-csv`
- **Export PDF** : `https://api.avs-autonomie.fr/api/export-pdf`

## 🔍 **Vérification Post-Déploiement**
```bash
# Tester l'API
curl https://api.avs-autonomie.fr/api/health

# Vérifier les certificats
curl -I https://planning.avs-autonomie.fr
curl -I https://api.avs-autonomie.fr

# Logs des services
docker-compose logs planning-api
docker-compose logs planning-frontend

# Vérifier OSRM local (si installé)
curl http://localhost:5000/health
```

## 🎯 **Avantages Architecture Sous-domaines**
- ✅ **Séparation claire** : Frontend et API isolés
- ✅ **CORS propre** : Configuration précise des origines
- ✅ **Scaling indépendant** : Possibilité de scaler séparément
- ✅ **Certificats dédiés** : SSL optimal pour chaque service
- ✅ **Monitoring distinct** : Logs et métriques séparés

**Configuration prête pour AVS Autonomie avec performance OSRM locale !** 🚀