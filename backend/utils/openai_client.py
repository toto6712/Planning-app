import openai
import json
import logging
import os
import asyncio
from typing import List, Dict, Any
from ..models import Intervention, Intervenant, PlanningEvent
from .planning_validator import planning_validator
from .geocoding import geocoding_service
from .travel_cache_service import travel_cache_service
from .osrm_service import osrm_service
from pathlib import Path

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        # Charger l'environnement
        from dotenv import load_dotenv
        ROOT_DIR = Path(__file__).parent.parent
        load_dotenv(ROOT_DIR / '.env')
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans l'environnement")
            
        self.client = openai.OpenAI(api_key=api_key)
        
        # Charger le prompt depuis le fichier
        prompt_path = ROOT_DIR / 'ia_prompt.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()

    async def get_travel_times_with_cache(self, interventions: List[Intervention], intervenants: List[Intervenant]) -> Dict[str, Dict[str, int]]:
        """Récupère les temps de trajet avec calcul automatique des manquants"""
        logger.info("🗂️ RÉCUPÉRATION des temps de trajet avec cache automatique")
        
        # Collecter TOUTES les coordonnées
        all_coordinates = set()
        
        # Coordonnées des intervenants
        for intervenant in intervenants:
            all_coordinates.add((intervenant.latitude, intervenant.longitude))
            logger.debug(f"Coordonnées intervenant: {intervenant.nom_prenom} -> ({intervenant.latitude:.4f},{intervenant.longitude:.4f})")
        
        # Coordonnées des interventions
        for intervention in interventions:
            all_coordinates.add((intervention.latitude, intervention.longitude))
            logger.debug(f"Coordonnées intervention: {intervention.client} -> ({intervention.latitude:.4f},{intervention.longitude:.4f})")
        
        logger.info(f"📍 {len(all_coordinates)} coordonnées uniques trouvées")
        
        # Calcul automatique des trajets manquants
        calculated_count = await travel_cache_service.calculate_and_cache_missing_routes(all_coordinates)
        
        if calculated_count > 0:
            logger.info(f"✅ {calculated_count} nouveaux trajets calculés et mis en cache")
        
        # Récupérer tous les temps de trajet depuis le cache (maintenant complet)
        travel_times = travel_cache_service.get_cached_travel_times(all_coordinates)
        
        logger.info(f"✅ TOUS les trajets récupérés depuis le cache ({len(travel_times)} adresses)")
        return travel_times
    async def calculate_travel_times(self, interventions: List[Intervention], intervenants: List[Intervenant]) -> Dict[str, Dict[str, int]]:
        """MÉTHODE DÉPRÉCIÉE - Utiliser get_travel_times_from_cache() à la place"""
        logger.info("🗺️ CALCUL EXHAUSTIF des temps de trajet via OpenStreetMap (AUCUNE valeur par défaut)")
        
        # Collecter TOUTES les adresses
        all_addresses = set()
        
        # Adresses des intervenants
        for intervenant in intervenants:
            all_addresses.add(intervenant.adresse)
            logger.debug(f"Adresse intervenant: {intervenant.nom_prenom} -> {intervenant.adresse}")
        
        # Adresses des interventions
        for intervention in interventions:
            all_addresses.add(intervention.adresse)
            logger.debug(f"Adresse intervention: {intervention.client} -> {intervention.adresse}")
        
        all_addresses = list(all_addresses)
        total_pairs = len(all_addresses) * (len(all_addresses) - 1)
        logger.info(f"📍 {len(all_addresses)} adresses uniques trouvées")
        logger.info(f"🔢 {total_pairs} trajets à calculer via OpenStreetMap")
        
        travel_times = {}
        calculated = 0
        errors = 0
        
        # Calculer TOUS les trajets sans limite
        for addr1 in all_addresses:
            travel_times[addr1] = {}
            
            for addr2 in all_addresses:
                if addr1 == addr2:
                    travel_times[addr1][addr2] = 0
                    continue
                
                try:
                    logger.debug(f"🚗 Calcul trajet: {addr1[:30]}... -> {addr2[:30]}...")
                    travel_time = await geocoding_service.calculate_travel_time(addr1, addr2)
                    travel_times[addr1][addr2] = travel_time
                    calculated += 1
                    
                    logger.info(f"✅ Trajet {calculated}/{total_pairs}: {travel_time} min")
                    
                    # Log de progression tous les 10 calculs
                    if calculated % 10 == 0:
                        percentage = (calculated / total_pairs) * 100
                        logger.info(f"📊 Progression: {calculated}/{total_pairs} ({percentage:.1f}%)")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"❌ ERREUR calcul trajet {addr1[:30]}... -> {addr2[:30]}...: {str(e)}")
                    # AUCUNE valeur par défaut - on lève l'erreur ou on réessaie
                    
                    # Réessayer une fois en cas d'erreur temporaire
                    try:
                        logger.warning(f"🔄 Nouvelle tentative pour le trajet...")
                        await asyncio.sleep(1)  # Attendre 1 seconde
                        travel_time = await geocoding_service.calculate_travel_time(addr1, addr2)
                        travel_times[addr1][addr2] = travel_time
                        calculated += 1
                        logger.info(f"✅ Succès après réessai: {travel_time} min")
                    except Exception as e2:
                        logger.error(f"❌ ÉCHEC DÉFINITIF pour trajet {addr1} -> {addr2}: {str(e2)}")
                        # Si vraiment impossible, on met une valeur calculée approximative
                        # Basée sur la distance à vol d'oiseau * facteur réaliste
                        estimated_time = await self._estimate_travel_time_fallback(addr1, addr2)
                        travel_times[addr1][addr2] = estimated_time
                        calculated += 1
                        logger.warning(f"⚠️ Utilisation estimation: {estimated_time} min")
        
        success_rate = ((calculated - errors) / total_pairs) * 100 if total_pairs > 0 else 0
        logger.info(f"🎯 CALCUL TERMINÉ: {calculated}/{total_pairs} trajets calculés")
        logger.info(f"📈 Taux de succès API: {success_rate:.1f}%")
        logger.info(f"❌ Erreurs: {errors}")
        
        return travel_times

    async def _estimate_travel_time_fallback(self, addr1: str, addr2: str) -> int:
        """Estimation de trajet basée sur la distance géodésique en cas d'échec API"""
        try:
            from .geocoding import geocoding_service
            
            # Obtenir les coordonnées
            coords1 = await geocoding_service.geocode_address(addr1)
            coords2 = await geocoding_service.geocode_address(addr2)
            
            if coords1 and coords2:
                from geopy.distance import geodesic
                distance_km = geodesic(coords1, coords2).kilometers
                
                # Facteur réaliste pour la ville (tenir compte des routes, feux, etc.)
                # 1 km = environ 2-3 minutes en ville avec embouteillages
                estimated_minutes = max(5, int(distance_km * 2.5))
                logger.info(f"🧮 Distance géodésique: {distance_km:.2f} km -> estimation: {estimated_minutes} min")
                return estimated_minutes
            else:
                logger.error("Impossible d'obtenir les coordonnées pour l'estimation")
                return 20  # Seule exception où on utilise une valeur fixe
                
        except Exception as e:
            logger.error(f"Erreur estimation fallback: {str(e)}")
            return 20  # Seule exception où on utilise une valeur fixe

    async def generate_planning(self, interventions: List[Intervention], intervenants: List[Intervenant]) -> List[PlanningEvent]:
        """Génère un planning optimisé via OpenAI avec calcul automatique des trajets"""
        try:
            logger.info("🚀 DÉBUT génération planning avec calcul automatique des trajets")
            
            # RÉCUPÉRER LES TEMPS DE TRAJET AVEC CALCUL AUTOMATIQUE
            travel_times = await self.get_travel_times_with_cache(interventions, intervenants)
            
            # Générer la palette de couleurs pour les intervenants
            color_palette = [
                "#32a852", "#3b82f6", "#f59e0b", "#8b5cf6", "#ef4444", 
                "#06b6d4", "#84cc16", "#f97316", "#ec4899", "#6366f1"
            ]
            
            # Créer un mapping couleur pour chaque intervenant (en évitant les doublons)
            intervenant_colors = {}
            noms_uniques = list(set(intervenant.nom_prenom for intervenant in intervenants))  # Éliminer les doublons potentiels
            for i, nom in enumerate(noms_uniques):
                intervenant_colors[nom] = color_palette[i % len(color_palette)]
            
            logger.info(f"Couleurs assignées aux intervenants: {intervenant_colors}")
            
            # Préparer les données en format compact pour l'IA
            interventions_data = []
            for i in interventions:
                data = {
                    "client": i.client,
                    "date": i.date,
                    "duree": i.duree,
                    "latitude": i.latitude,
                    "longitude": i.longitude,
                    "secteur": i.secteur
                }
                # N'ajouter l'intervenant que s'il est spécifié
                if i.intervenant:
                    data["intervenant_impose"] = i.intervenant
                # Ajouter les champs spéciaux
                if i.binome:
                    data["binome"] = True
                if i.intervenant_referent:
                    data["intervenant_referent"] = i.intervenant_referent
                interventions_data.append(data)
            
            intervenants_data = []
            for i, intervenant in enumerate(intervenants):
                data = {
                    "nom_prenom": intervenant.nom_prenom,
                    "latitude": intervenant.latitude,
                    "longitude": intervenant.longitude,
                    "heure_hebdomaire": intervenant.heure_hebdomaire,
                    "heure_mensuel": intervenant.heure_mensuel,
                    "roulement_weekend": intervenant.roulement_weekend,
                    "couleur_assignee": intervenant_colors[intervenant.nom_prenom]
                }
                # Ajouter les champs optionnels
                if intervenant.plage_horaire_autorisee:
                    data["plage_horaire_autorisee"] = intervenant.plage_horaire_autorisee
                if intervenant.specialites:
                    data["specialites"] = intervenant.specialites
                intervenants_data.append(data)
            
            # Construire un message utilisateur compact avec temps de trajet
            user_message = f"""INTERVENTIONS ({len(interventions_data)} total - traiter CHAQUE une EXACTEMENT UNE fois):
{json.dumps(interventions_data, ensure_ascii=False)}

INTERVENANTS ({len(intervenants_data)} total):
{json.dumps(intervenants_data, ensure_ascii=False)}

TEMPS DE TRAJET CALCULÉS (OSRM - en minutes) - Format: "latitude,longitude" -> temps:
{json.dumps(travel_times, ensure_ascii=False)}

RÈGLES CRITIQUES:
- UTILISER les temps de trajet réels fournis ci-dessus (format latitude,longitude)
- AUCUN intervenant ne peut être à 2 endroits en même temps
- VÉRIFIER les horaires avant assignation
- Temps entre interventions = temps de trajet réel + 5 min minimum
- Si conflit: chercher autre intervenant ou marquer non_planifiable

RETOURNER {len(interventions_data)} interventions SANS DOUBLONS ni CONFLITS."""
            
            logger.info(f"Envoi de {len(interventions_data)} interventions et {len(intervenants_data)} intervenants à OpenAI...")
            logger.info(f"Taille du message: ~{len(user_message)} caractères")
            
            # Utiliser GPT-4o-mini qui a des limites plus élevées
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.05,  # Très faible pour cohérence maximale
                max_tokens=4000
            )
            
            # Extraire la réponse
            planning_json = response.choices[0].message.content.strip()
            logger.info(f"Réponse OpenAI reçue: {len(planning_json)} caractères")
            logger.info(f"Début de la réponse: {planning_json[:200]}...")
            
            # Nettoyer et extraire le JSON
            try:
                # Supprimer les balises markdown si présentes
                if "```json" in planning_json:
                    start = planning_json.find("```json") + 7
                    end = planning_json.find("```", start)
                    if end > start:
                        planning_json = planning_json[start:end].strip()
                elif "```" in planning_json:
                    start = planning_json.find("```") + 3
                    end = planning_json.find("```", start)
                    if end > start:
                        planning_json = planning_json[start:end].strip()
                
                # Trouver le JSON array
                start_bracket = planning_json.find("[")
                end_bracket = planning_json.rfind("]")
                
                if start_bracket >= 0 and end_bracket > start_bracket:
                    clean_json = planning_json[start_bracket:end_bracket + 1]
                    logger.info(f"JSON extrait: {clean_json[:100]}...")
                    planning_data = json.loads(clean_json)
                else:
                    # Si pas de crochets trouvés, essayer de parser directement
                    if planning_json.strip():
                        planning_data = json.loads(planning_json)
                    else:
                        raise ValueError("Réponse OpenAI vide")
                        
            except json.JSONDecodeError as e:
                logger.error(f"Erreur parsing JSON OpenAI: {str(e)}")
                logger.error(f"Contenu complet reçu: {planning_json}")
                
                # Tentative de récupération en cas d'erreur
                if not planning_json.strip():
                    raise ValueError("L'IA n'a pas retourné de réponse. Réessayez avec moins d'interventions ou vérifiez votre clé OpenAI.")
                
                # Essayer de générer un planning de base en cas d'échec total
                logger.warning("Génération d'un planning de base en cas d'échec de l'IA")
                planning_data = await self.generate_fallback_planning(interventions, intervenants, travel_times)
                
            except Exception as e:
                logger.error(f"Erreur inattendue lors du parsing: {str(e)}")
                logger.error(f"Réponse complète: {planning_json}")
                raise ValueError(f"Impossible de traiter la réponse de l'IA: {str(e)}")
            
            # Vérifier que planning_data est une liste
            if not isinstance(planning_data, list):
                logger.error(f"Format de réponse invalide: {type(planning_data)}")
                raise ValueError("L'IA n'a pas retourné une liste d'interventions valide")
            
            if not planning_data:
                logger.error("Liste d'interventions vide retournée par l'IA")
                raise ValueError("L'IA n'a retourné aucune intervention planifiée")
            
            # Vérifier que toutes les interventions ont été traitées
            if len(planning_data) != len(interventions_data):
                logger.warning(f"⚠️ Nombre d'interventions différent: attendu {len(interventions_data)}, reçu {len(planning_data)}")
            
            # Convertir en objets PlanningEvent
            planning_events = []
            for event_data in planning_data:
                try:
                    # Vérifier/corriger la couleur selon l'intervenant
                    intervenant_name = event_data.get('intervenant', '')
                    assigned_color = event_data.get('color', '#64748b')
                    
                    # Si l'intervenant a une couleur assignée, l'utiliser
                    if intervenant_name in intervenant_colors:
                        assigned_color = intervenant_colors[intervenant_name]
                    
                    event = PlanningEvent(
                        client=event_data.get('client', ''),
                        intervenant=intervenant_name,
                        start=event_data.get('start', ''),
                        end=event_data.get('end', ''),
                        color=assigned_color,
                        non_planifiable=event_data.get('non_planifiable', False),
                        trajet_precedent=event_data.get('trajet_precedent', '0 min'),
                        latitude=event_data.get('latitude', 0.0),
                        longitude=event_data.get('longitude', 0.0),
                        raison=event_data.get('raison', None)
                    )
                    planning_events.append(event)
                except Exception as e:
                    logger.error(f"Erreur création PlanningEvent: {str(e)}")
                    continue
            
            logger.info(f"Planning brut généré avec {len(planning_events)} événements")
            
            # VALIDATION ET CORRECTION DES CONFLITS
            validated_planning = planning_validator.validate_and_fix_planning(planning_events)
            
            logger.info(f"✅ Planning final validé avec {len(validated_planning)} événements")
            
            return validated_planning
            
        except openai.APIError as e:
            logger.error(f"Erreur API OpenAI: {str(e)}")
            if "rate_limit_exceeded" in str(e):
                raise ValueError("Limite de tokens OpenAI dépassée. Réessayez dans 1 minute ou contactez votre administrateur pour augmenter les limites.")
            else:
                raise ValueError(f"Erreur OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur génération planning: {str(e)}")
            raise ValueError(f"Erreur interne: {str(e)}")
    
    async def generate_fallback_planning(self, interventions: List[Intervention], intervenants: List[Intervenant], travel_times: Dict[str, Dict[str, int]]) -> list:
        """Génère un planning de base en cas d'échec de l'IA"""
        try:
            logger.info("Génération d'un planning de fallback")
            fallback_planning = []
            
            # Couleurs de base
            colors = ["#32a852", "#3b82f6", "#f59e0b", "#8b5cf6", "#ef4444"]
            
            for i, intervention in enumerate(interventions):
                try:
                    # Assigner un intervenant de base
                    intervenant_assigned = intervention.intervenant if intervention.intervenant else (
                        intervenants[i % len(intervenants)].nom_prenom if intervenants else "Non assigné"
                    )
                    
                    # Calculer l'heure de fin (ajouter la durée à l'heure de début)
                    start_time = intervention.date  # Format: "29/06/2025 08:00"
                    duration = intervention.duree   # Format: "01:00"
                    
                    # Convertir au format ISO
                    date_part, time_part = start_time.split(" ")
                    day, month, year = date_part.split("/")
                    start_iso = f"{year}-{month}-{day}T{time_part}"
                    
                    # Calculer l'heure de fin
                    from datetime import datetime, timedelta
                    start_dt = datetime.fromisoformat(start_iso)
                    duration_parts = duration.split(":")
                    duration_td = timedelta(hours=int(duration_parts[0]), minutes=int(duration_parts[1]))
                    end_dt = start_dt + duration_td
                    end_iso = end_dt.isoformat()
                    
                    # Calculer le temps de trajet pour ce fallback
                    trajet_temps = "0 min"
                    if i > 0 and len(fallback_planning) > 0:
                        # Prendre les coordonnées de la dernière intervention
                        prev_lat = fallback_planning[-1]["latitude"]
                        prev_lon = fallback_planning[-1]["longitude"]
                        current_lat = intervention.latitude
                        current_lon = intervention.longitude
                        
                        # Chercher dans le cache des temps de trajet
                        prev_key = f"{prev_lat:.6f},{prev_lon:.6f}"
                        current_key = f"{current_lat:.6f},{current_lon:.6f}"
                        
                        if prev_key in travel_times and current_key in travel_times[prev_key]:
                            trajet_minutes = travel_times[prev_key][current_key]
                            trajet_temps = f"{trajet_minutes} min"
                    
                    fallback_event = {
                        "client": intervention.client,
                        "intervenant": intervenant_assigned,
                        "start": start_iso,
                        "end": end_iso,
                        "color": colors[i % len(colors)],
                        "non_planifiable": False,
                        "trajet_precedent": trajet_temps,
                        "latitude": intervention.latitude,
                        "longitude": intervention.longitude
                    }
                    
                    fallback_planning.append(fallback_event)
                    
                except Exception as e:
                    logger.error(f"Erreur création fallback pour intervention {i}: {str(e)}")
                    continue
            
            logger.info(f"Planning de fallback généré avec {len(fallback_planning)} interventions")
            return fallback_planning
            
        except Exception as e:
            logger.error(f"Erreur génération fallback: {str(e)}")
            return []
    
    def calculate_stats(self, planning_events: List[PlanningEvent], total_interventions: int, total_intervenants: int) -> Dict[str, Any]:
        """Calcule las statistiques du planning"""
        try:
            planifiees = sum(1 for event in planning_events if not event.non_planifiable)
            non_planifiables = sum(1 for event in planning_events if event.non_planifiable)
            
            taux_planification = (planifiees / total_interventions * 100) if total_interventions > 0 else 0
            
            return {
                "total_interventions": total_interventions,
                "interventions_planifiees": planifiees,
                "interventions_non_planifiables": non_planifiables,
                "intervenants": total_intervenants,
                "taux_planification": round(taux_planification, 1)
            }
        except Exception as e:
            logger.error(f"Erreur calcul statistiques: {str(e)}")
            return {
                "total_interventions": total_interventions,
                "interventions_planifiees": 0,
                "interventions_non_planifiables": total_interventions,
                "intervenants": total_intervenants,
                "taux_planification": 0.0
            }

# Instance globale du client OpenAI
openai_client = OpenAIClient()