// Script d'initialisation MongoDB
/* global db */
const planningDB = db.getSiblingDB('planning_db');

// Créer les collections avec indexes
planningDB.createCollection('planning_events');
planningDB.createCollection('cache_data');

// Index pour performance
planningDB.planning_events.createIndex({ "start": 1 });
planningDB.planning_events.createIndex({ "intervenant": 1 });
planningDB.cache_data.createIndex({ "created_at": 1 });

print('Base de données planning_db initialisée');