import React, { useState } from 'react';
import { Brain, Loader2, Zap, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PlanningGenerator = ({ interventionsFile, intervenantsFile, onPlanningGenerated }) => {
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [generationStatus, setGenerationStatus] = useState(null);

  const canGenerate = interventionsFile && intervenantsFile;

  const handleGeneratePlanning = async () => {
    if (!canGenerate) {
      setGenerationStatus({
        type: 'error',
        message: 'Veuillez charger les deux fichiers CSV avant de générer le planning'
      });
      return;
    }

    setProcessing(true);
    setProgress(0);
    setGenerationStatus(null);

    try {
      // Étape 1: Validation des fichiers
      setCurrentStep('Validation des fichiers CSV...');
      setProgress(20);
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Étape 2: Upload et parsing
      setCurrentStep('Upload et analyse des données...');
      setProgress(40);

      const formData = new FormData();
      formData.append('interventions_file', interventionsFile);
      formData.append('intervenants_file', intervenantsFile);

      // Étape 3: Traitement IA
      setCurrentStep('IA en cours d\'optimisation...');
      setProgress(60);

      const response = await axios.post(`${API}/upload-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes timeout pour l'IA
      });

      // Étape 4: Finalisation
      setCurrentStep('Finalisation du planning...');
      setProgress(80);
      await new Promise(resolve => setTimeout(resolve, 800));

      const result = response.data;

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

      setProgress(100);
      setCurrentStep('Planning généré avec succès !');

      setGenerationStatus({
        type: 'success',
        message: result.message
      });

      onPlanningGenerated({
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
      console.error('Erreur génération planning:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'Erreur lors de la génération du planning';
      setGenerationStatus({
        type: 'error',
        message: errorMessage
      });
      setProgress(0);
      setCurrentStep('');
    } finally {
      setProcessing(false);
      if (!generationStatus || generationStatus.type !== 'success') {
        setTimeout(() => {
          setProgress(0);
          setCurrentStep('');
        }, 3000);
      }
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

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-purple-900">
          <Brain className="h-6 w-6 text-purple-600" />
          Génération du Planning par IA
        </CardTitle>
        <CardDescription className="text-purple-700">
          L'intelligence artificielle va optimiser automatiquement vos tournées selon toutes les contraintes métier
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* État des fichiers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={`p-4 rounded-lg border-2 transition-all duration-300 ${
            interventionsFile 
              ? 'bg-blue-100 border-blue-300 text-blue-900' 
              : 'bg-gray-100 border-gray-300 text-gray-600'
          }`}>
            <div className="flex items-center gap-2">
              {interventionsFile ? (
                <CheckCircle className="h-5 w-5 text-blue-600" />
              ) : (
                <div className="h-5 w-5 border-2 border-gray-400 rounded-full" />
              )}
              <span className="font-medium">Interventions</span>
            </div>
            <p className="text-sm mt-1">
              {interventionsFile ? interventionsFile.name : 'Fichier non chargé'}
            </p>
          </div>

          <div className={`p-4 rounded-lg border-2 transition-all duration-300 ${
            intervenantsFile 
              ? 'bg-green-100 border-green-300 text-green-900' 
              : 'bg-gray-100 border-gray-300 text-gray-600'
          }`}>
            <div className="flex items-center gap-2">
              {intervenantsFile ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <div className="h-5 w-5 border-2 border-gray-400 rounded-full" />
              )}
              <span className="font-medium">Intervenants</span>
            </div>
            <p className="text-sm mt-1">
              {intervenantsFile ? intervenantsFile.name : 'Fichier non chargé'}
            </p>
          </div>
        </div>

        {/* Progression */}
        {processing && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-purple-900">{currentStep}</span>
              <span className="text-sm text-purple-700">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        )}

        {/* Statut de génération */}
        {generationStatus && (
          <Alert className={`${
            generationStatus.type === 'error' 
              ? 'border-red-200 bg-red-50' 
              : 'border-green-200 bg-green-50'
          }`}>
            {generationStatus.type === 'error' ? (
              <AlertCircle className="h-4 w-4 text-red-600" />
            ) : (
              <CheckCircle className="h-4 w-4 text-green-600" />
            )}
            <AlertDescription className={
              generationStatus.type === 'error' ? 'text-red-800' : 'text-green-800'
            }>
              {generationStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Bouton de génération */}
        <div className="text-center">
          <Button 
            onClick={handleGeneratePlanning}
            disabled={!canGenerate || processing}
            size="lg"
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-3 transition-all duration-300 transform hover:scale-105 disabled:transform-none disabled:opacity-50"
          >
            {processing ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                IA en cours de traitement...
              </>
            ) : (
              <>
                <Zap className="h-5 w-5 mr-2" />
                Générer le Planning Optimisé
              </>
            )}
          </Button>
        </div>

        {/* Informations sur l'IA */}
        <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-purple-200">
          <h4 className="font-medium text-purple-900 mb-3 flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Optimisations automatiques par IA
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs text-purple-800">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Respect horaires 07h-22h</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Gestion repos obligatoires</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Optimisation trajets</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Week-ends alternés</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Équilibrage charges</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Géocodage automatique</span>
            </div>
          </div>
        </div>

        {!canGenerate && (
          <div className="text-center py-4 text-gray-500">
            <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Chargez les deux fichiers CSV pour activer la génération IA</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PlanningGenerator;