from fpdf import FPDF
import csv
import io
import json
from typing import List
from ..models import PlanningEvent, PlanningStats
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ExportService:
    
    def generate_csv(self, planning_events: List[PlanningEvent]) -> str:
        """Génère un CSV du planning"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            headers = [
                'Date', 'Heure_debut', 'Heure_fin', 'Client', 
                'Intervenant', 'Adresse', 'Duree', 'Trajet_precedent',
                'Non_planifiable', 'Raison', 'Couleur'
            ]
            writer.writerow(headers)
            
            # Données
            for event in planning_events:
                try:
                    # Extraire date et heures
                    start_dt = datetime.fromisoformat(event.start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(event.end.replace('Z', '+00:00'))
                    
                    # Calculer la durée
                    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                    duration_str = f"{duration_minutes // 60}h{duration_minutes % 60:02d}" if duration_minutes >= 60 else f"{duration_minutes}min"
                    
                    row = [
                        start_dt.strftime('%Y-%m-%d'),
                        start_dt.strftime('%H:%M'),
                        end_dt.strftime('%H:%M'),
                        event.client,
                        event.intervenant,
                        event.adresse,
                        duration_str,
                        event.trajet_precedent or '0 min',
                        'Oui' if event.non_planifiable else 'Non',
                        event.raison or '',
                        event.color
                    ]
                    writer.writerow(row)
                except Exception as e:
                    logger.error(f"Erreur traitement événement CSV: {str(e)}")
                    continue
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"CSV généré avec {len(planning_events)} lignes")
            return csv_content
            
        except Exception as e:
            logger.error(f"Erreur génération CSV: {str(e)}")
            raise ValueError(f"Erreur génération CSV: {str(e)}")
    
    def generate_pdf(self, planning_events: List[PlanningEvent], stats: PlanningStats) -> bytes:
        """Génère un PDF du planning"""
        try:
            # Créer le PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Titre
            pdf.cell(0, 10, 'Planning des Tournees - Optimise par IA', 0, 1, 'C')
            pdf.ln(10)
            
            # Statistiques
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Statistiques du Planning', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            stats_lines = [
                f"Total interventions: {stats.total_interventions}",
                f"Interventions planifiees: {stats.interventions_planifiees}",
                f"Interventions non planifiables: {stats.interventions_non_planifiables}",
                f"Nombre d'intervenants: {stats.intervenants}",
                f"Taux de planification: {stats.taux_planification}%"
            ]
            
            for line in stats_lines:
                pdf.cell(0, 6, line, 0, 1)
            
            pdf.ln(10)
            
            # Planning détaillé
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Detail du Planning', 0, 1)
            
            # En-têtes tableau
            pdf.set_font('Arial', 'B', 8)
            col_widths = [25, 20, 20, 30, 30, 40, 25]
            headers = ['Date', 'Debut', 'Fin', 'Client', 'Intervenant', 'Adresse', 'Statut']
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
            pdf.ln()
            
            # Données
            pdf.set_font('Arial', '', 7)
            for event in planning_events:
                try:
                    start_dt = datetime.fromisoformat(event.start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(event.end.replace('Z', '+00:00'))
                    
                    # Limiter la longueur du texte
                    client = event.client[:15] + '...' if len(event.client) > 15 else event.client
                    intervenant = event.intervenant[:15] + '...' if len(event.intervenant) > 15 else event.intervenant
                    adresse = event.adresse[:30] + '...' if len(event.adresse) > 30 else event.adresse
                    statut = 'NON PLAN.' if event.non_planifiable else 'OK'
                    
                    row_data = [
                        start_dt.strftime('%d/%m/%Y'),
                        start_dt.strftime('%H:%M'),
                        end_dt.strftime('%H:%M'),
                        client,
                        intervenant,
                        adresse,
                        statut
                    ]
                    
                    for i, data in enumerate(row_data):
                        pdf.cell(col_widths[i], 6, str(data), 1, 0, 'L')
                    pdf.ln()
                    
                except Exception as e:
                    logger.error(f"Erreur traitement événement PDF: {str(e)}")
                    continue
            
            # Pied de page
            pdf.ln(10)
            pdf.set_font('Arial', 'I', 8)
            pdf.cell(0, 10, f'Genere le {datetime.now().strftime("%d/%m/%Y a %H:%M")} par Planning Tournees IA', 0, 1, 'C')
            
            # Retourner le PDF en bytes
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            logger.info(f"PDF généré avec {len(planning_events)} événements")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Erreur génération PDF: {str(e)}")
            raise ValueError(f"Erreur génération PDF: {str(e)}")

# Instance globale du service d'export
export_service = ExportService()