import openai
import json
import logging
import os
from typing import List, Dict, Any
from ..models import Intervention, Intervenant, PlanningEvent

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Charger le prompt depuis le fichier
        with open('ia_prompt.txt', 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()
    
    async def generate_planning(self, interventions: List[Intervention], intervenants: List[Intervenant]) -> List[PlanningEvent]:
        """Génère un planning optimisé via OpenAI"""
        try:
            # Préparer les données pour l'IA
            interventions_data = [
                {
                    "client": i.client,
                    "date": i.date,
                    "duree": i.duree,
                    "adresse": i.adresse,
                    "intervenant_impose": i.intervenant
                }
                for i in interventions
            ]
            
            intervenants_data = [
                {
                    "nom": i.nom,
                    "adresse": i.adresse,
                    "disponibilites": i.disponibilites,
                    "repos": i.repos,
                    "weekend": i.weekend
                }
                for i in intervenants
            ]
            
            # Construire le message utilisateur
            user_message = f"""
Voici les données à traiter :

INTERVENTIONS :
{json.dumps(interventions_data, ensure_ascii=False, indent=2)}

INTERVENANTS :
{json.dumps(intervenants_data, ensure_ascii=False, indent=2)}

Génère le planning optimisé en respectant toutes les contraintes.
"""
            
            logger.info("Envoi de la requête à OpenAI...")
            
            # Appel à l'API OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # Faible température pour plus de cohérence
                max_tokens=4000
            )
            
            # Extraire la réponse
            planning_json = response.choices[0].message.content.strip()
            logger.info(f"Réponse OpenAI reçue: {len(planning_json)} caractères")
            
            # Parser le JSON
            try:
                planning_data = json.loads(planning_json)
            except json.JSONDecodeError as e:
                logger.error(f"Erreur parsing JSON OpenAI: {str(e)}")
                logger.error(f"Contenu reçu: {planning_json}")
                raise ValueError(f"Réponse OpenAI invalide: {str(e)}")
            
            # Convertir en objets PlanningEvent
            planning_events = []
            for event_data in planning_data:
                try:
                    event = PlanningEvent(
                        client=event_data.get('client', ''),
                        intervenant=event_data.get('intervenant', ''),
                        start=event_data.get('start', ''),
                        end=event_data.get('end', ''),
                        color=event_data.get('color', '#64748b'),
                        non_planifiable=event_data.get('non_planifiable', False),
                        trajet_precedent=event_data.get('trajet_precedent', '0 min'),
                        adresse=event_data.get('adresse', ''),
                        raison=event_data.get('raison', None)
                    )
                    planning_events.append(event)
                except Exception as e:
                    logger.error(f"Erreur création PlanningEvent: {str(e)}")
                    continue
            
            logger.info(f"Planning généré avec {len(planning_events)} événements")
            return planning_events
            
        except openai.APIError as e:
            logger.error(f"Erreur API OpenAI: {str(e)}")
            raise ValueError(f"Erreur OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur génération planning: {str(e)}")
            raise ValueError(f"Erreur interne: {str(e)}")
    
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