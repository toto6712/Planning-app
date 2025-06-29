import React, { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Users } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';

const InterventionsUpload = ({ onFileUploaded, interventionsFile }) => {
  const [dragActive, setDragActive] = useState(false);
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
    processFile(droppedFiles[0]);
  }, []);

  const handleFileInput = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      processFile(selectedFile);
    }
  };

  const processFile = (file) => {
    if (!file) return;

    // Vérifier l'extension
    if (!file.name.endsWith('.csv')) {
      setUploadStatus({
        type: 'error',
        message: 'Veuillez sélectionner un fichier CSV'
      });
      return;
    }

    // Vérifier que c'est bien un fichier d'interventions
    if (!file.name.toLowerCase().includes('intervention')) {
      setUploadStatus({
        type: 'warning',
        message: 'Le nom du fichier devrait contenir "intervention" pour plus de clarté'
      });
    }

    onFileUploaded('interventions', file);
    setUploadStatus({
      type: 'success',
      message: 'Fichier interventions chargé avec succès'
    });
  };

  const removeFile = () => {
    onFileUploaded('interventions', null);
    setUploadStatus(null);
  };

  return (
    <Card className="border-2 border-dashed transition-all duration-300 hover:border-avs-blue bg-gradient-to-br from-blue-50 to-avs-blue/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-avs-blue">
          <Users className="h-5 w-5 text-avs-blue" />
          Fichier Interventions
        </CardTitle>
        <CardDescription className="text-avs-blue/80">
          Chargez votre fichier interventions.csv contenant la liste des clients et visites à planifier
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!interventionsFile ? (
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300 ${
              dragActive 
                ? 'border-avs-blue bg-avs-blue/10 scale-105' 
                : 'border-avs-blue/30 hover:border-avs-blue hover:bg-avs-blue/5'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-4">
              <div className="mx-auto w-12 h-12 bg-avs-blue/20 rounded-full flex items-center justify-center">
                <FileText className={`h-6 w-6 text-avs-blue transition-transform duration-300 ${dragActive ? 'scale-110' : ''}`} />
              </div>
              
              <div>
                <p className="font-medium text-avs-blue">
                  Glissez interventions.csv ici
                </p>
                <p className="text-sm text-blue-600 mt-1">
                  ou cliquez pour sélectionner
                </p>
              </div>

              <input
                type="file"
                accept=".csv"
                onChange={handleFileInput}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>
          </div>
        ) : (
          <div className="p-4 bg-blue-100 border border-blue-300 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-blue-600" />
                <div>
                  <span className="font-medium text-blue-900">{interventionsFile.name}</span>
                  <p className="text-sm text-blue-700">
                    {(interventionsFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={removeFile}
                className="text-blue-700 hover:text-blue-900 hover:bg-blue-200"
              >
                Retirer
              </Button>
            </div>
          </div>
        )}

        {/* Statut d'upload */}
        {uploadStatus && (
          <Alert className={`mt-4 ${
            uploadStatus.type === 'error' ? 'border-red-200 bg-red-50' : 
            uploadStatus.type === 'warning' ? 'border-orange-200 bg-orange-50' :
            'border-blue-200 bg-blue-50'
          }`}>
            {uploadStatus.type === 'error' ? (
              <AlertCircle className="h-4 w-4 text-red-600" />
            ) : (
              <CheckCircle className="h-4 w-4 text-blue-600" />
            )}
            <AlertDescription className={
              uploadStatus.type === 'error' ? 'text-red-800' : 
              uploadStatus.type === 'warning' ? 'text-orange-800' :
              'text-blue-800'
            }>
              {uploadStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Format attendu */}
        <div className="mt-4 p-3 bg-white/60 rounded-lg border border-blue-200">
          <h4 className="font-medium text-blue-900 text-sm mb-2">📋 Format attendu :</h4>
          <code className="block text-xs bg-white p-2 rounded border">
            Client,Date,Durée,Adresse,Intervenant,Binôme,Référent<br/>
            Martin Dubois,29/06/2025 08:00,01:00,1 rue des Lilas Strasbourg,,false,<br/>
            Sophie Bernard,29/06/2025 14:30,00:45,5 avenue des Roses Strasbourg,Dupont,true,Martin
          </code>
          <div className="mt-2 text-xs text-blue-700 space-y-1">
            <p>• <strong>Client</strong> : Nom du client à visiter</p>
            <p>• <strong>Date</strong> : Format JJ/MM/AAAA HH:MM</p>
            <p>• <strong>Durée</strong> : Format HH:MM</p>
            <p>• <strong>Adresse</strong> : Adresse complète avec ville</p>
            <p>• <strong>Intervenant</strong> : Nom imposé ou vide pour auto-assignation</p>
            <p>• <strong>Binôme</strong> : true si 2 intervenants requis (optionnel)</p>
            <p>• <strong>Référent</strong> : Intervenant préféré pour ce client (optionnel)</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default InterventionsUpload;