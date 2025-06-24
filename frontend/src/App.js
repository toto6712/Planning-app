import React, { useState, useEffect } from "react";
import "./App.css";
import { Toaster } from "./components/ui/toaster";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { CalendarDays, Brain, Upload, Download, FileText, UserCheck, RotateCcw } from "lucide-react";
import InterventionsUpload from "./components/InterventionsUpload";
import IntervenantsUpload from "./components/IntervenantsUpload";
import PlanningGenerator from "./components/PlanningGenerator";
import CalendarView from "./components/CalendarView";
import ExportButtons from "./components/ExportButtons";
import AvsLogo from "./components/AvsLogo";

function App() {
  const [interventionsFile, setInterventionsFile] = useState(null);
  const [intervenantsFile, setIntervenantsFile] = useState(null);
  const [planningData, setPlanningData] = useState(null);
  const [stats, setStats] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);

  const handleFileUploaded = (type, file) => {
    if (type === 'interventions') {
      setInterventionsFile(file);
    } else if (type === 'intervenants') {
      setIntervenantsFile(file);
    }
  };

  const handlePlanningGenerated = (result) => {
    setPlanningData(result.planning);
    setStats(result.stats);
    setCurrentStep(3);
  };

  const handleReset = () => {
    setInterventionsFile(null);
    setIntervenantsFile(null);
    setPlanningData(null);
    setStats(null);
    setCurrentStep(1);
  };

  const steps = [
    { 
      id: 1, 
      title: "Upload CSV", 
      icon: Upload, 
      description: "Chargez vos fichiers interventions et intervenants" 
    },
    { 
      id: 2, 
      title: "Planning IA", 
      icon: Brain, 
      description: "Générez le planning optimisé automatiquement" 
    },
    { 
      id: 3, 
      title: "Visualisation", 
      icon: CalendarDays, 
      description: "Visualisez et exportez votre planning" 
    }
  ];

  useEffect(() => {
    if (interventionsFile && intervenantsFile && currentStep === 1) {
      setCurrentStep(2);
    }
  }, [interventionsFile, intervenantsFile, currentStep]);

  useEffect(() => {
    if (planningData && planningData.length > 0) {
      setCurrentStep(3);
    }
  }, [planningData]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-green-50">
      <Toaster />
      
      {/* Header AVS Autonomie */}
      <header className="bg-white/95 backdrop-blur-md border-b border-avs-blue/20 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <AvsLogo className="h-12" />
            </div>
            <div className="flex items-center gap-3">
              {(interventionsFile || intervenantsFile || planningData) && (
                <Button
                  onClick={handleReset}
                  className="flex items-center gap-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-4 py-2 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                >
                  <RotateCcw className="h-4 w-4" />
                  RESET COMPLET
                </Button>
              )}
              <Badge variant="secondary" className="bg-avs-green/10 text-avs-green border-avs-green/20 px-3 py-1">
                <div className="w-2 h-2 bg-avs-green rounded-full mr-2 animate-pulse"></div>
                IA ACTIVÉE
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Card className="mb-8 bg-white/90 backdrop-blur-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => {
                const Icon = step.icon;
                const isActive = currentStep >= step.id;
                const isCurrent = currentStep === step.id;
                
                return (
                  <div key={step.id} className="flex items-center">
                    <div className={`flex items-center gap-3 ${isActive ? 'text-blue-600' : 'text-gray-400'}`}>
                      <div className={`p-3 rounded-full transition-all duration-300 ${
                        isActive 
                          ? 'bg-gradient-to-br from-blue-500 to-purple-500 text-white shadow-lg scale-110' 
                          : 'bg-gray-200'
                      }`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="hidden sm:block">
                        <p className={`font-semibold ${isCurrent ? 'text-blue-700' : ''}`}>
                          {step.title}
                        </p>
                        <p className="text-xs text-gray-500">{step.description}</p>
                      </div>
                    </div>
                    {index < steps.length - 1 && (
                      <div className={`w-16 lg:w-32 h-0.5 mx-4 transition-all duration-500 ${
                        currentStep > step.id ? 'bg-gradient-to-r from-blue-500 to-purple-500' : 'bg-gray-200'
                      }`} />
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Main Content */}
        <div className="space-y-8">
          {/* Étape 1: Upload CSV séparé */}
          {currentStep >= 1 && (
            <div className="animate-fade-in space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Étape 1 : Chargement des fichiers CSV
                </h2>
                <p className="text-gray-600">
                  Chargez vos fichiers interventions et intervenants séparément
                </p>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <InterventionsUpload 
                  onFileUploaded={handleFileUploaded}
                  interventionsFile={interventionsFile}
                />
                <IntervenantsUpload 
                  onFileUploaded={handleFileUploaded}
                  intervenantsFile={intervenantsFile}
                />
              </div>
            </div>
          )}

          {/* Étape 2: Génération du planning */}
          {currentStep >= 2 && (
            <div className="animate-fade-in">
              <div className="text-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Étape 2 : Génération du planning par IA
                </h2>
                <p className="text-gray-600">
                  L'intelligence artificielle va optimiser automatiquement vos tournées
                </p>
              </div>
              
              <PlanningGenerator 
                interventionsFile={interventionsFile}
                intervenantsFile={intervenantsFile}
                onPlanningGenerated={handlePlanningGenerated}
              />
            </div>
          )}

          {/* Étape 3: Affichage du planning */}
          {currentStep >= 3 && planningData && (
            <div className="animate-fade-in space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Étape 3 : Visualisation et export du planning
                </h2>
                <p className="text-gray-600">
                  Consultez votre planning optimisé et exportez-le aux formats souhaités
                </p>
              </div>
              
              <CalendarView planningData={planningData} stats={stats} />
              <ExportButtons planningData={planningData} stats={stats} />
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-16 py-8 border-t border-gray-200 bg-white/50 backdrop-blur-sm rounded-lg">
          <div className="text-center space-y-2">
            <p className="text-sm text-gray-600">
              🤖 <strong>Planification optimisée par OpenAI</strong> - Respect automatique de toutes les contraintes métier
            </p>
            <p className="text-xs text-gray-500">
              L'IA analyse vos données et génère le planning optimal en temps réel
            </p>
            <div className="flex justify-center gap-4 mt-4 text-xs text-gray-500">
              <span>✅ Respect des horaires 07h-22h</span>
              <span>✅ Gestion des repos obligatoires</span>
              <span>✅ Optimisation des trajets</span>
              <span>✅ Week-ends alternés</span>
            </div>
          </div>
        </footer>
      </div>

      <style jsx global>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fade-in {
          animation: fade-in 0.6s ease-out forwards;
        }
        
        .glass-effect {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
      `}</style>
    </div>
  );
}

export default App;