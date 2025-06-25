# ✅ CHECKLIST DÉPLOIEMENT AVS AUTONOMIE - Planning Tournées

## 🎯 **Actions AVANT de lancer Docker**

### ☑️ **1. Configuration DNS (OBLIGATOIRE)**
```bash
# Vérifier que ces domaines pointent vers votre VPS IP
nslookup planning.avs-autonomie.fr
nslookup api.avs-autonomie.fr

# Doit retourner l'IP de votre VPS
```

### ☑️ **2. Structure GitHub & Clone**
```bash
# Sur votre VPS
git clone https://github.com/votre-username/planning-avs.git
cd planning-avs

# Structure attendue après clone :
planning-avs/
├── docker-compose.yml              # Votre compose principal avec nos ajouts
├── .env                           # Variables globales
├── planning-app/
│   ├── backend/
│   │   ├── Dockerfile             # Nos Dockerfiles
│   │   ├── requirements.txt       # Dépendances Python
│   │   ├── server.py              # Code FastAPI
│   │   ├── .env                   # Variables backend
│   │   └── utils/                 # Services OSRM, cache, etc.
│   ├── frontend/
│   │   ├── Dockerfile             # Docker React
│   │   ├── package.json           # Dépendances React
│   │   ├── .env                   # Variables frontend
│   │   └── src/                   # Code React
│   └── mongo-init.js              # Init MongoDB
└── traefik/                       # Votre config Traefik existante
```

### ☑️ **3. Variables d'Environnement (CRITIQUE)**
```bash
# .env principal (racine)
echo "OPENAI_API_KEY=sk-your-real-api-key-here" >> .env

# planning-app/frontend/.env
echo "REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr" > planning-app/frontend/.env

# planning-app/backend/.env  
cat > planning-app/backend/.env << EOF
MONGO_URL=mongodb://planning-mongodb:27017/planning_db
OPENAI_API_KEY=sk-your-real-api-key-here
DB_NAME=planning_db
EOF
```

### ☑️ **4. Vérifier Traefik (OBLIGATOIRE)**
```bash
# Traefik doit être running avec les bons networks
docker ps | grep traefik
docker network ls | grep traefik

# Si pas de network traefik :
docker network create traefik
```

## 🚀 **Commandes de Déploiement**

### ☑️ **5. Build & Deploy**
```bash
# Dans le dossier planning-avs/
docker-compose build planning-api planning-frontend
docker-compose up -d planning-api planning-frontend planning-mongodb
```

### ☑️ **6. Vérification Post-Déploiement**
```bash
# Vérifier que les services sont UP
docker-compose ps

# Vérifier les logs (pas d'erreurs)
docker-compose logs planning-api
docker-compose logs planning-frontend

# Tester les endpoints
curl -f https://api.avs-autonomie.fr/api/health
curl -I https://planning.avs-autonomie.fr
```

## ⚡ **OSRM Local (Performance x100)**

### ☑️ **7. Installation OSRM (RECOMMANDÉ)**
```bash
# Option A: Docker OSRM (le plus simple)
wget https://votre-repo/docker-compose.osrm.yml
docker-compose -f docker-compose.osrm.yml up -d

# Option B: Votre OSRM Docker existant
# Assurez-vous qu'il tourne sur localhost:5000

# Test OSRM
curl "http://localhost:5000/route/v1/driving/7.7521,48.5734;7.7441,48.5794"
```

## 🔍 **Troubleshooting Fréquent**

### ❌ **Erreur: "network traefik not found"**
```bash
docker network create traefik
docker-compose up -d
```

### ❌ **Erreur: "CORS policy"**
```bash
# Vérifier que les domaines DNS pointent bien vers votre VPS
# Vérifier que Traefik génère bien les certificats SSL
docker-compose logs traefik | grep "avs-autonomie"
```

### ❌ **Erreur: "OpenAI API key"**
```bash
# Vérifier que la clé est bien dans les .env
grep OPENAI_API_KEY .env
grep OPENAI_API_KEY planning-app/backend/.env
```

### ❌ **Performance lente (sans OSRM local)**
```bash
# Les calculs prendront 10-15 minutes au lieu de 1-2 minutes
# Logs montreront "OSRM: Calcul de X trajets via OSRM" (lent)
# Au lieu de "OSRM LOCAL PARALLÈLE" (rapide)
```

## ✅ **Validation Finale**

### ☑️ **8. Test Complet**
```bash
# 1. Interface accessible
curl -I https://planning.avs-autonomie.fr
# → Doit retourner 200 OK

# 2. API functional  
curl https://api.avs-autonomie.fr/api/health
# → Doit retourner {"status": "healthy"}

# 3. Upload test (avec vos CSV)
# Aller sur https://planning.avs-autonomie.fr
# Uploader vos fichiers interventions.csv + intervenants.csv
# Vérifier la progression enrichie avec "OSRM LOCAL PARALLÈLE"
```

## 🎯 **Résumé Actions Critiques**

1. ✅ **DNS configuré** : planning.avs-autonomie.fr + api.avs-autonomie.fr → IP VPS
2. ✅ **Clé OpenAI** : Dans .env principal + backend .env  
3. ✅ **Traefik running** : Network traefik existe
4. ✅ **Structure GitHub** : Code bien organisé selon notre template
5. ✅ **OSRM local** : Pour performance x100 (optionnel mais recommandé)

**Si ces 5 points sont OK, alors OUI, juste `git clone` + `docker-compose build` + `docker-compose up -d` suffit !** 🚀

---

**Note**: Sans OSRM local, ça fonctionne mais calculs lents (10-15 min). Avec OSRM local : ultra-rapide (1-2 min) ⚡