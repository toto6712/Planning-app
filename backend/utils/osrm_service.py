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
    
    async def calculate_multiple_routes(self, coordinates: list) -> dict:
        """Calcule tous les trajets entre une liste de coordonnées"""
        results = {}
        total_routes = len(coordinates) * (len(coordinates) - 1)
        calculated = 0
        
        logger.info(f"🚀 OSRM: Calcul de {total_routes} trajets via OSRM")
        
        for i, (lat1, lon1) in enumerate(coordinates):
            coord1_key = f"{lat1},{lon1}"
            results[coord1_key] = {}
            
            for j, (lat2, lon2) in enumerate(coordinates):
                if i == j:
                    results[coord1_key][f"{lat2},{lon2}"] = 0  # Même point
                    continue
                
                # Calcul du trajet
                travel_time = await self.calculate_travel_time(lat1, lon1, lat2, lon2)
                results[coord1_key][f"{lat2},{lon2}"] = travel_time
                calculated += 1
                
                # Log de progression tous les 10 calculs
                if calculated % 10 == 0:
                    percentage = (calculated / total_routes) * 100
                    logger.info(f"📊 Progression OSRM: {calculated}/{total_routes} ({percentage:.1f}%)")
                
                # Délai pour ne pas surcharger l'API gratuite
                await asyncio.sleep(0.05)  # 50ms entre chaque requête (au lieu de 100ms)
        
        logger.info(f"✅ OSRM: Terminé - {calculated} trajets calculés")
        return results
    
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