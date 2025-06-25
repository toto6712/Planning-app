import openai
import json
import logging
import os
import asyncio
from typing import List, Dict, Any
from models import Intervention, Intervenant, PlanningEvent
from utils.planning_validator import planning_validator
from utils.travel_cache_service import travel_cache_service
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
        import time
        start_time = time.time()
        
        logger.info("🗂️ === DÉBUT RÉCUPÉRATION TEMPS DE TRAJET ===")
        
        # Collecter TOUTES les coordonnées
        logger.info("🔄 Collecte des coordonnées...")
        all_coordinates = set()
        
        # Coordonnées des intervenants
        for i, intervenant in enumerate(intervenants, 1):
            all_coordinates.add((intervenant.latitude, intervenant.longitude))
            logger.debug(f"   Intervenant {i}/{len(intervenants)}: {intervenant.nom_prenom} -> ({intervenant.latitude:.4f},{intervenant.longitude:.4f})")
        
        # Coordonnées des interventions
        for i, intervention in enumerate(interventions, 1):
            all_coordinates.add((intervention.latitude, intervention.longitude))
            logger.debug(f"   Intervention {i}/{len(interventions)}: {intervention.client} -> ({intervention.latitude:.4f},{intervention.longitude:.4f})")
        
        total_coords = len(all_coordinates)
        max_possible_routes = total_coords * (total_coords - 1)
        logger.info(f"📍 Coordonnées collectées: {total_coords} uniques")
        logger.info(f"🔢 Trajets théoriques maximum: {max_possible_routes}")
        
        # Calcul automatique des trajets manquants
        logger.info("🔄 Vérification du cache et calcul des trajets manquants...")
        calculation_start = time.time()
        calculated_count = await travel_cache_service.calculate_and_cache_missing_routes(all_coordinates)
        calculation_time = time.time() - calculation_start
        
        if calculated_count > 0:
            logger.info(f"⚡ Performance: {calculated_count} trajets calculés en {calculation_time:.2f}s")
            logger.info(f"📊 Vitesse: {calculated_count/calculation_time:.1f} trajets/seconde")
        else:
            logger.info(f"✅ Tous les trajets étaient déjà en cache")
        
        # Récupérer tous les temps de trajet depuis le cache (maintenant complet)
        logger.info("🔄 Récupération des temps de trajet depuis le cache...")
        travel_times = travel_cache_service.get_cached_travel_times(all_coordinates)
        
        total_time = time.time() - start_time
        actual_routes = sum(len(routes) for routes in travel_times.values())
        
        logger.info(f"✅ === RÉCUPÉRATION TERMINÉE ===")
        logger.info(f"📊 Résumé:")
        logger.info(f"   • Coordonnées uniques: {total_coords}")
        logger.info(f"   • Trajets disponibles: {actual_routes}")
        logger.info(f"   • Nouveaux calculs: {calculated_count}")
        logger.info(f"   • Temps total: {total_time:.2f}s")
        return travel_times
        
    async def generate_planning(self, interventions: List[Intervention], intervenants: List[Intervenant]) -> List[PlanningEvent]:
        """Génère un planning optimisé via OpenAI avec calcul automatique des trajets"""
        import time
        total_start_time = time.time()
        
        try:
            logger.info("🚀 === DÉBUT GÉNÉRATION PLANNING IA ===")
            
            # RÉCUPÉRER LES TEMPS DE TRAJET AVEC CALCUL AUTOMATIQUE
            logger.info("📍 Phase 1/4 - Récupération des temps de trajet")
            travel_times_start = time.time()
            travel_times = await self.get_travel_times_with_cache(interventions, intervenants)
            travel_times_duration = time.time() - travel_times_start
            logger.info(f"✅ Phase 1/4 terminée en {travel_times_duration:.2f}s")
            
            # PRÉPARATION DES DONNÉES POUR L'IA
            logger.info("🔧 Phase 2/4 - Préparation des données pour l'IA")
            prep_start = time.time()
            
            # Générer la palette de couleurs pour les intervenants
            color_palette = [
                "#32a852", "#3b82f6", "#f59e0b", "#8b5cf6", "#ef4444", 
                "#06b6d4", "#84cc16", "#f97316", "#ec4899", "#6366f1"
            ]
            
            # Créer un mapping couleur pour chaque intervenant (en évitant les doublons)
            intervenant_colors = {}
            noms_uniques = list(set(intervenant.nom_prenom for intervenant in intervenants))
            for i, nom in enumerate(noms_uniques):
                intervenant_colors[nom] = color_palette[i % len(color_palette)]
            
            logger.info(f"🎨 Couleurs assignées: {len(intervenant_colors)} intervenants")
            
            # Préparer les données en format compact pour l'IA
            interventions_data = []
            for i, intervention in enumerate(interventions, 1):
                logger.debug(f"   Préparation intervention {i}/{len(interventions)}: {intervention.client}")
                data = {
                    "client": intervention.client,
                    "date": intervention.date,
                    "duree": intervention.duree,
                    "latitude": intervention.latitude,
                    "longitude": intervention.longitude,
                    "secteur": intervention.secteur
                }
                # N'ajouter l'intervenant que s'il est spécifié
                if intervention.intervenant:
                    data["intervenant_impose"] = intervention.intervenant
                # Ajouter les champs spéciaux
                if intervention.binome:
                    data["binome"] = True
                if intervention.intervenant_referent:
                    data["intervenant_referent"] = intervention.intervenant_referent
                interventions_data.append(data)
            
            intervenants_data = []
            for i, intervenant in enumerate(intervenants, 1):
                logger.debug(f"   Préparation intervenant {i}/{len(intervenants)}: {intervenant.nom_prenom}")
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

