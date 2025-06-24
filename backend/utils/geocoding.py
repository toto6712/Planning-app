from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging
import asyncio
from typing import Tuple, Optional
import time

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="planning-tournees-app", timeout=5)  # Réduire le timeout à 5 secondes
        self.cache = {}  # Cache simple pour éviter les appels répétés
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Géocode une adresse et retourne (latitude, longitude)"""
        try:
            # Vérifier le cache
            if address in self.cache:
                return self.cache[address]
            
            # Ajouter un délai pour respecter les limites de l'API
            await asyncio.sleep(0.5)  # Réduit de 1s à 0.5s
            
            # Géocoder l'adresse
            location = self.geolocator.geocode(address, timeout=5)  # Réduit de 10s à 5s
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
        """Calcule le temps de trajet RÉEL en minutes entre deux adresses - AUCUNE valeur par défaut"""
        try:
            logger.debug(f"🗺️ Géocodage: {address1[:40]}...")
            coords1 = await self.geocode_address(address1)
            
            logger.debug(f"🗺️ Géocodage: {address2[:40]}...")
            coords2 = await self.geocode_address(address2)
            
            if not coords1:
                raise Exception(f"Impossible de géocoder l'adresse de départ: {address1}")
            
            if not coords2:
                raise Exception(f"Impossible de géocoder l'adresse d'arrivée: {address2}")
            
            # Calculer la distance réelle en km
            distance = geodesic(coords1, coords2).kilometers
            logger.debug(f"📏 Distance géodésique: {distance:.3f} km")
            
            # Facteur réaliste pour conduite en ville avec embouteillages
            # 0.75 min/km est TROP optimiste pour la ville
            # Facteur plus réaliste : 1.5-2 min/km en ville
            base_time_minutes = distance * 1.8  # 1.8 min/km (facteur urbain réaliste)
            
            # Arrondir au multiple de 5 supérieur, minimum 5 minutes
            rounded_time = max(5, int((base_time_minutes + 4) / 5) * 5)
            
            logger.info(f"✅ TRAJET CALCULÉ: {address1[:30]}... -> {address2[:30]}... = {distance:.2f}km = {rounded_time}min")
            return int(rounded_time)
            
        except Exception as e:
            error_msg = f"❌ ÉCHEC calcul trajet '{address1[:30]}...' -> '{address2[:30]}...': {str(e)}"
            logger.error(error_msg)
            
            # NE PAS utiliser de valeur par défaut - relancer l'erreur
            raise Exception(f"Calcul de trajet impossible: {str(e)}")
    
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