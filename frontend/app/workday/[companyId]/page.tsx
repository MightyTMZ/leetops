'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { companyAPI, simulationAPI } from '@/lib/api';
import { AlertTriangle, Clock, CheckCircle, XCircle, Loader2, Play, Square, Timer, Calendar } from 'lucide-react';
import { cn, formatTime, getSeverityColor, getSeverityLabel } from '@/lib/utils';

interface Company {
  id: number;
  name: string;
  description: string;
  industry: string;
  company_size: string;
  tech_stack: string[];
}

interface Incident {
  incident_id: string;
  title: string;
  description: string;
  severity: string;
  time_limit_minutes: number;
  affected_services: string[];
  error_logs: string;
  codebase_context: string;
  monitoring_dashboard_url: string;
  started_at: string;
  status: string;
}

interface GroqGrading {
  score: number;
  feedback: string;
  grading_method: string;
}

interface ResolutionResult {
  incident_resolved: boolean;
  time_spent_minutes: number;
  rating_result: any;
  rating_change: number;
  new_overall_rating: number;
  attempt_id: string;
  incident_status: string;
  groq_grading: GroqGrading;
}

interface WorkdaySession {
  id: string;
  company_id: number;
  user_email: string;
  start_time: string;
  end_time: string;
  incidents_scheduled: number;
  incidents_resolved: number;
  incidents_escalated: number;
  incidents_abandoned: number;
  current_rating: number;
  is_active: boolean;
}

