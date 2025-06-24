import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import frLocale from '@fullcalendar/core/locales/fr';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Calendar, Clock, MapPin, User, AlertTriangle, CheckCircle, Filter, CalendarRange } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';

const CalendarView = ({ planningData, stats }) => {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [currentView, setCurrentView] = useState('timeGridWeek');
  const [viewFilter, setViewFilter] = useState('all'); // all, day, week, month, custom
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [customDateRange, setCustomDateRange] = useState({
    start: new Date().toISOString().split('T')[0],
    end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });
  const [showDatePicker, setShowDatePicker] = useState(false);

  const getLegendData = () => {
    const intervenantData = new Map();
    
    planningData?.forEach(event => {
      const intervenant = event.extendedProps.intervenant;
      if (intervenant && !intervenantData.has(intervenant)) {
        intervenantData.set(intervenant, {
          name: intervenant,
          color: event.backgroundColor || event.borderColor || '#64748b'
        });
      }
    });
    
    return Array.from(intervenantData.values()).sort((a, b) => a.name.localeCompare(b.name));
  };

  // Filtrer les événements selon la vue sélectionnée
  const getFilteredEvents = () => {
    if (!planningData) return [];
    
    const referenceDate = new Date(selectedDate);
    const today = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), referenceDate.getDate());
    
    // Calculer début et fin de semaine
    const weekStart = new Date(today);
    const dayOfWeek = weekStart.getDay();
    const diffToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Lundi = 1
    weekStart.setDate(weekStart.getDate() + diffToMonday);
    weekStart.setHours(0, 0, 0, 0);
    
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    weekEnd.setHours(23, 59, 59, 999);
    
    // Calculer début et fin de mois
    const monthStart = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), 1);
    monthStart.setHours(0, 0, 0, 0);
    const monthEnd = new Date(referenceDate.getFullYear(), referenceDate.getMonth() + 1, 0);
    monthEnd.setHours(23, 59, 59, 999);

    return planningData.filter(event => {
      const eventDate = new Date(event.start);
      
      switch (viewFilter) {
        case 'day':
          const eventDay = new Date(eventDate.getFullYear(), eventDate.getMonth(), eventDate.getDate());
          return eventDay.getTime() === today.getTime();
        case 'week':
          return eventDate >= weekStart && eventDate <= weekEnd;
        case 'month':
          return eventDate >= monthStart && eventDate <= monthEnd;
        case 'custom':
          const customStart = new Date(customDateRange.start);
          customStart.setHours(0, 0, 0, 0);
          const customEnd = new Date(customDateRange.end);
          customEnd.setHours(23, 59, 59, 999);
          return eventDate >= customStart && eventDate <= customEnd;
        default:
          return true;
      }
    });
  };

  const filteredEvents = getFilteredEvents();

  const handleEventClick = (eventInfo) => {
    setSelectedEvent(eventInfo.event);
  };

  const handleDateClick = (dateInfo) => {
    console.log('Date cliquée:', dateInfo.dateStr);
    setSelectedDate(dateInfo.dateStr);
    if (viewFilter === 'all') {
      setViewFilter('day');
    }
  };

  const handleFilterChange = (newFilter) => {
    setViewFilter(newFilter);
    if (newFilter !== 'custom') {
      setShowDatePicker(false);
    }
  };

  const formatDuration = (start, end) => {
    const startTime = new Date(start);
    const endTime = new Date(end);
    const diffMs = endTime - startTime;
    const diffMins = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMins / 60);
    const minutes = diffMins % 60;
    return hours > 0 ? `${hours}h${minutes.toString().padStart(2, '0')}` : `${minutes}min`;
  };

  return (
    <div className="space-y-6">
      {/* Statistiques */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="font-semibold text-blue-900">{stats.totalInterventions}</p>
                  <p className="text-xs text-blue-700">Total interventions</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <p className="font-semibold text-green-900">{stats.interventionsPlanifiees}</p>
                  <p className="text-xs text-green-700">Planifiées</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                <div>
                  <p className="font-semibold text-orange-900">{stats.interventionsNonPlanifiables}</p>
                  <p className="text-xs text-orange-700">Non planifiables</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <User className="h-5 w-5 text-purple-600" />
                <div>
                  <p className="font-semibold text-purple-900">{stats.intervenants}</p>
                  <p className="text-xs text-purple-700">Intervenants</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-gray-600" />
                <div>
                  <p className="font-semibold text-gray-900">{stats.tauxPlanification}%</p>
                  <p className="text-xs text-gray-700">Taux planning</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtres et Légende */}
      {planningData && planningData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Filtres par période */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Filtrer par période
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant={viewFilter === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewFilter('all')}
                  className="flex-1 min-w-[80px]"
                >
                  Tout
                </Button>
                <Button
                  variant={viewFilter === 'day' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewFilter('day')}
                  className="flex-1 min-w-[80px]"
                >
                  Aujourd'hui
                </Button>
                <Button
                  variant={viewFilter === 'week' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewFilter('week')}
                  className="flex-1 min-w-[80px]"
                >
                  Cette semaine
                </Button>
                <Button
                  variant={viewFilter === 'month' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewFilter('month')}
                  className="flex-1 min-w-[80px]"
                >
                  Ce mois
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {filteredEvents.length} intervention(s) affichée(s)
              </p>
            </CardContent>
          </Card>

          {/* Légende des intervenants */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Légende des intervenants</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {getLegendData().map((legend, index) => (
                  <Badge 
                    key={index}
                    variant="secondary" 
                    className="flex items-center gap-2 px-3 py-1 border"
                    style={{ 
                      backgroundColor: legend.color + '20', 
                      borderColor: legend.color,
                      color: legend.color
                    }}
                  >
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: legend.color }}
                    />
                    <span className="font-medium">{legend.name}</span>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Contrôles de vue */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              Planning des tournées
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant={currentView === 'dayGridMonth' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentView('dayGridMonth')}
              >
                Mois
              </Button>
              <Button
                variant={currentView === 'timeGridWeek' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentView('timeGridWeek')}
              >
                Semaine
              </Button>
              <Button
                variant={currentView === 'timeGridDay' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentView('timeGridDay')}
              >
                Jour
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="calendar-container" style={{ height: '600px' }}>
            <FullCalendar
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              initialView={currentView}
              locale={frLocale}
              headerToolbar={{
                left: 'prev,next today',
                center: 'title',
                right: ''
              }}
              events={filteredEvents || []}
              eventClick={handleEventClick}
              dateClick={handleDateClick}
              height="100%"
              slotMinTime="07:00:00"
              slotMaxTime="22:00:00"
              allDaySlot={false}
              nowIndicator={true}
              eventDidMount={(info) => {
                // Ajouter une classe pour les événements non planifiables
                if (info.event.extendedProps.nonPlanifiable) {
                  info.el.classList.add('non-planifiable');
                  info.el.style.opacity = '0.8';
                  info.el.style.borderLeft = '4px solid #f59e0b';
                }
              }}
              view={currentView}
              viewDidMount={(view) => setCurrentView(view.view.type)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Modal de détails d'événement */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full max-h-[80vh] overflow-y-auto">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Détails de l'intervention</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setSelectedEvent(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <User className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Client</p>
                    <p className="text-gray-600">{selectedEvent.extendedProps.client}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <User className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Intervenant</p>
                    <p className="text-gray-600">{selectedEvent.extendedProps.intervenant}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Clock className="h-5 w-5 text-purple-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Horaires</p>
                    <p className="text-gray-600">
                      {new Date(selectedEvent.start).toLocaleTimeString('fr-FR', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })} - {new Date(selectedEvent.end).toLocaleTimeString('fr-FR', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </p>
                    <p className="text-sm text-gray-500">
                      Durée : {formatDuration(selectedEvent.start, selectedEvent.end)}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Adresse</p>
                    <p className="text-gray-600">{selectedEvent.extendedProps.address}</p>
                    {selectedEvent.extendedProps.trajetPrecedent && (
                      <p className="text-sm text-gray-500">
                        Trajet depuis intervention précédente : {selectedEvent.extendedProps.trajetPrecedent}
                      </p>
                    )}
                  </div>
                </div>

                {selectedEvent.extendedProps.nonPlanifiable && (
                  <div className="flex items-start gap-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-orange-900">Intervention non planifiable</p>
                      <p className="text-sm text-orange-700">
                        {selectedEvent.extendedProps.raison || "Contraintes non respectées"}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t">
                <Button 
                  onClick={() => setSelectedEvent(null)}
                  className="w-full"
                >
                  Fermer
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <style jsx global>{`
        .non-planifiable {
          animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 0.8; }
          50% { opacity: 1; }
        }
        
        .fc-event-time {
          font-weight: 600;
        }
        
        .fc-event-title {
          font-weight: 500;
        }
        
        .fc-timegrid-slot {
          height: 2em;
        }
        
        .fc-col-header-cell {
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
          font-weight: 600;
        }
        
        .fc-daygrid-day-number {
          color: #1e293b;
          font-weight: 600;
        }
      `}</style>
    </div>
  );
};

export default CalendarView;