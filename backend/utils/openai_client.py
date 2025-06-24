import openai
import json
import logging
import os
from typing import List, Dict, Any
from ..models import Intervention, Intervenant, PlanningEvent
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
    
    async def generate_planning(self, interventions: List[Intervention], intervenants: List[Intervenant]) -> List[PlanningEvent]:
        """Génère un planning optimisé via OpenAI"""
        try:
            # Préparer les données en format compact pour l'IA
            interventions_data = []
            for i in interventions:
                data = {
                    "client": i.client,
                    "date": i.date,
                    "duree": i.duree,
                    "adresse": i.adresse
                }
                # N'ajouter l'intervenant que s'il est spécifié
                if i.intervenant:
                    data["intervenant_impose"] = i.intervenant
                interventions_data.append(data)
            
            intervenants_data = []
            for i in intervenants:
                data = {
                    "nom": i.nom,
                    "adresse": i.adresse,
                    "disponibilites": i.disponibilites,
                    "weekend": i.weekend
                }
                # N'ajouter le repos que s'il existe
                if i.repos:
                    data["repos"] = i.repos
                intervenants_data.append(data)
            
            # Construire un message utilisateur compact
            user_message = f"""INTERVENTIONS:
{json.dumps(interventions_data, ensure_ascii=False)}

INTERVENANTS:
{json.dumps(intervenants_data, ensure_ascii=False)}"""
            
            logger.info("Envoi de la requête à OpenAI...")
            logger.info(f"Taille du message: ~{len(user_message)} caractères")
            
            # Utiliser GPT-4o-mini qui a des limites plus élevées et coûte moins cher
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Changement de modèle
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Très faible pour cohérence
                max_tokens=3000   # Limiter la réponse
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
                # Essayer de nettoyer la réponse si elle contient du texte en plus
                if "```json" in planning_json:
                    # Extraire le JSON entre les balises
                    start = planning_json.find("[")
                    end = planning_json.rfind("]") + 1
                    if start >= 0 and end > start:
                        clean_json = planning_json[start:end]
                        planning_data = json.loads(clean_json)
                    else:
                        raise ValueError(f"Impossible d'extraire le JSON: {str(e)}")
                else:
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
            if "rate_limit_exceeded" in str(e):
                raise ValueError("Limite de tokens OpenAI dépassée. Réessayez dans 1 minute ou contactez votre administrateur pour augmenter les limites.")
            else:
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