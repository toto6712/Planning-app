from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging
import asyncio
from typing import Tuple, Optional
import time

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="planning-tournees-app")
        self.cache = {}  # Cache simple pour éviter les appels répétés
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Géocode une adresse et retourne (latitude, longitude)"""
        try:
            # Vérifier le cache
            if address in self.cache:
                return self.cache[address]
            
            # Ajouter un délai pour respecter les limites de l'API
            await asyncio.sleep(1)
            
            # Géocoder l'adresse
            location = self.geolocator.geocode(address, timeout=10)
            if location:
                coords = (location.latitude, location.longitude)
                self.cache[address] = coords
                logger.info(f"Géocodage réussi pour '{address}': {coords}")
                return coords
            else:
                logger.warning(f"Géocodage échoué pour '{address}'")
                return None
                
        except Exception as e:
            logger.error(f"Erreur géocodage pour '{address}': {str(e)}")
            return None
    
    async def calculate_travel_time(self, address1: str, address2: str) -> int:
        """Calcule le temps de trajet en minutes entre deux adresses"""
        try:
            coords1 = await self.geocode_address(address1)
            coords2 = await self.geocode_address(address2)
            
            if not coords1 or not coords2:
                logger.warning(f"Impossible de calculer le trajet entre '{address1}' et '{address2}'")
                return 15  # Valeur par défaut
            
            # Calculer la distance en km
            distance = geodesic(coords1, coords2).kilometers
            
            # Appliquer la règle : 0.75 min/km, arrondi à 5 min
            travel_time_minutes = distance * 0.75
            rounded_time = max(5, round(travel_time_minutes / 5) * 5)  # Arrondi à 5 min près, min 5 min
            
            logger.info(f"Trajet {address1} -> {address2}: {distance:.2f}km = {rounded_time}min")
            return int(rounded_time)
            
        except Exception as e:
            logger.error(f"Erreur calcul trajet '{address1}' -> '{address2}': {str(e)}")
            return 15  # Valeur par défaut en cas d'erreur
    
    async def geocode_multiple_addresses(self, addresses: list) -> dict:
        """Géocode plusieurs adresses en lot avec cache"""
        results = {}
        
        for address in addresses:
            if address not in self.cache:
                coords = await self.geocode_address(address)
                results[address] = coords
            else:
                results[address] = self.cache[address]
        
        return results

# Instance globale du service de géocodage
geocoding_service = GeocodingService()