import React, { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, UserCheck } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';

const IntervenantsUpload = ({ onFileUploaded, intervenantsFile }) => {
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

    // Vérifier que c'est bien un fichier d'intervenants
    if (!file.name.toLowerCase().includes('intervenant')) {
      setUploadStatus({
        type: 'warning',
        message: 'Le nom du fichier devrait contenir "intervenant" pour plus de clarté'
      });
    }

    onFileUploaded('intervenants', file);
    setUploadStatus({
      type: 'success',
      message: 'Fichier intervenants chargé avec succès'
    });
  };

  const removeFile = () => {
    onFileUploaded('intervenants', null);
    setUploadStatus(null);
  };

  return (
    <Card className="border-2 border-dashed transition-all duration-300 hover:border-green-400 bg-gradient-to-br from-green-50 to-emerald-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-green-900">
          <UserCheck className="h-5 w-5 text-green-600" />
          Fichier Intervenants
        </CardTitle>
        <CardDescription className="text-green-700">
          Chargez votre fichier intervenants.csv avec les disponibilités et contraintes de votre équipe
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!intervenantsFile ? (
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300 ${
              dragActive 
                ? 'border-green-500 bg-green-100 scale-105' 
                : 'border-green-300 hover:border-green-400 hover:bg-green-50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-4">
              <div className="mx-auto w-12 h-12 bg-green-200 rounded-full flex items-center justify-center">
                <FileText className={`h-6 w-6 text-green-600 transition-transform duration-300 ${dragActive ? 'scale-110' : ''}`} />
              </div>
              
              <div>
                <p className="font-medium text-green-900">
                  Glissez intervenants.csv ici
                </p>
                <p className="text-sm text-green-600 mt-1">
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
          <div className="p-4 bg-green-100 border border-green-300 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <span className="font-medium text-green-900">{intervenantsFile.name}</span>
                  <p className="text-sm text-green-700">
                    {(intervenantsFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={removeFile}
                className="text-green-700 hover:text-green-900 hover:bg-green-200"
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
            'border-green-200 bg-green-50'
          }`}>
            {uploadStatus.type === 'error' ? (
              <AlertCircle className="h-4 w-4 text-red-600" />
            ) : (
              <CheckCircle className="h-4 w-4 text-green-600" />
            )}
            <AlertDescription className={
              uploadStatus.type === 'error' ? 'text-red-800' : 
              uploadStatus.type === 'warning' ? 'text-orange-800' :
              'text-green-800'
            }>
              {uploadStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Format attendu */}
        <div className="mt-4 p-3 bg-white/60 rounded-lg border border-green-200">
          <h4 className="font-medium text-green-900 text-sm mb-2">📋 Format attendu :</h4>
          <code className="block text-xs bg-white p-2 rounded border">
            Nom,Adresse,Disponibilités,Repos,Week-end<br/>
            Dupont,12 avenue des Vosges Strasbourg,L-M-M-J-V 07-14,2025-07-01,A<br/>
            Martin,8 rue du Commerce Strasbourg,L-M-M-J-V-S 14-22,,B
          </code>
          <div className="mt-2 text-xs text-green-700 space-y-1">
            <p>• <strong>Nom</strong> : Nom de l'intervenant</p>
            <p>• <strong>Adresse</strong> : Domicile de l'intervenant</p>
            <p>• <strong>Disponibilités</strong> : Jours et heures (L-M-M-J-V-S-D HH-HH)</p>
            <p>• <strong>Repos</strong> : Date de congé spécifique (format AAAA-MM-JJ)</p>
            <p>• <strong>Week-end</strong> : Type A ou B pour alternance</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default IntervenantsUpload;