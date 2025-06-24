from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import List
import io
import logging
from datetime import datetime

from models import (
    PlanningResponse, FileUploadResponse, ExportResponse,
    PlanningStats, PlanningEvent
)
from utils.csv_parser import parse_interventions_csv, parse_intervenants_csv, validate_csv_data
from utils.openai_client import openai_client
from utils.export_service import export_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.post("/upload-csv", response_model=PlanningResponse)
async def upload_and_process_csv(
    interventions_file: UploadFile = File(...),
    intervenants_file: UploadFile = File(...)
):
    """Upload et traitement des fichiers CSV avec génération de planning par IA"""
    try:
        logger.info(f"Réception fichiers: {interventions_file.filename}, {intervenants_file.filename}")
        
        # Vérifier les extensions
        if not interventions_file.filename.endswith('.csv'):
            raise HTTPException(400, "Le fichier interventions doit être au format CSV")
        if not intervenants_file.filename.endswith('.csv'):
            raise HTTPException(400, "Le fichier intervenants doit être au format CSV")
        
        # Lire les fichiers
        interventions_content = await interventions_file.read()
        intervenants_content = await intervenants_file.read()
        
        # Parser les CSV
        try:
            interventions = parse_interventions_csv(interventions_content)
            intervenants = parse_intervenants_csv(intervenants_content)
        except ValueError as e:
            raise HTTPException(400, f"Erreur parsing CSV: {str(e)}")
        
        # Valider les données
        is_valid, validation_message = validate_csv_data(interventions, intervenants)
        if not is_valid:
            raise HTTPException(400, f"Données invalides: {validation_message}")
        
        logger.info(f"Données validées: {len(interventions)} interventions, {len(intervenants)} intervenants")
        
        # Générer le planning avec OpenAI
        try:
            planning_events = await openai_client.generate_planning(interventions, intervenants)
        except ValueError as e:
            raise HTTPException(500, f"Erreur génération planning IA: {str(e)}")
        
        # Calculer les statistiques
        stats_data = openai_client.calculate_stats(
            planning_events, 
            len(interventions), 
            len(intervenants)
        )
        stats = PlanningStats(**stats_data)
        
        logger.info(f"Planning généré avec succès: {len(planning_events)} événements")
        
        return PlanningResponse(
            success=True,
            message=f"Planning généré avec succès par l'IA ! {stats.interventions_planifiees}/{stats.total_interventions} interventions planifiées",
            planning=planning_events,
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur traitement CSV: {str(e)}")
        raise HTTPException(500, f"Erreur interne: {str(e)}")

@router.post("/export-csv")
async def export_planning_csv(planning_data: List[PlanningEvent]):
    """Export du planning en format CSV"""
    try:
        if not planning_data:
            raise HTTPException(400, "Aucune donnée de planning à exporter")
        
        csv_content = export_service.generate_csv(planning_data)
        
        # Créer la réponse avec le fichier CSV
        csv_bytes = csv_content.encode('utf-8')
        filename = f"planning_tournees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erreur export CSV: {str(e)}")
        raise HTTPException(500, f"Erreur export CSV: {str(e)}")

@router.post("/export-pdf")
async def export_planning_pdf(request_data: dict):
    """Export du planning en format PDF"""
    try:
        planning_data = request_data.get('planning', [])
        stats_data = request_data.get('stats', {})
        
        if not planning_data:
            raise HTTPException(400, "Aucune donnée de planning à exporter")
        
        # Convertir les données
        planning_events = [PlanningEvent(**event) for event in planning_data]
        stats = PlanningStats(**stats_data)
        
        pdf_bytes = export_service.generate_pdf(planning_events, stats)
        
        filename = f"planning_tournees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erreur export PDF: {str(e)}")
        raise HTTPException(500, f"Erreur export PDF: {str(e)}")

@router.get("/health")
async def health_check():
    """Vérification de l'état du service"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "planning-tournees-api"
    }