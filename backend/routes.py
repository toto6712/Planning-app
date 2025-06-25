from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import List
import io
import os
import logging
from datetime import datetime

from .models import (
    PlanningResponse, FileUploadResponse, ExportResponse,
    PlanningStats, PlanningEvent
)
from .utils.csv_parser import parse_interventions_csv, parse_intervenants_csv, validate_csv_data
from .utils.openai_client import openai_client
from .utils.export_service import export_service
from .utils.travel_cache_service import travel_cache_service

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
        
        logger.info(f"📊 ÉTAPE 1/5 - PARSING CSV")
        logger.info(f"📄 Traitement de {interventions_file.filename} ({len(interventions_content)} bytes)")
        logger.info(f"📄 Traitement de {intervenants_file.filename} ({len(intervenants_content)} bytes)")
        
        # Parser les CSV
        try:
            logger.info("🔄 Parsing interventions.csv en cours...")
            interventions = parse_interventions_csv(interventions_content)
            logger.info(f"✅ Interventions parsées: {len(interventions)} lignes valides")
            
            logger.info("🔄 Parsing intervenants.csv en cours...")
            intervenants = parse_intervenants_csv(intervenants_content)
            logger.info(f"✅ Intervenants parsés: {len(intervenants)} lignes valides")
        except ValueError as e:
            raise HTTPException(400, f"Erreur parsing CSV: {str(e)}")
        
        logger.info(f"📊 ÉTAPE 2/5 - VALIDATION DES DONNÉES")
        # Valider les données
        is_valid, validation_message = validate_csv_data(interventions, intervenants)
        if not is_valid:
            raise HTTPException(400, f"Données invalides: {validation_message}")
        
        logger.info(f"✅ Validation réussie: {len(interventions)} interventions, {len(intervenants)} intervenants")
        
        logger.info(f"📊 ÉTAPE 3/5 - GÉNÉRATION PLANNING IA")
        
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

@router.get("/travel-cache/stats")
async def get_travel_cache_stats():
    """Récupère les statistiques du cache des trajets"""
    try:
        stats = travel_cache_service.get_cache_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Erreur récupération stats cache: {str(e)}")
        raise HTTPException(500, f"Erreur stats cache: {str(e)}")

@router.post("/travel-cache/import")
async def import_travel_times(file: UploadFile = File(...)):
    """Importe des temps de trajet depuis un fichier CSV"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(400, "Le fichier doit être au format CSV")
        
        # Sauvegarder le fichier temporairement
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Importer les trajets
        imported_count = travel_cache_service.import_travel_times_from_csv(temp_path)
        
        # Sauvegarder le cache
        travel_cache_service.save_cache()
        
        # Nettoyer le fichier temporaire
        os.unlink(temp_path)
        
        return {
            "success": True,
            "message": f"Importé {imported_count} trajets avec succès",
            "imported_count": imported_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur import trajets: {str(e)}")
        raise HTTPException(500, f"Erreur import: {str(e)}")

@router.post("/travel-cache/clear")
async def clear_travel_cache():
    """Vide complètement le cache des trajets"""
    try:
        travel_cache_service.clear_cache()
        return {
            "success": True,
            "message": "Cache des trajets vidé avec succès"
        }
    except Exception as e:
        logger.error(f"Erreur vidage cache: {str(e)}")
        raise HTTPException(500, f"Erreur vidage cache: {str(e)}")

@router.get("/travel-cache/download-template/{filename}")
async def download_missing_routes_template(filename: str):
    """Télécharge le template des trajets manquants"""
    try:
        file_path = f"/app/data/{filename}"
        if not os.path.exists(file_path):
            raise HTTPException(404, "Fichier template non trouvé")
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur téléchargement template: {str(e)}")
        raise HTTPException(500, f"Erreur téléchargement: {str(e)}")