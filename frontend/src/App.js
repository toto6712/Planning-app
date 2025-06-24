import React, { useState, useEffect } from "react";
import "./App.css";
import { Toaster } from "./components/ui/toaster";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { CalendarDays, Brain, Upload, Download } from "lucide-react";
import CSVUpload from "./components/CSVUpload";
import CalendarView from "./components/CalendarView";
import ExportButtons from "./components/ExportButtons";

function App() {
  const [planningData, setPlanningData] = useState(null);
  const [stats, setStats] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);

  const handleFilesProcessed = (result) => {
    setPlanningData(result.planning);
    setStats(result.stats);
    setCurrentStep(2);
  };

  const steps = [
    { 
      id: 1, 
      title: "Import CSV", 
      icon: Upload, 
      description: "Chargez vos fichiers interventions et intervenants" 
    },
    { 
      id: 2, 
      title: "Planning IA", 
      icon: Brain, 
      description: "Visualisez le planning optimisé automatiquement" 
    },
    { 
      id: 3, 
      title: "Export", 
      icon: Download, 
      description: "Téléchargez votre planning en PDF ou CSV" 
    }
  ];

  useEffect(() => {
    if (planningData && planningData.length > 0) {
      setCurrentStep(3);
    }
  }, [planningData]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <Toaster />
      
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl">
                <CalendarDays className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Planning Tournées IA
                </h1>
                <p className="text-sm text-gray-600">
                  Optimisation automatique de vos interventions à domicile
                </p>
              </div>
            </div>
            <Badge variant="secondary" className="bg-green-100 text-green-800 px-3 py-1">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
              DÉMO AVEC MOCK DATA
            </Badge>
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
          {/* Étape 1: Upload CSV */}
          {currentStep >= 1 && (
            <div className="animate-fade-in">
              <CSVUpload onFilesProcessed={handleFilesProcessed} />
            </div>
          )}

          {/* Étape 2: Affichage du planning */}
          {currentStep >= 2 && planningData && (
            <div className="animate-fade-in">
              <CalendarView planningData={planningData} stats={stats} />
            </div>
          )}

          {/* Étape 3: Export */}
          {currentStep >= 3 && planningData && (
            <div className="animate-fade-in">
              <ExportButtons planningData={planningData} stats={stats} />
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-16 py-8 border-t border-gray-200 bg-white/50 backdrop-blur-sm rounded-lg">
          <div className="text-center space-y-2">
            <p className="text-sm text-gray-600">
              🤖 <strong>Application de démonstration</strong> - Utilise des données mock pour la présentation
            </p>
            <p className="text-xs text-gray-500">
              L'IA ChatGPT optimisera automatiquement vos vraies données selon les contraintes métier
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