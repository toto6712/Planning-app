from typing import List, Dict, Set
from datetime import datetime, timedelta
import logging
from models import PlanningEvent

logger = logging.getLogger(__name__)

class PlanningValidator:
    """Valide et corrige les conflits dans un planning"""
    
    def __init__(self):
        self.color_palette = [
            "#32a852", "#3b82f6", "#f59e0b", "#8b5cf6", "#ef4444", 
            "#06b6d4", "#84cc16", "#f97316", "#ec4899", "#6366f1"
        ]
    
    def validate_and_fix_planning(self, planning_events: List[PlanningEvent]) -> List[PlanningEvent]:
        """Valide le planning et corrige les conflits d'horaires"""
        try:
            logger.info(f"Validation du planning avec {len(planning_events)} événements")
            
            # Étape 1: Supprimer les doublons exacts
            unique_events = self.remove_duplicates(planning_events)
            logger.info(f"Après suppression doublons: {len(unique_events)} événements")
            
            # Étape 2: Détecter et résoudre les conflits d'horaires
            validated_events = self.resolve_scheduling_conflicts(unique_events)
            logger.info(f"Après résolution conflits: {len(validated_events)} événements")
            
            # Étape 3: Vérifier et corriger les couleurs
            final_events = self.fix_intervenant_colors(validated_events)
            logger.info(f"Planning final validé: {len(final_events)} événements")
            
            # Étape 4: Logs de diagnostic
            self.log_planning_summary(final_events)
            
            return final_events
            
        except Exception as e:
            logger.error(f"Erreur validation planning: {str(e)}")
            return planning_events  # Retourner le planning original en cas d'erreur
    
    def remove_duplicates(self, events: List[PlanningEvent]) -> List[PlanningEvent]:
        """Supprime les doublons exacts"""
        seen_clients = set()
        unique_events = []
        
        for event in events:
            # Critères de doublon: même client + même horaire de début
            key = f"{event.client}_{event.start}"
            if key not in seen_clients:
                seen_clients.add(key)
                unique_events.append(event)
            else:
                logger.warning(f"Doublon supprimé: {event.client} à {event.start}")
        
        return unique_events
    
    def resolve_scheduling_conflicts(self, events: List[PlanningEvent]) -> List[PlanningEvent]:
        """Résout les conflits d'horaires pour chaque intervenant"""
        # Grouper par intervenant
        by_intervenant = {}
        for event in events:
            if event.intervenant not in by_intervenant:
                by_intervenant[event.intervenant] = []
            by_intervenant[event.intervenant].append(event)
        
        validated_events = []
        
        for intervenant, intervenant_events in by_intervenant.items():
            if intervenant == "Non assigné" or not intervenant:
                # Pas de validation pour les non assignés
                validated_events.extend(intervenant_events)
                continue
            
            # Trier par heure de début
            sorted_events = sorted(intervenant_events, key=lambda x: x.start)
            
            # Valider et ajuster les horaires
            conflict_free_events = self.fix_intervenant_schedule(intervenant, sorted_events)
            validated_events.extend(conflict_free_events)
        
        return validated_events
    
    def fix_intervenant_schedule(self, intervenant: str, events: List[PlanningEvent]) -> List[PlanningEvent]:
        """Corrige les conflits d'horaires pour un intervenant spécifique"""
        if not events:
            return []
        
        validated = [events[0]]  # Premier événement toujours valide
        
        for i in range(1, len(events)):
            current = events[i]
            previous = validated[-1]
            
            # Convertir en datetime pour comparaison
            try:
                prev_end = datetime.fromisoformat(previous.end.replace('Z', ''))
                curr_start = datetime.fromisoformat(current.start.replace('Z', ''))
                curr_end = datetime.fromisoformat(current.end.replace('Z', ''))
                
                # Vérifier le conflit
                if curr_start < prev_end:
                    logger.warning(f"Conflit détecté pour {intervenant}: {previous.client} se termine à {previous.end}, {current.client} commence à {current.start}")
                    
                    # Ajuster l'horaire de début (15 min après la fin de la précédente)
                    new_start = prev_end + timedelta(minutes=15)
                    duration = curr_end - curr_start
                    new_end = new_start + duration
                    
                    # Vérifier que c'est dans les heures de travail (07h-22h)
                    if new_end.hour >= 22:
                        # Marquer comme non planifiable si dépasse 22h
                        logger.warning(f"Intervention {current.client} marquée non planifiable: dépasserait 22h")
                        current.non_planifiable = True
                        current.color = "#ff6b6b"
                    else:
                        # Ajuster les horaires
                        current.start = new_start.isoformat()
                        current.end = new_end.isoformat()
                        current.trajet_precedent = "15 min"
                        logger.info(f"Horaire ajusté pour {current.client}: {current.start} - {current.end}")
                
                validated.append(current)
                
            except Exception as e:
                logger.error(f"Erreur traitement horaires pour {intervenant}: {str(e)}")
                # Garder l'événement original en cas d'erreur
                validated.append(current)
        
        return validated
    
    def fix_intervenant_colors(self, events: List[PlanningEvent]) -> List[PlanningEvent]:
        """Assure une couleur unique par intervenant"""
        intervenant_colors = {}
        color_index = 0
        
        for event in events:
            if event.non_planifiable:
                event.color = "#ff6b6b"  # Rouge pour non planifiable
            elif event.intervenant not in intervenant_colors:
                intervenant_colors[event.intervenant] = self.color_palette[color_index % len(self.color_palette)]
                color_index += 1
            
            if not event.non_planifiable:
                event.color = intervenant_colors[event.intervenant]
        
        logger.info(f"Couleurs assignées: {intervenant_colors}")
        return events
    
    def log_planning_summary(self, events: List[PlanningEvent]) -> None:
        """Log un résumé du planning pour diagnostic"""
        try:
            by_intervenant = {}
            non_planifiable_count = 0
            
            for event in events:
                if event.non_planifiable:
                    non_planifiable_count += 1
                else:
                    if event.intervenant not in by_intervenant:
                        by_intervenant[event.intervenant] = 0
                    by_intervenant[event.intervenant] += 1
            
            logger.info("=== RÉSUMÉ DU PLANNING ===")
            logger.info(f"Total interventions: {len(events)}")
            logger.info(f"Interventions planifiées: {len(events) - non_planifiable_count}")
            logger.info(f"Interventions non planifiables: {non_planifiable_count}")
            
            for intervenant, count in by_intervenant.items():
                logger.info(f"  - {intervenant}: {count} interventions")
            
            logger.info("=========================")
            
        except Exception as e:
            logger.error(f"Erreur génération résumé: {str(e)}")

# Instance globale du validateur
planning_validator = PlanningValidator()