import React, { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CSVUpload = ({ onFilesProcessed }) => {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState({ interventions: null, intervenants: null });
  const [processing, setProcessing] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const droppedFiles = [...e.dataTransfer.files];
    processFiles(droppedFiles);
  }, []);

  const handleFileInput = (e) => {
    const selectedFiles = [...e.target.files];
    processFiles(selectedFiles);
  };

  const processFiles = (fileList) => {
    const newFiles = { ...files };
    
    fileList.forEach(file => {
      if (file.name.includes('intervention')) {
        newFiles.interventions = file;
      } else if (file.name.includes('intervenant')) {
        newFiles.intervenants = file;
      }
    });
    
    setFiles(newFiles);
    setUploadStatus({
      type: 'success',
      message: `${fileList.length} fichier(s) chargé(s) avec succès`
    });
  };

  const handleProcessFiles = async () => {
    if (!files.interventions || !files.intervenants) {
      setUploadStatus({
        type: 'error',
        message: 'Veuillez charger les deux fichiers CSV (interventions et intervenants)'
      });
      return;
    }

    setProcessing(true);
    setUploadStatus(null);

    try {
      // Créer le FormData pour l'upload
      const formData = new FormData();
      formData.append('interventions_file', files.interventions);
      formData.append('intervenants_file', files.intervenants);

      // Envoyer au backend
      const response = await axios.post(`${API}/upload-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 secondes timeout pour l'IA
      });

      const result = response.data;
      
      setUploadStatus({
        type: 'success',
        message: result.message
      });

      // Convertir les données backend au format frontend
      const frontendPlanning = result.planning.map(event => ({
        id: event.id,
        title: `${event.client} - ${event.intervenant}`,
        start: event.start,
        end: event.end,
        backgroundColor: event.color,
        borderColor: event.color,
        extendedProps: {
          client: event.client,
          intervenant: event.intervenant,
          address: event.adresse,
          duration: calculateDuration(event.start, event.end),
          nonPlanifiable: event.non_planifiable,
          trajetPrecedent: event.trajet_precedent || "0 min",
          raison: event.raison
        }
      }));

      onFilesProcessed({
        success: true,
        message: result.message,
        stats: {
          totalInterventions: result.stats.total_interventions,
          interventionsPlanifiees: result.stats.interventions_planifiees,
          interventionsNonPlanifiables: result.stats.interventions_non_planifiables,
          intervenants: result.stats.intervenants,
          tauxPlanification: result.stats.taux_planification
        },
        planning: frontendPlanning
      });

    } catch (error) {
      console.error('Erreur traitement fichiers:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'Erreur lors du traitement des fichiers';
      setUploadStatus({
        type: 'error',
        message: errorMessage
      });
    } finally {
      setProcessing(false);
    }
  };

  const calculateDuration = (start, end) => {
    const startTime = new Date(start);
    const endTime = new Date(end);
    const diffMs = endTime - startTime;
    const diffMins = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMins / 60);
    const minutes = diffMins % 60;
    return hours > 0 ? `${hours}h${minutes.toString().padStart(2, '0')}` : `${minutes}min`;
  };

  const resetFiles = () => {
    setFiles({ interventions: null, intervenants: null });
    setUploadStatus(null);
  };

  return (
    <div className="space-y-6">
      <Card className="border-2 border-dashed transition-all duration-300 hover:border-primary/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5 text-primary" />
            Import des fichiers CSV
          </CardTitle>
          <CardDescription>
            Chargez vos fichiers interventions.csv et intervenants.csv pour générer le planning optimisé par IA
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300 ${
              dragActive 
                ? 'border-primary bg-primary/5 scale-105' 
                : 'border-gray-300 hover:border-primary/50 hover:bg-gray-50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-4">
              <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                <Upload className={`h-8 w-8 text-primary transition-transform duration-300 ${dragActive ? 'scale-110' : ''}`} />
              </div>
              
              <div>
                <p className="text-lg font-medium text-gray-900">
                  Glissez-déplacez vos fichiers CSV ici
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  ou cliquez pour parcourir vos fichiers
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 max-w-md mx-auto text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>interventions.csv</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>intervenants.csv</span>
                </div>
              </div>

              <input
                type="file"
                multiple
                accept=".csv"
                onChange={handleFileInput}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>
          </div>

          {/* Fichiers chargés */}
          {(files.interventions || files.intervenants) && (
            <div className="mt-6 space-y-3">
              <h4 className="font-medium text-gray-900">Fichiers chargés :</h4>
              <div className="grid gap-2">
                {files.interventions && (
                  <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="font-medium text-green-800">{files.interventions.name}</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        {(files.interventions.size / 1024).toFixed(1)} KB
                      </Badge>
                    </div>
                  </div>
                )}
                
                {files.intervenants && (
                  <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="font-medium text-green-800">{files.intervenants.name}</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        {(files.intervenants.size / 1024).toFixed(1)} KB
                      </Badge>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Statut d'upload */}
          {uploadStatus && (
            <Alert className={`mt-4 ${uploadStatus.type === 'error' ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}>
              {uploadStatus.type === 'error' ? (
                <AlertCircle className="h-4 w-4 text-red-600" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-600" />
              )}
              <AlertDescription className={uploadStatus.type === 'error' ? 'text-red-800' : 'text-green-800'}>
                {uploadStatus.message}
              </AlertDescription>
            </Alert>
          )}

          {/* Boutons d'action */}
          <div className="flex gap-3 mt-6">
            <Button 
              onClick={handleProcessFiles}
              disabled={!files.interventions || !files.intervenants || processing}
              className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-300"
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  IA en cours de traitement...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Générer le planning IA
                </>
              )}
            </Button>
            
            {(files.interventions || files.intervenants) && (
              <Button variant="outline" onClick={resetFiles}>
                Réinitialiser
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900 text-sm">📋 Format des fichiers CSV</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-blue-800">
          <div>
            <strong>interventions.csv :</strong>
            <code className="block mt-1 p-2 bg-white rounded text-xs">
              Client,Date,Durée,Adresse,Intervenant<br/>
              Martin,29/06/2025 08:00,01:00,1 rue des Lilas Strasbourg,Dupont
            </code>
          </div>
          <div>
            <strong>intervenants.csv :</strong>
            <code className="block mt-1 p-2 bg-white rounded text-xs">
              Nom,Adresse,Disponibilités,Repos,Week-end<br/>
              Dupont,12 avenue des Vosges Strasbourg,L-M-M-J-V 07-14,2025-06-30,A
            </code>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CSVUpload;