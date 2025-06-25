import React, { useState, useEffect, useRef } from 'react';
import { Brain, Loader2, Zap, CheckCircle, AlertCircle, Activity, Database, Clock, BarChart3 } from 'lucide-react';
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
  const [detailedStep, setDetailedStep] = useState('');
  const [stepStats, setStepStats] = useState(null);
  const [generationStatus, setGenerationStatus] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const intervalRef = useRef(null);

  const canGenerate = interventionsFile && intervenantsFile;

  // Timer pour l'elapsed time
  useEffect(() => {
    if (processing && startTime) {
      intervalRef.current = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [processing, startTime]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStepIcon = (step) => {
    if (step.includes('PARSING')) return <Database className="h-4 w-4" />;
    if (step.includes('VALIDATION')) return <CheckCircle className="h-4 w-4" />;
    if (step.includes('OSRM') || step.includes('trajet')) return <Activity className="h-4 w-4" />;
    if (step.includes('IA') || step.includes('OpenAI')) return <Brain className="h-4 w-4" />;
    if (step.includes('STATISTIQUES')) return <BarChart3 className="h-4 w-4" />;
    return <Clock className="h-4 w-4" />;
  };

  const simulateProgressFromLogs = (step, substep = '') => {
    // Simuler la progression basée sur les étapes détaillées
    if (step.includes('ÉTAPE 1/5') || step.includes('PARSING')) {
      setProgress(10);
      if (substep.includes('interventions')) setProgress(15);
      if (substep.includes('intervenants')) setProgress(20);
    } else if (step.includes('ÉTAPE 2/5') || step.includes('VALIDATION')) {
      setProgress(25);
    } else if (step.includes('ÉTAPE 3/5') || step.includes('trajet') || step.includes('OSRM')) {
      setProgress(30);
      if (substep.includes('Phase 1/4')) setProgress(35);
      if (substep.includes('PARALLÈLE')) setProgress(45);
      if (substep.includes('Lot')) {
        // Extraire le numéro de lot si possible
        const lotMatch = substep.match(/Lot (\d+)\/(\d+)/);
        if (lotMatch) {
          const current = parseInt(lotMatch[1]);
          const total = parseInt(lotMatch[2]);
          const lotProgress = 45 + (current / total) * 15; // 45-60%
          setProgress(Math.min(60, lotProgress));
        }
      }
      if (substep.includes('Phase 2/4')) setProgress(62);
      if (substep.includes('Phase 3/4')) setProgress(65);
      if (substep.includes('Phase 4/4')) setProgress(75);
    } else if (step.includes('ÉTAPE 4/5') || step.includes('STATISTIQUES')) {
      setProgress(80);
    } else if (step.includes('ÉTAPE 5/5') || step.includes('FINALISATION')) {
      setProgress(90);
    }
  };

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
    setStartTime(Date.now());
    setElapsedTime(0);
    setStepStats(null);

    try {
      // Phase initiale
      setCurrentStep('📊 ÉTAPE 1/5 - PARSING CSV');
      setDetailedStep('Préparation des données...');
      setProgress(5);
      await new Promise(resolve => setTimeout(resolve, 500));

      const formData = new FormData();
      formData.append('interventions_file', interventionsFile);
      formData.append('intervenants_file', intervenantsFile);

      // Simulation des étapes détaillées pendant l'appel API
      const progressSteps = [
        { step: '📊 ÉTAPE 1/5 - PARSING CSV', detail: '📄 Lecture des fichiers...', progress: 10, delay: 800 },
        { step: '📊 ÉTAPE 1/5 - PARSING CSV', detail: '🔄 Parsing interventions.csv...', progress: 15, delay: 1200 },
        { step: '📊 ÉTAPE 1/5 - PARSING CSV', detail: '🔄 Parsing intervenants.csv...', progress: 20, delay: 800 },
        { step: '📊 ÉTAPE 2/5 - VALIDATION', detail: '✅ Validation des coordonnées GPS...', progress: 25, delay: 600 },
        { step: '📊 ÉTAPE 3/5 - GÉNÉRATION PLANNING IA', detail: '📍 Phase 1/4 - Collecte des coordonnées...', progress: 30, delay: 1000 },
        { step: '📊 ÉTAPE 3/5 - GÉNÉRATION PLANNING IA', detail: '🚀 OSRM LOCAL PARALLÈLE - Calculs ultra-rapides...', progress: 40, delay: 2000 },
        { step: '📊 ÉTAPE 3/5 - GÉNÉRATION PLANNING IA', detail: '⚡ Calculs parallèles en cours (20 simultanés)...', progress: 50, delay: 1500 },
        { step: '📊 ÉTAPE 3/5 - GÉNÉRATION PLANNING IA', detail: '🔧 Phase 2/4 - Préparation des données IA...', progress: 62, delay: 800 },
        { step: '📊 ÉTAPE 3/5 - GÉNÉRATION PLANNING IA', detail: '🤖 Phase 3/4 - Appel OpenAI GPT-4o-mini...', progress: 65, delay: 3000 },
        { step: '📊 ÉTAPE 3/5 - GÉNÉRATION PLANNING IA', detail: '🔍 Phase 4/4 - Traitement de la réponse IA...', progress: 75, delay: 1000 },
        { step: '📊 ÉTAPE 4/5 - CALCUL STATISTIQUES', detail: '📈 Calcul des métriques de performance...', progress: 80, delay: 500 },
        { step: '📊 ÉTAPE 5/5 - FINALISATION', detail: '🎉 Finalisation du planning...', progress: 90, delay: 800 }
      ];

      // Lancer les étapes de simulation en parallèle avec l'appel API
      const simulateProgress = async () => {
        for (const { step, detail, progress, delay } of progressSteps) {
          setCurrentStep(step);
          setDetailedStep(detail);
          setProgress(progress);
          
          // Ajouter des statistiques simulées pour certaines étapes
          if (detail.includes('OSRM')) {
            setStepStats({
              trajets: '~420 trajets théoriques',
              vitesse: '40+ trajets/seconde',
              mode: 'Parallèle (20 simultanés)'
            });
          } else if (detail.includes('OpenAI')) {
            setStepStats({
              modele: 'GPT-4o-mini',
              taille: '~3,500 caractères',
              temperature: '0.05 (optimisé)'
            });
          } else {
            setStepStats(null);
          }
          
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      };

      // Lancer simulation et appel API en parallèle
      const [_, response] = await Promise.all([
        simulateProgress(),
        axios.post(`${API}/upload-csv`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes timeout
        })
      ]);

      const result = response.data;

      // Finalisation
      setProgress(100);
      setCurrentStep('✅ SUCCÈS COMPLET');
      setDetailedStep('Planning généré avec succès !');
      setStepStats({
        temps_total: `${elapsedTime}s`,
        interventions: result.stats.interventions_planifiees,
        taux: `${result.stats.taux_planification}%`
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
      setCurrentStep('❌ ERREUR');
      setDetailedStep('');
      setStepStats(null);
    } finally {
      setProcessing(false);
      if (!generationStatus || generationStatus.type !== 'success') {
        setTimeout(() => {
          setProgress(0);
          setCurrentStep('');
          setDetailedStep('');
          setStepStats(null);
        }, 5000);
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