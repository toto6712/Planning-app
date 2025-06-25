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
        import time
        
        results = {}
        route_tasks = []
        
        logger.info(f"🚀 === OSRM LOCAL PARALLÈLE DÉMARRÉ ===")
        start_time = time.time()
        
        # Préparer tous les calculs
        prep_start = time.time()
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
        
        prep_time = time.time() - prep_start
        total_routes = len(route_tasks)
        
        logger.info(f"📊 Préparation terminée en {prep_time:.3f}s")
        logger.info(f"🔢 Total à calculer: {total_routes} trajets")
        logger.info(f"⚡ Parallélisme: {self.max_concurrent_requests} requêtes simultanées")
        
        # Exécuter par lots pour éviter la surcharge
        batch_size = self.max_concurrent_requests
        completed = 0
        calculation_times = []
        
        for batch_num, i in enumerate(range(0, len(route_tasks), batch_size), 1):
            batch = route_tasks[i:i + batch_size]
            batch_start = time.time()
            
            logger.info(f"🔄 Lot {batch_num}/{(len(route_tasks) + batch_size - 1) // batch_size}")
            logger.info(f"   📦 Trajets dans ce lot: {len(batch)}")
            
            batch_tasks = [task for task, _, _ in batch]
            
            # Exécuter le lot en parallèle
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                batch_time = time.time() - batch_start
                calculation_times.append(batch_time)
                
                # Traiter les résultats du lot
                for j, (task, coord1_key, coord2_key) in enumerate(batch):
                    try:
                        travel_time = batch_results[j]
                        if isinstance(travel_time, Exception):
                            logger.warning(f"   ⚠️ Erreur trajet {coord1_key} -> {coord2_key}: {travel_time}")
                            travel_time = 15  # Fallback en cas d'erreur
                        results[coord1_key][coord2_key] = travel_time
                        completed += 1
                    except Exception as e:
                        logger.error(f"   ❌ Erreur traitement résultat: {str(e)}")
                        results[coord1_key][coord2_key] = 15
                        completed += 1
                
                # Statistiques du lot
                percentage = (completed / total_routes) * 100
                avg_time_per_route = batch_time / len(batch) if len(batch) > 0 else 0
                
                logger.info(f"   ✅ Lot terminé en {batch_time:.2f}s")
                logger.info(f"   ⚡ {avg_time_per_route*1000:.1f}ms par trajet")
                logger.info(f"   📊 Progression globale: {completed}/{total_routes} ({percentage:.1f}%)")
                
                # Estimation du temps restant
                if completed > 0 and completed < total_routes:
                    avg_batch_time = sum(calculation_times) / len(calculation_times)
                    remaining_batches = (total_routes - completed + batch_size - 1) // batch_size
                    eta = remaining_batches * avg_batch_time
                    logger.info(f"   ⏱️ Temps restant estimé: {eta:.1f}s")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors du traitement du lot {batch_num}: {str(e)}")
                # Marquer tous les trajets du lot comme échoués
                for task, coord1_key, coord2_key in batch:
                    results[coord1_key][coord2_key] = 15
                    completed += 1
        
        total_time = time.time() - start_time
        
        logger.info(f"✅ === OSRM LOCAL PARALLÈLE TERMINÉ ===")
        logger.info(f"📊 Statistiques finales:")
        logger.info(f"   • Trajets calculés: {completed}")
        logger.info(f"   • Temps total: {total_time:.2f}s")
        logger.info(f"   • Vitesse moyenne: {completed/total_time:.1f} trajets/seconde")
        logger.info(f"   • Temps moyen par trajet: {total_time/completed*1000:.1f}ms")
        
        if calculation_times:
            avg_batch_time = sum(calculation_times) / len(calculation_times)
            logger.info(f"   • Temps moyen par lot: {avg_batch_time:.2f}s")
        
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