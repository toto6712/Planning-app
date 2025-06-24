from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Intervention(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client: str
    date: str  # Format: "29/06/2025 08:00"
    duree: str  # Format: "01:00"
    adresse: str
    intervenant: Optional[str] = ""  # Peut être vide si non imposé
    
class Intervenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    adresse: str
    disponibilites: str  # Format: "L-M-M-J-V 07-14"
    repos: Optional[str] = ""  # Format: "2025-06-30"
    weekend: str  # "A" ou "B"

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