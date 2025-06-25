# 🚀 Configuration Docker Compose + Traefik HTTPS

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

### 2. **Ajout dans votre docker-compose.yml**
```yaml
# Ajouter ces lignes dans votre docker-compose.yml existant

services:
  # Vos services existants...
  
  # === PLANNING SERVICES ===
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
      - "traefik.http.routers.planning-api.rule=Host(\`votre-domaine.com\`) && PathPrefix(\`/api\`)"
      - "traefik.http.routers.planning-api.entrypoints=websecure"
      - "traefik.http.routers.planning-api.tls.certresolver=letsencrypt"
      - "traefik.http.services.planning-api.loadbalancer.server.port=8001"

  planning-frontend:
    build:
      context: ./planning-app/frontend
    container_name: planning-frontend
    restart: unless-stopped
    environment:
      - REACT_APP_BACKEND_URL=https://votre-domaine.com
    depends_on:
      - planning-api
    networks:
      - traefik
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik"
      - "traefik.http.routers.planning-frontend.rule=Host(\`votre-domaine.com\`) && !PathPrefix(\`/api\`)"
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

### 3. **Variables d'Environnement (.env)**
```env
# Ajouter dans votre fichier .env
OPENAI_API_KEY=sk-your-openai-api-key-here

# Remplacer votre-domaine.com par votre vrai domaine
```

### 4. **Commandes de Déploiement**
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

## 🔧 **Configuration Spécifique**

### **Routing Traefik Intelligent**
- **Frontend** : `https://votre-domaine.com/*` (sauf `/api`)
- **Backend** : `https://votre-domaine.com/api/*`
- **Certificats** : Let's Encrypt automatique

### **Sécurité HTTPS**
- ✅ Headers de sécurité automatiques
- ✅ CORS configuré pour votre domaine
- ✅ MongoDB non exposé publiquement
- ✅ SSL/TLS via Let's Encrypt

### **Performance Optimisée**
- ✅ Cache persistant pour les trajets
- ✅ Health checks automatiques
- ✅ Restart policies configurées
- ✅ Networks isolés (internal/traefik)

## 🌍 **URLs Finales**
- **Application** : `https://votre-domaine.com`
- **API** : `https://votre-domaine.com/api/health`
- **Upload CSV** : `https://votre-domaine.com/api/upload-csv`

## 🔍 **Vérification Post-Déploiement**
```bash
# Tester l'API
curl https://votre-domaine.com/api/health

# Vérifier les certificats
curl -I https://votre-domaine.com

# Logs des services
docker-compose logs planning-api
docker-compose logs planning-frontend
```

**Remplacez `votre-domaine.com` par votre vrai domaine dans tous les fichiers !** 🎯