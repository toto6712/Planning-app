// Données mock pour la démonstration de l'application de planification

export const mockInterventions = [
  {
    id: 1,
    client: "Martin",
    date: "2025-06-29T08:00",
    duration: "01:00",
    address: "1 rue des Lilas, Strasbourg",
    intervenant: "Dupont"
  },
  {
    id: 2,
    client: "Durand",
    date: "2025-06-30T10:30",
    duration: "00:45",
    address: "3 rue des Acacias, Strasbourg",
    intervenant: ""
  },
  {
    id: 3,
    client: "Petit",
    date: "2025-07-01T14:00",
    duration: "01:30",
    address: "5 avenue des Roses, Strasbourg",
    intervenant: "Martin"
  },
  {
    id: 4,
    client: "Bernard",
    date: "2025-07-02T09:15",
    duration: "00:30",
    address: "12 place du Marché, Strasbourg",
    intervenant: ""
  }
];

export const mockIntervenants = [
  {
    id: 1,
    nom: "Dupont",
    address: "12 avenue des Vosges, Strasbourg",
    disponibilites: "L-M-M-J-V 07-14",
    repos: "2025-06-30",
    weekend: "A"
  },
  {
    id: 2,
    nom: "Martin",
    address: "8 rue du Commerce, Strasbourg",
    disponibilites: "L-M-M-J-V-S 14-22",
    repos: "2025-07-01",
    weekend: "B"
  },
  {
    id: 3,
    nom: "Leroy",
    address: "25 boulevard de la Liberté, Strasbourg",
    disponibilites: "M-M-J-V-S-D 07-22",
    repos: "",
    weekend: "A"
  }
];

// Planning optimisé généré par l'IA (simulation)
export const mockPlanningData = [
  {
    id: 1,
    title: "Martin - Dupont",
    start: "2025-06-29T08:00:00",
    end: "2025-06-29T09:00:00",
    backgroundColor: "#32a852",
    borderColor: "#2d8f47",
    extendedProps: {
      client: "Martin",
      intervenant: "Dupont",
      address: "1 rue des Lilas, Strasbourg",
      duration: "1h00",
      nonPlanifiable: false,
      trajetPrecedent: "0 min"
    }
  },
  {
    id: 2,
    title: "Durand - Martin",
    start: "2025-06-30T10:30:00",
    end: "2025-06-30T11:15:00",
    backgroundColor: "#3b82f6",
    borderColor: "#2563eb",
    extendedProps: {
      client: "Durand",
      intervenant: "Martin",
      address: "3 rue des Acacias, Strasbourg",
      duration: "45min",
      nonPlanifiable: false,
      trajetPrecedent: "5 min"
    }
  },
  {
    id: 3,
    title: "Petit - Martin",
    start: "2025-07-01T14:00:00",
    end: "2025-07-01T15:30:00",
    backgroundColor: "#3b82f6",
    borderColor: "#2563eb",
    extendedProps: {
      client: "Petit",
      intervenant: "Martin",
      address: "5 avenue des Roses, Strasbourg",
      duration: "1h30",
      nonPlanifiable: false,
      trajetPrecedent: "10 min"
    }
  },
  {
    id: 4,
    title: "Bernard - NON PLANIFIABLE",
    start: "2025-07-02T09:15:00",
    end: "2025-07-02T09:45:00",
    backgroundColor: "#a0e0ff",
    borderColor: "#7dd3fc",
    extendedProps: {
      client: "Bernard",
      intervenant: "Aucun disponible",
      address: "12 place du Marché, Strasbourg",
      duration: "30min",
      nonPlanifiable: true,
      raison: "Aucun intervenant disponible à cet horaire"
    }
  }
];

export const mockStats = {
  totalInterventions: 4,
  interventionsPlanifiees: 3,
  interventionsNonPlanifiables: 1,
  intervenants: 3,
  tauxPlanification: 75
};

// Fonction pour simuler l'upload et traitement des fichiers CSV
export const simulateFileProcessing = (files) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        message: "Fichiers traités avec succès par l'IA",
        stats: mockStats,
        planning: mockPlanningData
      });
    }, 2000);
  });
};

// Fonction pour simuler l'export PDF
export const simulateExportPDF = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        filename: "planning_tournees_" + new Date().toISOString().split('T')[0] + ".pdf",
        message: "Export PDF généré avec succès"
      });
    }, 1500);
  });
};

// Fonction pour simuler l'export CSV
export const simulateExportCSV = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const csvData = mockPlanningData.map(event => ({
        Date: event.start.split('T')[0],
        Heure_debut: event.start.split('T')[1].substring(0,5),
        Heure_fin: event.end.split('T')[1].substring(0,5),
        Client: event.extendedProps.client,
        Intervenant: event.extendedProps.intervenant,
        Adresse: event.extendedProps.address,
        Duree: event.extendedProps.duration,
        Non_planifiable: event.extendedProps.nonPlanifiable ? 'Oui' : 'Non'
      }));
      
      resolve({
        success: true,
        filename: "planning_tournees_" + new Date().toISOString().split('T')[0] + ".csv",
        data: csvData,
        message: "Export CSV généré avec succès"
      });
    }, 1000);
  });
};