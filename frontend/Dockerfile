FROM node:18-alpine

WORKDIR /app

# Dépendances
COPY package*.json ./
RUN npm install

# Code application
COPY . .

# Variables d'environnement build pour AVS
ARG REACT_APP_BACKEND_URL=https://api.avs-autonomie.fr
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Port d'exposition
EXPOSE 3000

# Santé check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3000 || exit 1

# Commande de démarrage
CMD ["npm", "start"]