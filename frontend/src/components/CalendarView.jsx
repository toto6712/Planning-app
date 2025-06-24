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
    
    // Utiliser les événements filtrés pour calculer les heures selon la période affichée
    const eventsToProcess = filteredEvents || planningData || [];
    
    eventsToProcess.forEach(event => {
      const intervenant = event.extendedProps?.intervenant || event.intervenant;
      if (intervenant) {
        if (!intervenantData.has(intervenant)) {
          intervenantData.set(intervenant, {
            name: intervenant,
            color: event.backgroundColor || event.borderColor || '#64748b',
            totalMinutes: 0,
            interventionsCount: 0
          });
        }
        
        // Calculer la durée de l'intervention
        const startTime = new Date(event.start);
        const endTime = new Date(event.end);
        const durationMinutes = (endTime - startTime) / (1000 * 60);
        
        const data = intervenantData.get(intervenant);
        data.totalMinutes += durationMinutes;
        data.interventionsCount += 1;
        intervenantData.set(intervenant, data);
      }
    });

    // Convertir en array et ajouter les heures formatées
    return Array.from(intervenantData.values()).map(data => ({
      ...data,
      formattedHours: formatMinutesToHours(data.totalMinutes)
    }));
  };

  const formatMinutesToHours = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours === 0) {
      return `${mins}min`;
    } else if (mins === 0) {
      return `${hours}h`;
    } else {
      return `${hours}h${mins}`;
    }
  };

  const getPeriodLabel = () => {
    switch (viewFilter) {
      case 'day':
        return 'jour';
      case 'week':
        return 'semaine';
      case 'month':
        return 'mois';
      case 'custom':
        return 'période';
      default:
        return 'total';
    }
  };

  const createTravelTimeEvents = (events) => {
    if (!events || events.length === 0) return [];
    
    const travelEvents = [];
    
    // Grouper les événements par intervenant
    const eventsByIntervenant = {};
    events.forEach(event => {
      const intervenant = event.extendedProps?.intervenant || event.intervenant;
      if (intervenant && !event.extendedProps?.isTravel) {
        if (!eventsByIntervenant[intervenant]) {
          eventsByIntervenant[intervenant] = [];
        }
        eventsByIntervenant[intervenant].push(event);
      }
    });

    // Créer les événements de trajet entre interventions consécutives
    Object.keys(eventsByIntervenant).forEach(intervenant => {
      const interventions = eventsByIntervenant[intervenant]
        .sort((a, b) => new Date(a.start) - new Date(b.start));
      
      for (let i = 0; i < interventions.length - 1; i++) {
        const currentEvent = interventions[i];
        const nextEvent = interventions[i + 1];
        
        const currentEnd = new Date(currentEvent.end);
        const nextStart = new Date(nextEvent.start);
        
        // Créer un événement de trajet si il y a du temps entre les interventions
        if (nextStart > currentEnd) {
          const travelTime = currentEvent.extendedProps?.trajet_vers_suivant || 
                            nextEvent.extendedProps?.trajet_precedent || "15 min";
          
          travelEvents.push({
            id: `travel-${currentEvent.id}-${nextEvent.id}`,
            title: `🚗 Trajet ${travelTime}`,
            start: currentEnd.toISOString(),
            end: nextStart.toISOString(),
            backgroundColor: '#00ff88',
            borderColor: '#00cc6a',
            textColor: '#000',
            extendedProps: {
              isTravel: true,
              intervenant: intervenant,
              travelTime: travelTime,
              fromAddress: currentEvent.extendedProps?.adresse || '',
              toAddress: nextEvent.extendedProps?.adresse || ''
            },
            display: 'block',
            classNames: ['travel-event']
          });
        }
      }
    });

    return travelEvents;
  };

  const getAllEvents = () => {
    const regularEvents = filteredEvents || [];
    const travelEvents = createTravelTimeEvents(regularEvents);
    return [...regularEvents, ...travelEvents];
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
        <div className="grid grid-cols-1 gap-6">
          {/* Légende des intervenants */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Légende des intervenants - {getPeriodLabel()}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {getLegendData().map((legend, index) => (
                  <Badge 
                    key={index}
                    variant="secondary" 
                    className="flex items-center gap-2 px-3 py-2 border"
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
                    <div className="flex flex-col">
                      <span className="font-medium text-sm">{legend.name}</span>
                      <span className="text-xs opacity-75">
                        {legend.formattedHours} • {legend.interventionsCount} intervention{legend.interventionsCount > 1 ? 's' : ''}
                      </span>
                    </div>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Contrôles de vue avec filtres intégrés */}
      <Card>
        <CardHeader>
          <div className="flex flex-col space-y-4">
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
            
            {/* Filtres de période intégrés */}
            {planningData && planningData.length > 0 && (
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={viewFilter === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleFilterChange('all')}
                  >
                    Tout ({planningData.length})
                  </Button>
                  <Button
                    variant={viewFilter === 'day' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleFilterChange('day')}
                  >
                    Jour
                  </Button>
                  <Button
                    variant={viewFilter === 'week' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleFilterChange('week')}
                  >
                    Semaine
                  </Button>
                  <Button
                    variant={viewFilter === 'month' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleFilterChange('month')}
                  >
                    Mois
                  </Button>
                  <Button
                    variant={viewFilter === 'custom' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => {
                      setViewFilter('custom');
                      setShowDatePicker(!showDatePicker);
                    }}
                  >
                    <CalendarRange className="h-4 w-4 mr-1" />
                    Personnalisé
                  </Button>
                </div>
                
                {/* Sélecteur de date pour les filtres */}
                {(viewFilter === 'day' || viewFilter === 'week' || viewFilter === 'month') && (
                  <div className="flex items-center gap-2">
                    <input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-500">
                      ({filteredEvents.length} intervention{filteredEvents.length > 1 ? 's' : ''})
                    </span>
                  </div>
                )}
              </div>
            )}
            
            {/* Sélecteur de plage personnalisée */}
            {showDatePicker && viewFilter === 'custom' && (
              <div className="flex flex-col sm:flex-row gap-3 p-3 bg-gray-50 rounded-lg border">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Du :</label>
                  <input
                    type="date"
                    value={customDateRange.start}
                    onChange={(e) => setCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Au :</label>
                  <input
                    type="date"
                    value={customDateRange.end}
                    onChange={(e) => setCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <span className="text-sm text-gray-500 self-center">
                  ({filteredEvents.length} intervention{filteredEvents.length > 1 ? 's' : ''})
                </span>
              </div>
            )}
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
              initialDate={selectedDate}
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
              datesSet={(dateInfo) => {
                // Synchroniser le calendrier avec la date sélectionnée
                if (viewFilter !== 'all') {
                  const viewDate = new Date(dateInfo.view.currentStart);
                  const newSelectedDate = viewDate.toISOString().split('T')[0];
                  if (newSelectedDate !== selectedDate) {
                    setSelectedDate(newSelectedDate);
                  }
                }
              }}
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