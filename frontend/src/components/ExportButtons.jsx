import React, { useState } from 'react';
import { Download, FileText, Table, Loader2, CheckCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { simulateExportPDF, simulateExportCSV } from '../mock';

const ExportButtons = ({ planningData, stats }) => {
  const [exportingPDF, setExportingPDF] = useState(false);
  const [exportingCSV, setExportingCSV] = useState(false);
  const [exportStatus, setExportStatus] = useState(null);

  const handleExportPDF = async () => {
    setExportingPDF(true);
    setExportStatus(null);
    
    try {
      const result = await simulateExportPDF();
      setExportStatus({
        type: 'success',
        message: `✅ ${result.message} - ${result.filename}`
      });
      
      // Simulation du téléchargement
      const element = document.createElement('a');
      element.href = 'data:application/pdf;base64,JVBERi0xLjQKJe...'; // PDF simulé
      element.download = result.filename;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      
    } catch (error) {
      setExportStatus({
        type: 'error',
        message: 'Erreur lors de l\'export PDF'
      });
    } finally {
      setExportingPDF(false);
    }
  };

  const handleExportCSV = async () => {
    setExportingCSV(true);
    setExportStatus(null);
    
    try {
      const result = await simulateExportCSV();
      setExportStatus({
        type: 'success',
        message: `✅ ${result.message} - ${result.filename}`
      });
      
      // Création et téléchargement du CSV réel
      const csvContent = convertToCSV(result.data);
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      
      const element = document.createElement('a');
      element.href = url;
      element.download = result.filename;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      URL.revokeObjectURL(url);
      
    } catch (error) {
      setExportStatus({
        type: 'error',
        message: 'Erreur lors de l\'export CSV'
      });
    } finally {
      setExportingCSV(false);
    }
  };

  const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    data.forEach(row => {
      const values = headers.map(header => {
        const value = row[header];
        return `"${value}"`;
      });
      csvRows.push(values.join(','));
    });
    
    return csvRows.join('\n');
  };

  const isDataAvailable = planningData && planningData.length > 0;

  return (
    <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-indigo-900">
          <Download className="h-5 w-5" />
          Export du planning
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Statut d'export */}
        {exportStatus && (
          <Alert className={`${exportStatus.type === 'error' ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}>
            <CheckCircle className={`h-4 w-4 ${exportStatus.type === 'error' ? 'text-red-600' : 'text-green-600'}`} />
            <AlertDescription className={exportStatus.type === 'error' ? 'text-red-800' : 'text-green-800'}>
              {exportStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Résumé des données */}
        {stats && (
          <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-indigo-200">
            <h4 className="font-medium text-indigo-900 mb-2">Résumé du planning</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-indigo-700">Total interventions :</span>
                <span className="font-semibold ml-2 text-indigo-900">{stats.totalInterventions}</span>
              </div>
              <div>
                <span className="text-indigo-700">Planifiées :</span>
                <span className="font-semibold ml-2 text-green-700">{stats.interventionsPlanifiees}</span>
              </div>
              <div>
                <span className="text-indigo-700">Non planifiables :</span>
                <span className="font-semibold ml-2 text-orange-700">{stats.interventionsNonPlanifiables}</span>
              </div>
              <div>
                <span className="text-indigo-700">Taux de planification :</span>
                <span className="font-semibold ml-2 text-indigo-900">{stats.tauxPlanification}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Boutons d'export */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Button
            onClick={handleExportPDF}
            disabled={!isDataAvailable || exportingPDF}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white transition-all duration-300 transform hover:scale-105"
          >
            {exportingPDF ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
            {exportingPDF ? 'Génération PDF...' : 'Export PDF'}
          </Button>

          <Button
            onClick={handleExportCSV}
            disabled={!isDataAvailable || exportingCSV}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white transition-all duration-300 transform hover:scale-105"
          >
            {exportingCSV ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Table className="h-4 w-4" />
            )}
            {exportingCSV ? 'Génération CSV...' : 'Export CSV'}
          </Button>
        </div>

        {/* Informations sur les formats */}
        <div className="text-xs text-indigo-700 space-y-1 bg-white/40 p-3 rounded-lg">
          <p><strong>📄 PDF :</strong> Planning visuel complet avec calendrier et statistiques</p>
          <p><strong>📊 CSV :</strong> Données tabulaires pour intégration dans d'autres outils</p>
        </div>

        {!isDataAvailable && (
          <div className="text-center py-4 text-gray-500">
            <Download className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Veuillez d'abord générer un planning pour activer les exports</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ExportButtons;