import pandas as pd
import os
import logging
from typing import Dict, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class TravelCacheService:
    """Service pour gérer le cache persistant des temps de trajet"""
    
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
                    addr1 = row['adresse_depart']
                    addr2 = row['adresse_arrivee']
                    temps = int(row['temps_minutes'])
                    
                    if addr1 not in self.cache_dict:
                        self.cache_dict[addr1] = {}
                    self.cache_dict[addr1][addr2] = temps
                
                logger.info(f"Dictionnaire de cache construit avec {len(self.cache_dict)} adresses de départ")
            else:
                logger.info(f"Aucun cache existant trouvé, création d'un nouveau cache")
                self.cache_df = pd.DataFrame({
                    'adresse_depart': [],
                    'adresse_arrivee': [],
                    'temps_minutes': [],
                    'date_calcul': []
                })
                self.cache_dict = {}
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache: {str(e)}")
            # Créer un cache vide en cas d'erreur
            self.cache_df = pd.DataFrame({
                'adresse_depart': [],
                'adresse_arrivee': [],
                'temps_minutes': [],
                'date_calcul': []
            })
            self.cache_dict = {}
    
    def get_travel_time(self, addr1: str, addr2: str) -> Optional[int]:
        """Récupère le temps de trajet depuis le cache"""
        try:
            if addr1 in self.cache_dict and addr2 in self.cache_dict[addr1]:
                temps = self.cache_dict[addr1][addr2]
                logger.debug(f"🎯 Cache HIT: {addr1[:30]}... -> {addr2[:30]}... = {temps} min")
                return temps
            else:
                logger.debug(f"🚫 Cache MISS: {addr1[:30]}... -> {addr2[:30]}...")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache: {str(e)}")
            return None
    
    def add_travel_time(self, addr1: str, addr2: str, temps_minutes: int):
        """Ajoute un temps de trajet au cache"""
        try:
            # Ajouter au dictionnaire
            if addr1 not in self.cache_dict:
                self.cache_dict[addr1] = {}
            self.cache_dict[addr1][addr2] = temps_minutes
            
            # Ajouter au DataFrame
            new_row = pd.DataFrame({
                'adresse_depart': [addr1],
                'adresse_arrivee': [addr2],
                'temps_minutes': [temps_minutes],
                'date_calcul': [datetime.now().isoformat()]
            })
            
            self.cache_df = pd.concat([self.cache_df, new_row], ignore_index=True)
            
            logger.debug(f"💾 Cache ADD: {addr1[:30]}... -> {addr2[:30]}... = {temps_minutes} min")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout au cache: {str(e)}")
    
    def save_cache(self):
        """Sauvegarde le cache dans le fichier CSV"""
        try:
            self.cache_df.to_csv(self.cache_file_path, index=False)
            logger.info(f"💾 Cache sauvegardé: {len(self.cache_df)} trajets dans {self.cache_file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache: {str(e)}")
    
    def get_missing_routes(self, addresses: Set[str]) -> Set[Tuple[str, str]]:
        """Retourne les routes manquantes dans le cache"""
        missing_routes = set()
        addresses_list = list(addresses)
        
        for i, addr1 in enumerate(addresses_list):
            for j, addr2 in enumerate(addresses_list):
                if i != j:  # Ne pas inclure les trajets vers soi-même
                    if self.get_travel_time(addr1, addr2) is None:
                        missing_routes.add((addr1, addr2))
        
        logger.info(f"📊 Routes manquantes: {len(missing_routes)} sur {len(addresses_list) * (len(addresses_list) - 1)} total")
        return missing_routes
    
    def get_cached_travel_times(self, addresses: Set[str]) -> Dict[str, Dict[str, int]]:
        """Retourne tous les temps de trajet disponibles dans le cache pour les adresses données"""
        travel_times = {}
        
        for addr1 in addresses:
            if addr1 in self.cache_dict:
                travel_times[addr1] = {}
                for addr2 in addresses:
                    if addr2 in self.cache_dict[addr1]:
                        travel_times[addr1][addr2] = self.cache_dict[addr1][addr2]
                    elif addr1 == addr2:
                        travel_times[addr1][addr2] = 0  # Temps de trajet vers soi-même
        
        return travel_times
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Retourne les statistiques du cache"""
        try:
            unique_addresses = set()
            if not self.cache_df.empty:
                unique_addresses.update(self.cache_df['adresse_depart'].unique())
                unique_addresses.update(self.cache_df['adresse_arrivee'].unique())
            
            return {
                'total_routes': len(self.cache_df),
                'unique_addresses': len(unique_addresses),
                'cache_file_path': self.cache_file_path,
                'cache_file_exists': os.path.exists(self.cache_file_path),
                'cache_file_size_mb': os.path.getsize(self.cache_file_path) / (1024*1024) if os.path.exists(self.cache_file_path) else 0,
                'last_updated': self.cache_df['date_calcul'].max() if not self.cache_df.empty else None
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                'total_routes': 0,
                'unique_addresses': 0,
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
                'adresse_depart': [],
                'adresse_arrivee': [],
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
    
    def remove_old_entries(self, days_old: int = 30):
        """Supprime les entrées plus anciennes que X jours"""
        try:
            if self.cache_df.empty:
                return
            
            # Convertir les dates
            self.cache_df['date_calcul'] = pd.to_datetime(self.cache_df['date_calcul'])
            cutoff_date = datetime.now() - pd.Timedelta(days=days_old)
            
            # Filtrer les entrées récentes
            recent_entries = self.cache_df[self.cache_df['date_calcul'] >= cutoff_date]
            removed_count = len(self.cache_df) - len(recent_entries)
            
            if removed_count > 0:
                self.cache_df = recent_entries
                # Reconstruire le dictionnaire
                self.load_cache()
                logger.info(f"🧹 Supprimé {removed_count} entrées anciennes du cache")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du cache: {str(e)}")

# Instance globale du service de cache
travel_cache_service = TravelCacheService()