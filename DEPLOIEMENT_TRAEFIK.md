# 🚀 Déploiement Planning AVS - Configuration Traefik

## 🎯 Configuration DNS Requise

Ajoutez ces enregistrements DNS pour pointer vers votre VPS :

```dns
planning-avs-autonomie.fr   A    VOTRE_IP_VPS
api.avs-autonomie.fr        A    VOTRE_IP_VPS
```

## 📋 Étapes de Déploiement

### 1. Intégration dans votre docker-compose.yml existant

Ajoutez ces services à votre fichier docker-compose.yml existant (après vos services actuels) :

```yaml
  # === PLANNING AVS AUTONOMIE ===
  planning-backend:
    build: ./planning-avs/backend
    container_name: planning-backend
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./planning-avs/backend:/app
      - planning-cache:/app/data
    networks:
      - avs-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.planning-api.rule=Host(\`api.avs-autonomie.fr\`)"
      - "traefik.http.routers.planning-api.entrypoints=websecure"
      - "traefik.http.routers.planning-api.tls=true"
      - "traefik.http.routers.planning-api.tls.certresolver=mytlschallenge"
      - "traefik.http.services.planning-api.loadbalancer.server.port=8001"
      - "traefik.http.middlewares.planning-cors.headers.accessControlAllowOriginList=https://planning-avs-autonomie.fr"
      - "traefik.http.middlewares.planning-cors.headers.accessControlAllowMethods=GET,POST,PUT,DELETE,OPTIONS"
      - "traefik.http.middlewares.planning-cors.headers.accessControlAllowHeaders=*"
      - "traefik.http.routers.planning-api.middlewares=planning-cors"

  planning-frontend:
    build: ./planning-avs/frontend
    container_name: planning-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr
    volumes:
      - ./planning-avs/frontend:/app
      - /app/node_modules
    depends_on:
      - planning-backend
    networks:
      - avs-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.planning-web.rule=Host(\`planning-avs-autonomie.fr\`)"
      - "traefik.http.routers.planning-web.entrypoints=websecure"
      - "traefik.http.routers.planning-web.tls=true"
      - "traefik.http.routers.planning-web.tls.certresolver=mytlschallenge"
      - "traefik.http.services.planning-web.loadbalancer.server.port=3000"
```

### 2. Ajout du volume et vérification du network

Dans la section `volumes:` de votre docker-compose.yml :
```yaml
volumes:
  # Vos volumes existants...
  planning-cache:
    driver: local
```

Vérifiez que le network `avs-network` existe (il est déjà dans votre config).

### 3. Variables d'environnement

Ajoutez dans votre fichier `.env` principal :
```env
# Vos variables existantes...
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 4. Structure des fichiers

```bash
# Sur votre serveur, organisez comme ça :
/votre-projet/
├── docker-compose.yml          # Votre fichier principal avec ajouts
├── .env                       # Variables incluant OPENAI_API_KEY
├── planning-avs/              # Nouveau dossier planning
│   ├── backend/               # Code backend FastAPI
│   ├── frontend/              # Code frontend React
│   └── data/                  # Cache des trajets
├── n8n/                       # Vos dossiers existants...
├── wordpress/
└── traefik/
```

## 🚀 Commandes de Déploiement

```bash
# 1. Clone du projet planning
git clone https://github.com/votre-username/planning-avs.git

# 2. Configuration
cp planning-avs/backend/.env.example planning-avs/backend/.env
cp planning-avs/frontend/.env.example planning-avs/frontend/.env

# Modifier planning-avs/backend/.env avec votre vraie clé OpenAI
echo "OPENAI_API_KEY=sk-your-real-key" > planning-avs/backend/.env

# 3. Ajouter la variable dans votre .env principal
echo "OPENAI_API_KEY=sk-your-real-key" >> .env

# 4. Build et déploiement
docker-compose build planning-backend planning-frontend
docker-compose up -d planning-backend planning-frontend

# 5. Vérification
docker-compose ps
docker-compose logs -f planning-backend
```

## 🔍 Tests de Validation

```bash
# Test certificats SSL
curl -I https://planning-avs-autonomie.fr
curl -I https://api.avs-autonomie.fr

# Test API backend
curl https://api.avs-autonomie.fr/api/health
# Doit retourner: {"status": "healthy"}

# Test cache trajets
curl https://api.avs-autonomie.fr/api/travel-cache/stats
```

## 🌐 URLs Finales

- **Application Planning** : https://planning-avs-autonomie.fr
- **API Backend** : https://api.avs-autonomie.fr
- **Health Check** : https://api.avs-autonomie.fr/api/health
- **Stats Cache** : https://api.avs-autonomie.fr/api/travel-cache/stats

## 🛠️ Monitoring

```bash
# Logs en temps réel
docker-compose logs -f planning-backend
docker-compose logs -f planning-frontend

# Status des services
docker-compose ps | grep planning

# Utilisation ressources
docker stats planning-backend planning-frontend
```

## ⚡ Performance avec OSRM Local

Votre OSRM existant sur port 5000 sera automatiquement utilisé pour des calculs ultra-rapides :
- **1000 trajets** : ~1-2 minutes (au lieu de 15 minutes)
- **Cache persistant** : évite les recalculs
- **Calculs parallèles** : 20 requêtes simultanées

## 🚨 Troubleshooting

### Erreur certificat SSL
```bash
# Vérifier que Traefik génère bien les certificats
docker-compose logs traefik | grep "avs-autonomie"
```

### Erreur CORS
```bash
# Vérifier que les domaines DNS pointent bien vers votre VPS
nslookup planning-avs-autonomie.fr
nslookup api.avs-autonomie.fr
```

### Service ne démarre pas
```bash
# Vérifier les logs
docker-compose logs planning-backend
docker-compose logs planning-frontend
```

---

**Configuration prête pour production avec vos domaines AVS !** 🎯