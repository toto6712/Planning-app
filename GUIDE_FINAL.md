# 🎯 ÉTAPES FINALES - Planning AVS Autonomie

## ✅ **BONNE NOUVELLE : Vous avez déjà OSRM local !**
Votre configuration OSRM est parfaite et va donner une performance ultra-rapide !

## 🧹 **Fichiers nettoyés**
- ❌ Supprimé tous les fichiers Docker inutiles  
- ❌ Supprimé mongo-init.js (pas de MongoDB)
- ✅ Gardé seulement les fichiers essentiels

## 📋 **Actions à faire sur votre VPS**

### **1. Remplacer votre docker-compose.yml**
```bash
# Sauvegarder l'ancien
cp docker-compose.yml docker-compose.yml.backup

# Remplacer par le nouveau (copier docker-compose-final.yml)
```

### **2. Ajouter les variables d'environnement**
```bash
# Dans votre .env principal, ajouter :
echo "OPENAI_API_KEY=sk-your-real-api-key-here" >> .env
```

### **3. Créer la structure des fichiers**
```bash
mkdir -p planning-app/backend
mkdir -p planning-app/frontend

# Copier tous les fichiers depuis /app/ vers planning-app/
```

### **4. Créer les .env spécifiques**
```bash
# Backend
echo "OPENAI_API_KEY=sk-your-real-api-key-here" > planning-app/backend/.env

# Frontend  
echo "REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr" > planning-app/frontend/.env
```

### **5. Créer les Dockerfiles**
```bash
# Dans planning-app/backend/Dockerfile :
```
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

```bash
# Dans planning-app/frontend/Dockerfile :
```
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ENV REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr
EXPOSE 3000
CMD ["npm", "start"]
```

### **6. Configuration DNS**
Vérifiez que ces domaines pointent vers votre VPS :
```
api.avs-autonomie.fr       →  VOTRE_IP_VPS
planning.avs-autonomie.fr  →  VOTRE_IP_VPS
```

### **7. Lancer les services**
```bash
# Build et up des nouveaux services
docker-compose build planning-backend planning-frontend
docker-compose up -d planning-backend planning-frontend

# Vérifier que tout fonctionne
docker-compose ps
curl https://api.avs-autonomie.fr/api/health
```

## 🎯 **Différences principales avec votre config**

### **AVANT (votre config)**
```yaml
- traefik.http.routers.api.rule=Host(`api-planning.avs-autonomie.fr`)
- traefik.http.routers.web.rule=Host(`planning.avs-autonomie.fr`)
```

### **MAINTENANT (config corrigée)**
```yaml
- traefik.http.routers.planning-api.rule=Host(`api.avs-autonomie.fr`)  
- traefik.http.routers.planning-web.rule=Host(`planning.avs-autonomie.fr`)
```

### **AJOUTS IMPORTANTS**
- ✅ Networks `avs-network` ajoutés partout
- ✅ CORS configuré entre les domaines
- ✅ Ports d'exposition ajoutés
- ✅ Volumes corrects pour le cache
- ✅ Variables d'environnement simplifiées

## 🚀 **URLs Finales**
- **Application** : https://planning.avs-autonomie.fr
- **API** : https://api.avs-autonomie.fr/api/health

## ⚡ **Performance Attendue**
Avec votre OSRM local d'Alsace : **1-2 minutes** pour 1000+ trajets !
(Au lieu de 15 minutes avec API externe)

**Votre setup est quasi parfait, juste quelques ajustements ! 🎯**