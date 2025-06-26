# Étape 1 : Build de l'application
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install --force
COPY . .
RUN npm run build

# Étape 2 : Serveur statique avec serve
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve

COPY --from=builder /app/build ./build

EXPOSE 80
CMD ["serve", "-s", "build", "-l", "80"]
