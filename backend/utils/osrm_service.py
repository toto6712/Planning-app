import asyncio
import httpx
import logging
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class OSRMService:
    """Service pour calculer les temps de trajet via OSRM local"""
    
    def __init__(self):
        # Serveur OSRM local Docker
        self.base_url = "http://localhost:5000/route/v1/driving"
        self.timeout = 10  # secondes (généreux pour OSRM local)
        self.max_concurrent_requests = 20  # Nombre de requêtes parallèles
        
    async def calculate_travel_time(self, lat1: float, lon1: float, lat2: float, lon2: float) -> int:
        """Calcule le temps de trajet en minutes entre deux points via OSRM local"""
        try:
            # Format de l'URL OSRM: /route/v1/driving/lon1,lat1;lon2,lat2
            url = f"{self.base_url}/{lon1},{lat1};{lon2},{lat2}"
            
            # Paramètres optimisés pour OSRM local
            params = {
                "overview": "false",  # Pas besoin de la géométrie
                "steps": "false",     # Pas besoin des étapes
                "geometries": "geojson"  # Plus rapide que polyline
            }
            
            logger.debug(f"🗺️ OSRM LOCAL: ({lat1:.6f},{lon1:.6f}) → ({lat2:.6f},{lon2:.6f})")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == "Ok" and data.get("routes"):
                        # Durée en secondes, convertir en minutes
                        duration_seconds = data["routes"][0]["duration"]
                        duration_minutes = max(1, round(duration_seconds / 60))
                        
                        logger.debug(f"✅ OSRM LOCAL: {duration_minutes} min")
                        return duration_minutes
                    else:
                        error_msg = data.get("message", "Route non trouvée")
                        logger.warning(f"⚠️ OSRM LOCAL: Pas de route - {error_msg}")
                        return 15  # Fallback 15 minutes
                else:
                    logger.error(f"❌ OSRM LOCAL: Erreur HTTP {response.status_code}")
                    return 15  # Fallback 15 minutes
                    
        except asyncio.TimeoutError:
            logger.error(f"⏱️ OSRM LOCAL: Timeout après {self.timeout}s")
            return 15  # Fallback 15 minutes
        except Exception as e:
            logger.error(f"❌ OSRM LOCAL: Erreur {str(e)}")
            return 15  # Fallback 15 minutes
    
    
    async def calculate_multiple_routes_parallel(self, coordinates: list) -> dict:
        """Calcule tous les trajets entre une liste de coordonnées en parallèle (OSRM local ultra-rapide)"""
        results = {}
        route_tasks = []
        
        # Préparer tous les calculs
        for i, (lat1, lon1) in enumerate(coordinates):
            coord1_key = f"{lat1},{lon1}"
            results[coord1_key] = {}
            
            for j, (lat2, lon2) in enumerate(coordinates):
                coord2_key = f"{lat2},{lon2}"
                if i == j:
                    results[coord1_key][coord2_key] = 0  # Même point
                else:
                    # Créer une tâche asynchrone pour chaque calcul
                    task = self.calculate_travel_time(lat1, lon1, lat2, lon2)
                    route_tasks.append((task, coord1_key, coord2_key))
        
        total_routes = len(route_tasks)
        logger.info(f"🚀 OSRM LOCAL PARALLÈLE: Calcul de {total_routes} trajets")
        
        # Exécuter par lots pour éviter la surcharge
        batch_size = self.max_concurrent_requests
        completed = 0
        
        for i in range(0, len(route_tasks), batch_size):
            batch = route_tasks[i:i + batch_size]
            batch_tasks = [task for task, _, _ in batch]
            
            # Exécuter le lot en parallèle
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Traiter les résultats du lot
            for j, (task, coord1_key, coord2_key) in enumerate(batch):
                try:
                    travel_time = batch_results[j]
                    if isinstance(travel_time, Exception):
                        travel_time = 15  # Fallback en cas d'erreur
                    results[coord1_key][coord2_key] = travel_time
                    completed += 1
                except Exception as e:
                    logger.error(f"Erreur traitement résultat: {str(e)}")
                    results[coord1_key][coord2_key] = 15
                    completed += 1
            
            # Log de progression
            percentage = (completed / total_routes) * 100
            logger.info(f"📊 Progression OSRM LOCAL: {completed}/{total_routes} ({percentage:.1f}%)")
        
        logger.info(f"✅ OSRM LOCAL PARALLÈLE: Terminé - {completed} trajets calculés")
        return results

    async def calculate_multiple_routes(self, coordinates: list) -> dict:
        """Calcule tous les trajets entre une liste de coordonnées (mode séquentiel pour compatibilité)"""
        # Utiliser la version parallèle qui est beaucoup plus rapide avec OSRM local
        return await self.calculate_multiple_routes_parallel(coordinates)
    
    def coordinates_to_key(self, lat: float, lon: float) -> str:
        """Convertit des coordonnées en clé pour le cache"""
        return f"{lat:.6f},{lon:.6f}"
    
    def key_to_coordinates(self, key: str) -> Tuple[float, float]:
        """Convertit une clé en coordonnées"""
        try:
            lat_str, lon_str = key.split(',')
            return float(lat_str), float(lon_str)
        except:
            raise ValueError(f"Format de clé invalide: {key}")

# Instance globale du service OSRM
osrm_service = OSRMService()