TEMPS DE TRAJET CALCULÉS (OSRM LOCAL - en minutes) - Format: "latitude,longitude" -> temps:
{json.dumps(travel_times, ensure_ascii=False)}

RÈGLES CRITIQUES:
- UTILISER les temps de trajet réels fournis ci-dessus (format latitude,longitude)
- AUCUN intervenant ne peut être à 2 endroits en même temps
- VÉRIFIER les horaires avant assignation
- Temps entre interventions = temps de trajet réel + 5 min minimum
- Si conflit: chercher autre intervenant ou marquer non_planifiable

RETOURNER {len(interventions_data)} interventions SANS DOUBLONS ni CONFLITS."""
            
            prep_duration = time.time() - prep_start
            logger.info(f"✅ Phase 2/4 terminée en {prep_duration:.2f}s")
            logger.info(f"📏 Taille du message: {len(user_message):,} caractères")
            
            # APPEL À L'IA OPENAI
            logger.info("🤖 Phase 3/4 - Appel à l'IA OpenAI")
            logger.info(f"📤 Envoi à GPT-4o-mini:")
            logger.info(f"   • {len(interventions_data)} interventions")
            logger.info(f"   • {len(intervenants_data)} intervenants") 
            logger.info(f"   • {sum(len(routes) for routes in travel_times.values())} temps de trajet")
            
            ai_start = time.time()
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
            ai_duration = time.time() - ai_start
            
            # Extraire la réponse
            planning_json = response.choices[0].message.content.strip()
            logger.info(f"✅ Phase 3/4 terminée en {ai_duration:.2f}s")
            logger.info(f"📥 Réponse reçue: {len(planning_json):,} caractères")
            
            # TRAITEMENT DE LA RÉPONSE IA
            logger.info("🔍 Phase 4/4 - Traitement de la réponse IA")
            processing_start = time.time()
            
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
                    logger.info(f"🧹 JSON nettoyé: {len(clean_json):,} caractères")
                    planning_data = json.loads(clean_json)
                else:
                    # Si pas de crochets trouvés, essayer de parser directement
                    if planning_json.strip():
                        planning_data = json.loads(planning_json)
                    else:
                        raise ValueError("Réponse OpenAI vide")
                        
            except json.JSONDecodeError as e:
                logger.error(f"❌ Erreur parsing JSON OpenAI: {str(e)}")
                logger.error(f"📋 Contenu complet reçu: {planning_json}")
                
                # Tentative de récupération en cas d'erreur
                if not planning_json.strip():
                    raise ValueError("L'IA n'a pas retourné de réponse. Réessayez avec moins d'interventions ou vérifiez votre clé OpenAI.")
                
                # Essayer de générer un planning de base en cas d'échec total
                logger.warning("🔄 Génération d'un planning de base en cas d'échec de l'IA")
                planning_data = await self.generate_fallback_planning(interventions, intervenants, travel_times)
                
            except Exception as e:
                logger.error(f"❌ Erreur inattendue lors du parsing: {str(e)}")
                logger.error(f"📋 Réponse complète: {planning_json}")
                raise ValueError(f"Impossible de traiter la réponse de l'IA: {str(e)}")
            
            # Vérifier que planning_data est une liste
            if not isinstance(planning_data, list):
                logger.error(f"❌ Format de réponse invalide: {type(planning_data)}")
                raise ValueError("L'IA n'a pas retourné une liste d'interventions valide")
            
            if not planning_data:
                logger.error("❌ Liste d'interventions vide retournée par l'IA")
                raise ValueError("L'IA n'a retourné aucune intervention planifiée")
            
            # Vérifier que toutes les interventions ont été traitées
            if len(planning_data) != len(interventions_data):
                logger.warning(f"⚠️ Nombre d'interventions différent: attendu {len(interventions_data)}, reçu {len(planning_data)}")
            
            # Convertir en objets PlanningEvent
            planning_events = []
            for i, event_data in enumerate(planning_data, 1):
                try:
                    logger.debug(f"   Traitement événement {i}/{len(planning_data)}: {event_data.get('client', 'N/A')}")
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
                    logger.error(f"❌ Erreur création PlanningEvent {i}: {str(e)}")
                    continue
            
            processing_duration = time.time() - processing_start
            logger.info(f"✅ Phase 4/4 terminée en {processing_duration:.2f}s")
            logger.info(f"📋 Planning brut généré: {len(planning_events)} événements")
            
            # VALIDATION ET CORRECTION DES CONFLITS
            logger.info("🔍 Validation finale et correction des conflits...")
            validation_start = time.time()
            validated_planning = planning_validator.validate_and_fix_planning(planning_events)
            validation_duration = time.time() - validation_start
            
            total_duration = time.time() - total_start_time
            
            logger.info(f"✅ === GÉNÉRATION PLANNING TERMINÉE ===")
            logger.info(f"📊 Résumé complet:")
            logger.info(f"   • Temps de trajet: {travel_times_duration:.2f}s")
            logger.info(f"   • Préparation IA: {prep_duration:.2f}s") 
            logger.info(f"   • Appel OpenAI: {ai_duration:.2f}s")
            logger.info(f"   • Traitement: {processing_duration:.2f}s")
            logger.info(f"   • Validation: {validation_duration:.2f}s")
            logger.info(f"   • TEMPS TOTAL: {total_duration:.2f}s")
            logger.info(f"   • Événements finaux: {len(validated_planning)}")
            
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