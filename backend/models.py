from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Intervention(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client: str
    date: str  # Format: "29/06/2025 08:00"
    duree: str  # Format: "01:00"
    latitude: float
    longitude: float
    intervenant: Optional[str] = ""  # Peut être vide si non imposé
    binome: bool = False  # Si intervention nécessite 2 intervenants
    intervenant_referent: Optional[str] = ""  # Intervenant préféré pour ce client
    secteur: Optional[str] = ""  # Ville/secteur (peut être détecté depuis les coordonnées)
    
class Intervenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom_prenom: str
    latitude: float
    longitude: float
    heure_mensuel: str  # Format: "151h" ou "169h"
    heure_hebdomaire: str  # Format: "35h" ou "39h"
    plage_horaire_autorisee: Optional[str] = ""  # Format: "09h00-18h00" ou vide
    specialites: List[str] = []  # ["volant", "14h-22h_only"] pour cas spéciaux
    roulement_weekend: Optional[str] = ""  # "A", "B" ou "exempt"

class PlanningEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client: str
    intervenant: str
    start: str  # Format ISO: "2025-06-29T08:00"
    end: str    # Format ISO: "2025-06-29T09:00"
    color: str
    non_planifiable: bool = False
    trajet_precedent: Optional[str] = "0 min"
    adresse: str
    raison: Optional[str] = None  # Si non planifiable

class PlanningStats(BaseModel):
    total_interventions: int
    interventions_planifiees: int
    interventions_non_planifiables: int
    intervenants: int
    taux_planification: float

class PlanningResponse(BaseModel):
    success: bool
    message: str
    planning: List[PlanningEvent]
    stats: PlanningStats

class FileUploadResponse(BaseModel):
    success: bool
    message: str
    interventions_count: int
    intervenants_count: int

class ExportResponse(BaseModel):
    success: bool
    message: str
    filename: str
    download_url: Optional[str] = None