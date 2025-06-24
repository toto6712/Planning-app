import pandas as pd
import os
import logging
from typing import Dict, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class TravelCacheService:
    """Service pour gérer le cache persistant des temps de trajet basé sur les coordonnées"""
    
    def __init__(self, cache_file_path: str = "/app/data/travel_times_cache.csv"):
        self.cache_file_path = cache_file_path
        self.cache_df = None
        self.cache_dict = {}
        
        # Créer le répertoire de données s'il n'existe pas
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
        
        # Charger le cache existant
        self.load_cache()
    
    def load_cache(self):
        """Charge le cache depuis le fichier CSV"""
        try:
            if os.path.exists(self.cache_file_path):
                self.cache_df = pd.read_csv(self.cache_file_path)
                logger.info(f"Cache chargé: {len(self.cache_df)} trajets depuis {self.cache_file_path}")
                
                # Construire le dictionnaire de cache pour un accès rapide
                self.cache_dict = {}
                for _, row in self.cache_df.iterrows():
                    coord1 = f"{row['lat_depart']},{row['lon_depart']}"
                    coord2 = f"{row['lat_arrivee']},{row['lon_arrivee']}"
                    temps = int(row['temps_minutes'])
                    
                    if coord1 not in self.cache_dict:
                        self.cache_dict[coord1] = {}
                    self.cache_dict[coord1][coord2] = temps
                
                logger.info(f"Dictionnaire de cache construit avec {len(self.cache_dict)} coordonnées de départ")
            else:
                logger.info(f"Aucun cache existant trouvé, création d'un nouveau cache")
                self.cache_df = pd.DataFrame({
                    'lat_depart': [],
                    'lon_depart': [],
                    'lat_arrivee': [],
                    'lon_arrivee': [],
                    'temps_minutes': [],
                    'date_calcul': []
                })
                self.cache_dict = {}
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache: {str(e)}")
            # Créer un cache vide en cas d'erreur
            self.cache_df = pd.DataFrame({
                'lat_depart': [],
                'lon_depart': [],
                'lat_arrivee': [],
                'lon_arrivee': [],
                'temps_minutes': [],
                'date_calcul': []
            })
            self.cache_dict = {}
    
    def get_travel_time(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[int]:
        """Récupère le temps de trajet depuis le cache"""
        try:
            coord1 = f"{lat1:.6f},{lon1:.6f}"
            coord2 = f"{lat2:.6f},{lon2:.6f}"
            
            if coord1 in self.cache_dict and coord2 in self.cache_dict[coord1]:
                temps = self.cache_dict[coord1][coord2]
                logger.debug(f"🎯 Cache HIT: ({lat1:.4f},{lon1:.4f}) -> ({lat2:.4f},{lon2:.4f}) = {temps} min")
                return temps
            else:
                logger.debug(f"🚫 Cache MISS: ({lat1:.4f},{lon1:.4f}) -> ({lat2:.4f},{lon2:.4f})")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache: {str(e)}")
            return None
    
    def add_travel_time(self, lat1: float, lon1: float, lat2: float, lon2: float, temps_minutes: int):
        """Ajoute un temps de trajet au cache"""
        try:
            coord1 = f"{lat1:.6f},{lon1:.6f}"
            coord2 = f"{lat2:.6f},{lon2:.6f}"
            
            # Ajouter au dictionnaire
            if coord1 not in self.cache_dict:
                self.cache_dict[coord1] = {}
            self.cache_dict[coord1][coord2] = temps_minutes
            
            # Ajouter au DataFrame
            new_row = pd.DataFrame({
                'lat_depart': [lat1],
                'lon_depart': [lon1],
                'lat_arrivee': [lat2],
                'lon_arrivee': [lon2],
                'temps_minutes': [temps_minutes],
                'date_calcul': [datetime.now().isoformat()]
            })
            
            self.cache_df = pd.concat([self.cache_df, new_row], ignore_index=True)
            
            logger.debug(f"💾 Cache ADD: ({lat1:.4f},{lon1:.4f}) -> ({lat2:.4f},{lon2:.4f}) = {temps_minutes} min")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout au cache: {str(e)}")
    
    def save_cache(self):
        """Sauvegarde le cache dans le fichier CSV"""
        try:
            self.cache_df.to_csv(self.cache_file_path, index=False)
            logger.info(f"💾 Cache sauvegardé: {len(self.cache_df)} trajets dans {self.cache_file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache: {str(e)}")
    
    def get_missing_routes(self, coordinates: Set[Tuple[float, float]]) -> Set[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Retourne les routes manquantes dans le cache"""
        missing_routes = set()
        coord_list = list(coordinates)
        
        for i, coord1 in enumerate(coord_list):
            for j, coord2 in enumerate(coord_list):
                if i != j:  # Ne pas inclure les trajets vers soi-même
                    if self.get_travel_time(coord1[0], coord1[1], coord2[0], coord2[1]) is None:
                        missing_routes.add((coord1, coord2))
        
        logger.info(f"📊 Routes manquantes: {len(missing_routes)} sur {len(coord_list) * (len(coord_list) - 1)} total")
        return missing_routes
    
    def check_all_routes_available(self, coordinates: Set[Tuple[float, float]]) -> Tuple[bool, Set[Tuple[Tuple[float, float], Tuple[float, float]]]]:
        """Vérifie si tous les trajets nécessaires sont disponibles dans le cache"""
        missing_routes = self.get_missing_routes(coordinates)
        all_available = len(missing_routes) == 0
        
        if all_available:
            logger.info("✅ Tous les trajets sont disponibles dans le cache")
        else:
            logger.warning(f"❌ {len(missing_routes)} trajets manquants dans le cache")
            
        return all_available, missing_routes
    
    def get_cached_travel_times(self, coordinates: Set[Tuple[float, float]]) -> Dict[str, Dict[str, int]]:
        """Retourne tous les temps de trajet disponibles dans le cache pour les coordonnées données"""
        travel_times = {}
        
        for lat1, lon1 in coordinates:
            coord1_key = f"{lat1:.6f},{lon1:.6f}"
            travel_times[coord1_key] = {}
            
            for lat2, lon2 in coordinates:
                coord2_key = f"{lat2:.6f},{lon2:.6f}"
                
                if lat1 == lat2 and lon1 == lon2:
                    travel_times[coord1_key][coord2_key] = 0  # Même point
                else:
                    cached_time = self.get_travel_time(lat1, lon1, lat2, lon2)
                    if cached_time is not None:
                        travel_times[coord1_key][coord2_key] = cached_time
        
        return travel_times
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Retourne les statistiques du cache"""
        try:
            unique_coordinates = set()
            if not self.cache_df.empty:
                for _, row in self.cache_df.iterrows():
                    unique_coordinates.add((row['lat_depart'], row['lon_depart']))
                    unique_coordinates.add((row['lat_arrivee'], row['lon_arrivee']))
            
            return {
                'total_routes': len(self.cache_df),
                'unique_coordinates': len(unique_coordinates),
                'cache_file_path': self.cache_file_path,
                'cache_file_exists': os.path.exists(self.cache_file_path),
                'cache_file_size_mb': os.path.getsize(self.cache_file_path) / (1024*1024) if os.path.exists(self.cache_file_path) else 0,
                'last_updated': self.cache_df['date_calcul'].max() if not self.cache_df.empty else None
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                'total_routes': 0,
                'unique_coordinates': 0,
                'cache_file_path': self.cache_file_path,
                'cache_file_exists': False,
                'cache_file_size_mb': 0,
                'last_updated': None,
                'error': str(e)
            }
    
    def clear_cache(self):
        """Vide complètement le cache"""
        try:
            self.cache_df = pd.DataFrame({
                'lat_depart': [],
                'lon_depart': [],
                'lat_arrivee': [],
                'lon_arrivee': [],
                'temps_minutes': [],
                'date_calcul': []
            })
            self.cache_dict = {}
            
            # Supprimer le fichier s'il existe
            if os.path.exists(self.cache_file_path):
                os.remove(self.cache_file_path)
            
            logger.info("🗑️ Cache vidé complètement")
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {str(e)}")
    
    async def calculate_and_cache_missing_routes(self, coordinates: Set[Tuple[float, float]]) -> int:
        """Calcule et cache automatiquement les trajets manquants via OSRM"""
        try:
            from .osrm_service import osrm_service
            
            # Obtenir les trajets manquants
            all_available, missing_routes = self.check_all_routes_available(coordinates)
            
            if all_available:
                logger.info("✅ Aucun trajet manquant, pas de calcul nécessaire")
                return 0
            
            logger.info(f"🚀 Calcul automatique de {len(missing_routes)} trajets manquants via OSRM")
            
            calculated_count = 0
            for (coord1, coord2) in missing_routes:
                lat1, lon1 = coord1
                lat2, lon2 = coord2
                
                # Calculer le temps de trajet via OSRM
                travel_time = await osrm_service.calculate_travel_time(lat1, lon1, lat2, lon2)
                
                # Ajouter au cache
                self.add_travel_time(lat1, lon1, lat2, lon2, travel_time)
                calculated_count += 1
                
                # Log de progression
                if calculated_count % 10 == 0:
                    logger.info(f"📊 Progression cache: {calculated_count}/{len(missing_routes)}")
            
            # Sauvegarder le cache
            self.save_cache()
            
            logger.info(f"✅ {calculated_count} nouveaux trajets calculés et mis en cache")
            return calculated_count
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul automatique: {str(e)}")
            return 0

# Instance globale du service de cache
travel_cache_service = TravelCacheService()