export default function WorkdaySimulationPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const companyId = params.companyId as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [workdaySession, setWorkdaySession] = useState<WorkdaySession | null>(null);
  const [currentIncident, setCurrentIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [resolutionApproach, setResolutionApproach] = useState('');
  const [solutionType, setSolutionType] = useState<'root_cause' | 'workaround' | 'escalation' | 'abandonment'>('workaround');
  const [isResolving, setIsResolving] = useState(false);
  const [resolutionResult, setResolutionResult] = useState<ResolutionResult | null>(null);
  const [showGradingModal, setShowGradingModal] = useState(false);
  const [currentUserRating, setCurrentUserRating] = useState(800);
  
  // Workday simulation state
  const [simulationStatus, setSimulationStatus] = useState<'idle' | 'waiting' | 'active' | 'completed' | 'monitoring'>('idle');
  const [nextIncidentTime, setNextIncidentTime] = useState<Date | null>(null);
  const [timeUntilNext, setTimeUntilNext] = useState(0);
  const [incidentCount, setIncidentCount] = useState(0);
  const [sessionStats, setSessionStats] = useState({
    resolved: 0,
    escalated: 0,
    abandoned: 0
  });
  const [isMonitoringMode, setIsMonitoringMode] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchCompanyAndStartWorkday();
  }, [companyId, isAuthenticated, router]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (currentIncident && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            // Time's up - auto-escalate
            handleResolveIncident(false, 'escalation');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [currentIncident, timeRemaining]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (simulationStatus === 'waiting' && nextIncidentTime) {
      interval = setInterval(() => {
        const now = new Date();
        const timeLeft = Math.max(0, Math.floor((nextIncidentTime.getTime() - now.getTime()) / 1000));
        setTimeUntilNext(timeLeft);
        
        if (timeLeft <= 0) {
          generateNextIncident();
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [simulationStatus, nextIncidentTime]);

  const fetchCompanyAndStartWorkday = async () => {
    try {
      // Fetch company details
      const companyResponse = await companyAPI.getCompany(parseInt(companyId));
      setCompany(companyResponse);

      // Start workday simulation
      await startWorkdaySimulation();
    } catch (error) {
      console.error('Failed to load company and start workday:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startWorkdaySimulation = async () => {
    try {
      // Start workday session
      const sessionResponse = await simulationAPI.startWorkdaySimulation(parseInt(companyId));
      setWorkdaySession(sessionResponse);
      setCurrentUserRating(sessionResponse.current_rating);
      
      // Generate first incident after a short delay
      setSimulationStatus('waiting');
      scheduleNextIncident(5); // First incident in 5 seconds
      
    } catch (error) {
      console.error('Failed to start workday simulation:', error);
    }
  };

  const generateRandomInterval = () => {
    // Generate random interval from 10 seconds to 4 hours
    // Weighted towards shorter intervals for more realistic simulation
    const random = Math.random();
    
    if (random < 0.3) {
      // 30% chance: 10 seconds to 5 minutes (quick incidents)
      return Math.floor(Math.random() * 290) + 10;
    } else if (random < 0.7) {
      // 40% chance: 5 minutes to 1 hour (normal intervals)
      return Math.floor(Math.random() * 3300) + 300;
    } else if (random < 0.9) {
      // 20% chance: 1 hour to 2 hours (longer breaks)
      return Math.floor(Math.random() * 3600) + 3600;
    } else {
      // 10% chance: 2 hours to 4 hours (very long breaks)
      return Math.floor(Math.random() * 7200) + 7200;
    }
  };

  const scheduleNextIncident = (delaySeconds?: number) => {
    const actualDelay = delaySeconds || generateRandomInterval();
    const nextTime = new Date(Date.now() + actualDelay * 1000);
    setNextIncidentTime(nextTime);
    setTimeUntilNext(actualDelay);
    setSimulationStatus('waiting');
  };

  const generateNextIncident = async () => {
    try {
      setSimulationStatus('active');
      setNextIncidentTime(null);
      setTimeUntilNext(0);
      
      // Generate new incident
      const incidentResponse = await simulationAPI.generateIncident(parseInt(companyId));
      const incident = incidentResponse;
      
      setCurrentIncident(incident);
      setTimeRemaining(incident.time_limit_minutes * 60); // Convert to seconds
      setResolutionApproach('');
      setSolutionType('workaround');
      setIncidentCount(prev => prev + 1);
      
    } catch (error) {
      console.error('Failed to generate incident:', error);
    }
  };

  const handleResolveIncident = async (wasSuccessful: boolean, type?: 'root_cause' | 'workaround' | 'escalation' | 'abandonment') => {
    if (!currentIncident || isResolving) return;

    setIsResolving(true);
    try {
      const resolutionType = type || solutionType;
      const result = await simulationAPI.resolveIncident({
        incidentId: currentIncident.incident_id,
        resolutionApproach,
        codeChanges: '',
        commandsExecuted: [],
        solutionType: resolutionType,
        wasSuccessful,
      });

      // Store the resolution result with LLM grading
      setResolutionResult(result);
      setCurrentUserRating(result.new_overall_rating);
      setShowGradingModal(true);

      // Update session stats
      if (result.incident_status === 'resolved') {
        setSessionStats(prev => ({ ...prev, resolved: prev.resolved + 1 }));
      } else if (result.incident_status === 'escalated') {
        setSessionStats(prev => ({ ...prev, escalated: prev.escalated + 1 }));
      } else {
        setSessionStats(prev => ({ ...prev, abandoned: prev.abandoned + 1 }));
      }

      // Clear current incident
      setCurrentIncident(null);
      setTimeRemaining(0);

      // Schedule next incident after showing grading
      setTimeout(() => {
        setShowGradingModal(false);
        setResolutionResult(null);
        
        // Check if workday is complete
        if (incidentCount >= (workdaySession?.incidents_scheduled || 8)) {
          // Enter monitoring mode instead of completing
          enterMonitoringMode();
        } else {
          // Schedule next incident with random delay
          scheduleNextIncident();
        }
      }, 5000); // Show grading for 5 seconds
      
    } catch (error) {
      console.error('Failed to resolve incident:', error);
    } finally {
      setIsResolving(false);
    }
  };

  const enterMonitoringMode = () => {
    setSimulationStatus('monitoring');
    setIsMonitoringMode(true);
    // Schedule a random incident for monitoring mode (could be hours away)
    scheduleNextIncident();
  };

  const completeWorkdaySimulation = async () => {
    try {
      setSimulationStatus('completed');
      setIsMonitoringMode(false);
      await simulationAPI.completeWorkdaySimulation(workdaySession?.id || '');
    } catch (error) {
      console.error('Failed to complete workday simulation:', error);
    }
  };

  const goBackToDashboard = () => {
    router.push('/dashboard');
  };

  const formatTimeRemaining = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!company) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <XCircle className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Loading Error</h3>
          <p className="mt-1 text-sm text-gray-500">Failed to load company data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-sm text-gray-500 hover:text-gray-700 mr-4"
              >
                ← Back to Dashboard
              </button>
              <div className="h-8 w-8 flex items-center justify-center rounded-full bg-blue-100">
                <span className="text-lg font-bold text-blue-600">L</span>
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-bold text-gray-900">{company.name}</h1>
                <p className="text-sm text-gray-600">Workday Simulation (9 AM - 5 PM)</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {/* Current Rating Display */}
              <div className="flex items-center px-3 py-2 bg-blue-50 rounded-md">
                <span className="text-sm font-medium text-blue-700">Rating:</span>
                <span className="ml-2 text-lg font-bold text-blue-900">{currentUserRating}</span>
              </div>
              
              {/* Simulation Status */}
              <div className="flex items-center px-3 py-2 bg-gray-50 rounded-md">
                <Calendar className="h-4 w-4 mr-2 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">
                  {simulationStatus === 'idle' && 'Starting...'}
                  {simulationStatus === 'waiting' && 'Waiting for incident...'}
                  {simulationStatus === 'active' && 'Active incident'}
                  {simulationStatus === 'monitoring' && 'Monitoring mode'}
                  {simulationStatus === 'completed' && 'Workday complete!'}
                </span>
              </div>
              
              <button
                onClick={goBackToDashboard}
                className="flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Square className="h-4 w-4 mr-2" />
                End Simulation
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Workday Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Workday Progress</h2>
                <div className="text-sm text-gray-500">
                  Incident {incidentCount} of {workdaySession?.incidents_scheduled || 8}
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 bg-green-50 rounded">
                  <div className="text-2xl font-bold text-green-600">{sessionStats.resolved}</div>
                  <div className="text-sm text-green-700">Resolved</div>
                </div>
                <div className="text-center p-3 bg-yellow-50 rounded">
                  <div className="text-2xl font-bold text-yellow-600">{sessionStats.escalated}</div>
                  <div className="text-sm text-yellow-700">Escalated</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded">
                  <div className="text-2xl font-bold text-red-600">{sessionStats.abandoned}</div>
                  <div className="text-sm text-red-700">Abandoned</div>
                </div>
              </div>

              {/* Next Incident Timer */}
              {simulationStatus === 'waiting' && timeUntilNext > 0 && (
                <div className="text-center p-4 bg-blue-50 rounded">
                  <Timer className="h-6 w-6 mx-auto text-blue-600 mb-2" />
                  <div className="text-lg font-semibold text-blue-700">
                    Next incident in: {formatTimeRemaining(timeUntilNext)}
                  </div>
                  <div className="text-sm text-blue-600 mt-1">
                    {isMonitoringMode 
                      ? "Stay alert! Incidents can appear at any moment during monitoring mode."
                      : "Take a break! Incidents come randomly throughout the workday."
                    }
                  </div>
                </div>
              )}

              {simulationStatus === 'monitoring' && (
                <div className="text-center p-4 bg-yellow-50 rounded border-2 border-yellow-200">
                  <AlertTriangle className="h-6 w-6 mx-auto text-yellow-600 mb-2" />
                  <div className="text-lg font-semibold text-yellow-700">
                    You are finished with incidents right now, BUT please stay alert for one that can come up any moment!!!
                  </div>
                  <div className="text-sm text-yellow-600 mt-1">
                    Monitoring mode active - incidents can appear randomly from seconds to hours.
                  </div>
                  {timeUntilNext > 0 && (
                    <div className="mt-2 text-sm font-medium text-yellow-800">
                      Next potential incident in: {formatTimeRemaining(timeUntilNext)}
                    </div>
                  )}
                </div>
              )}

              {simulationStatus === 'completed' && (
                <div className="text-center p-4 bg-green-50 rounded">
                  <CheckCircle className="h-6 w-6 mx-auto text-green-600 mb-2" />
                  <div className="text-lg font-semibold text-green-700">
                    Workday Complete! 🎉
                  </div>
                  <div className="text-sm text-green-600 mt-1">
                    Great job handling all the incidents today.
                  </div>
                </div>
              )}
            </div>

            {/* Current Incident */}
            {currentIncident ? (
              <>
                {/* Incident Header */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <AlertTriangle className="h-6 w-6 text-red-500 mr-3" />
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">
                          {currentIncident.title}
                        </h2>
                        <div className="flex items-center mt-1">
                          <span
                            className={cn(
                              'text-sm font-medium px-2 py-1 rounded-full border',
                              getSeverityColor(currentIncident.severity)
                            )}
                          >
                            {currentIncident.severity}
                          </span>
                          <span className="ml-2 text-sm text-gray-500">
                            {getSeverityLabel(currentIncident.severity)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">
                        Time Limit: {currentIncident.time_limit_minutes} minutes
                      </div>
                      {timeRemaining > 0 && (
                        <div className={cn(
                          "text-lg font-bold",
                          timeRemaining < 60 ? "text-red-600" : 
                          timeRemaining < 300 ? "text-yellow-600" : 
                          "text-green-600"
                        )}>
                          {formatTimeRemaining(timeRemaining)}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="prose max-w-none">
                    <p className="text-gray-700 mb-4">{currentIncident.description}</p>
                  </div>

                  {/* Affected Services */}
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-gray-900 mb-2">Affected Services</h3>
                    <div className="flex flex-wrap gap-2">
                      {currentIncident.affected_services.map((service, index) => (
                        <span
                          key={index}
                          className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded"
                        >
                          {service}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Error Logs */}
                  {currentIncident.error_logs && (
                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-900 mb-2">Error Logs</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                        {currentIncident.error_logs}
                      </pre>
                    </div>
                  )}

                  {/* Codebase Context */}
                  {currentIncident.codebase_context && (
                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-900 mb-2">Codebase Context</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                        {currentIncident.codebase_context}
                      </pre>
                    </div>
                  )}

                  {/* Monitoring Dashboard */}
                  {currentIncident.monitoring_dashboard_url && (
                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-900 mb-2">Monitoring Dashboard</h3>
                      <a
                        href={currentIncident.monitoring_dashboard_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        View Dashboard →
                      </a>
                    </div>
                  )}
                </div>

                {/* Resolution Form */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Resolution</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Resolution Approach
                      </label>
                      <textarea
                        value={resolutionApproach}
                        onChange={(e) => setResolutionApproach(e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Describe your approach to resolving this incident..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Solution Type
                      </label>
                      <select
                        value={solutionType}
                        onChange={(e) => setSolutionType(e.target.value as any)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="root_cause">Root Cause Fix</option>
                        <option value="workaround">Workaround</option>
                        <option value="escalation">Escalation</option>
                        <option value="abandonment">Abandonment</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex space-x-4 mt-6">
                    <button
                      onClick={() => handleResolveIncident(true)}
                      disabled={isResolving}
                      className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Resolve Successfully
                    </button>
                    <button
                      onClick={() => handleResolveIncident(false)}
                      disabled={isResolving}
                      className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Escalate/Abandon
                    </button>
                  </div>
                </div>
              </>
            ) : simulationStatus === 'waiting' ? (
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <Timer className="mx-auto h-12 w-12 text-blue-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Waiting for Next Incident</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {isMonitoringMode 
                    ? "Monitoring mode - incidents can appear at any moment!"
                    : "Incidents appear randomly throughout the workday. Take a break!"
                  }
                </p>
                {timeUntilNext > 0 && (
                  <div className="mt-4 text-lg font-semibold text-blue-600">
                    Next incident in: {formatTimeRemaining(timeUntilNext)}
                  </div>
                )}
              </div>
            ) : simulationStatus === 'monitoring' ? (
              <div className="bg-white rounded-lg shadow p-6 text-center border-2 border-yellow-200">
                <AlertTriangle className="mx-auto h-12 w-12 text-yellow-500" />
                <h3 className="mt-2 text-lg font-semibold text-yellow-700">Monitoring Mode Active</h3>
                <p className="mt-2 text-sm text-gray-600">
                  You are finished with incidents right now, BUT please stay alert for one that can come up any moment!!!
                </p>
                <div className="mt-4 p-3 bg-yellow-50 rounded">
                  <p className="text-sm text-yellow-800">
                    Incidents can appear randomly from seconds to hours. Stay vigilant!
                  </p>
                  {timeUntilNext > 0 && (
                    <div className="mt-2 text-sm font-medium text-yellow-900">
                      Next potential incident in: {formatTimeRemaining(timeUntilNext)}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => completeWorkdaySimulation()}
                  className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  End Monitoring & Complete Workday
                </button>
              </div>
            ) : simulationStatus === 'completed' ? (
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <CheckCircle className="mx-auto h-12 w-12 text-green-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Workday Complete!</h3>
                <p className="mt-1 text-sm text-gray-500">
                  You've successfully handled all incidents for today.
                </p>
                <button
                  onClick={goBackToDashboard}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Return to Dashboard
                </button>
              </div>
            ) : null}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Company Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Info</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Company</span>
                  <span className="text-sm font-medium text-gray-900">{company.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Industry</span>
                  <span className="text-sm font-medium text-gray-900">{company.industry}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Size</span>
                  <span className="text-sm font-medium text-gray-900">{company.company_size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Status</span>
                  <span className="text-sm font-medium text-green-600">Active</span>
                </div>
              </div>
            </div>

            {/* Tech Stack */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tech Stack</h3>
              <div className="flex flex-wrap gap-2">
                {company.tech_stack.map((tech, index) => (
                  <span
                    key={index}
                    className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            {/* Workday Tips */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Workday Tips</h3>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-start">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                  <span>Incidents appear randomly from seconds to hours</span>
                </div>
                <div className="flex items-start">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                  <span>After scheduled incidents, monitoring mode keeps you alert</span>
                </div>
                <div className="flex items-start">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                  <span>Focus on quality over speed for better ratings</span>
                </div>
                <div className="flex items-start">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                  <span>Stay vigilant - incidents can come at any moment!</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Groq Grading Modal */}
      {showGradingModal && resolutionResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Incident Resolution Grading</h2>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-sm text-gray-500">Groq Score</div>
                    <div className="text-3xl font-bold text-blue-600">
                      {resolutionResult.groq_grading.score}/100
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-500">Rating Change</div>
                    <div className={cn(
                      "text-2xl font-bold",
                      resolutionResult.rating_change >= 0 ? "text-green-600" : "text-red-600"
                    )}>
                      {resolutionResult.rating_change >= 0 ? "+" : ""}{resolutionResult.rating_change}
                    </div>
                  </div>
                </div>
              </div>

              {/* Score Quality Indicator */}
              <div className="mb-6">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-2">Quality Assessment</div>
                  <div className={cn(
                    "text-2xl font-bold",
                    resolutionResult.groq_grading.score >= 80 ? "text-green-600" :
                    resolutionResult.groq_grading.score >= 50 ? "text-yellow-600" : "text-red-600"
                  )}>
                    {resolutionResult.groq_grading.score >= 80 ? "Excellent" :
                     resolutionResult.groq_grading.score >= 50 ? "Good" : "Needs Improvement"}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {resolutionResult.groq_grading.grading_method === 'groq' ? 'Graded by Groq AI' : 'Fallback Grading'}
                  </div>
                </div>
              </div>

              {/* Feedback */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Instructor Feedback</h3>
                  <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                    <p className="text-gray-700 leading-relaxed">
                      {resolutionResult.groq_grading.feedback}
                    </p>
                  </div>
                </div>

                {/* Performance Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded">
                    <h4 className="font-semibold text-gray-900 mb-2">Performance Summary</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Time Spent:</span>
                        <span className="font-medium">{resolutionResult.time_spent_minutes} minutes</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">New Rating:</span>
                        <span className="font-medium">{resolutionResult.new_overall_rating}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Status:</span>
                        <span className={cn(
                          "font-medium",
                          resolutionResult.incident_status === 'resolved' ? "text-green-600" : "text-red-600"
                        )}>
                          {resolutionResult.incident_status}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded">
                    <h4 className="font-semibold text-gray-900 mb-2">Rating Impact</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Change:</span>
                        <span className={cn(
                          "font-medium",
                          resolutionResult.rating_change >= 0 ? "text-green-600" : "text-red-600"
                        )}>
                          {resolutionResult.rating_change >= 0 ? "+" : ""}{resolutionResult.rating_change}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Quality Score:</span>
                        <span className="font-medium">{resolutionResult.groq_grading.score}/100</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="text-center text-sm text-gray-500">
                  {isMonitoringMode 
                    ? "Next incident could appear at any moment - stay alert!"
                    : "Next incident will appear in a few seconds..."
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
