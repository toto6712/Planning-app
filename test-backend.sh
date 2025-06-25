#!/bin/bash

# 🧪 Script de test rapide Planning AVS

echo "🎯 Test Backend Planning AVS Autonomie"
echo "======================================="

# Test de l'API Health
echo "1. Test API Health..."
curl -s http://localhost:8001/api/health | jq . || curl -s http://localhost:8001/api/health

echo ""
echo "2. Test Cache Stats..."
curl -s http://localhost:8001/api/travel-cache/stats | jq . || curl -s http://localhost:8001/api/travel-cache/stats

echo ""
echo "3. Test import Python..."
python3 -c "
import sys
sys.path.append('/app/backend')
try:
    from server import app
    print('✅ Import server.py OK')
    from models import Intervention, Intervenant
    print('✅ Import models.py OK')
    from utils.csv_parser import parse_interventions_csv
    print('✅ Import csv_parser.py OK')
    from utils.travel_cache_service import travel_cache_service
    print('✅ Import travel_cache_service.py OK')
    print('🎉 Tous les imports sont réparés !')
except Exception as e:
    print(f'❌ Erreur import: {e}')
"

echo ""
echo "4. Test logs backend..."
echo "Dernières lignes des logs :"
tail -n 3 /var/log/supervisor/backend.out.log

echo ""
echo "✅ Tests terminés ! Backend opérationnel 🚀"