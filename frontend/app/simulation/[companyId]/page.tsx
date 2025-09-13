'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { companyAPI, simulationAPI } from '@/lib/api';
import { AlertTriangle, Clock, Code, Terminal, CheckCircle, XCircle, Loader2, Play, Square } from 'lucide-react';
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

interface SimulationSession {
  session_id: string;
  company: {
    id: number;
    name: string;
    slug: string;
  };
  scheduled_duration_hours: number;
  started_at: string;
  incident_schedule: any[];
  total_incidents_planned: number;
}

export default function SimulationPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const companyId = params.companyId as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [session, setSession] = useState<SimulationSession | null>(null);
  const [currentIncident, setCurrentIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSimulationActive, setIsSimulationActive] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [resolutionApproach, setResolutionApproach] = useState('');
  const [codeChanges, setCodeChanges] = useState('');
  const [commandsExecuted, setCommandsExecuted] = useState<string[]>([]);
  const [newCommand, setNewCommand] = useState('');
  const [solutionType, setSolutionType] = useState<'root_cause' | 'workaround' | 'escalation' | 'abandonment'>('workaround');
  const [isResolving, setIsResolving] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchCompanyAndStartSimulation();
  }, [companyId, isAuthenticated, router]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isSimulationActive && currentIncident && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            // Time's up - auto-escalate
            handleResolveIncident(true, 'escalation');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isSimulationActive, currentIncident, timeRemaining]);

  const fetchCompanyAndStartSimulation = async () => {
    try {
      // Fetch company details
      const companyResponse = await companyAPI.getCompany(parseInt(companyId));
      setCompany(companyResponse);

      // Start simulation
      const sessionResponse = await simulationAPI.startSimulation(parseInt(companyId), 8);
      setSession(sessionResponse);
      setIsSimulationActive(true);

      // Generate first incident
      await generateNewIncident();
    } catch (error) {
      console.error('Failed to start simulation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateNewIncident = async () => {
    if (!session) return;

    try {
      const incidentResponse = await simulationAPI.generateIncident(session.session_id);
      setCurrentIncident(incidentResponse);
      setTimeRemaining(incidentResponse.time_limit_minutes * 60); // Convert to seconds
      setResolutionApproach('');
      setCodeChanges('');
      setCommandsExecuted([]);
      setNewCommand('');
      setSolutionType('workaround');
    } catch (error) {
      console.error('Failed to generate incident:', error);
    }
  };

  const addCommand = () => {
    if (newCommand.trim()) {
      setCommandsExecuted(prev => [...prev, newCommand.trim()]);
      setNewCommand('');
    }
  };

  const handleResolveIncident = async (wasSuccessful: boolean, type?: 'root_cause' | 'workaround' | 'escalation' | 'abandonment') => {
    if (!currentIncident || !session || isResolving) return;

    setIsResolving(true);
    try {
      const resolutionType = type || solutionType;
      await simulationAPI.resolveIncident({
        incidentId: currentIncident.incident_id,
        sessionId: session.session_id,
        resolutionApproach,
        codeChanges,
        commandsExecuted,
        solutionType: resolutionType,
        wasSuccessful,
      });

      // Generate next incident or end simulation
      await generateNewIncident();
    } catch (error) {
      console.error('Failed to resolve incident:', error);
    } finally {
      setIsResolving(false);
    }
  };

  const endSimulation = async () => {
    if (!session) return;

    try {
      await simulationAPI.endSimulation(session.session_id);
      router.push('/dashboard');
    } catch (error) {
      console.error('Failed to end simulation:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!company || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <XCircle className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Simulation Error</h3>
          <p className="mt-1 text-sm text-gray-500">Failed to load simulation data.</p>
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
                <p className="text-sm text-gray-600">On-Call Simulation</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={endSimulation}
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
          {/* Incident Details */}
          <div className="lg:col-span-2 space-y-6">
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
                      <div className="flex items-center text-lg font-semibold text-red-600">
                        <Clock className="h-5 w-5 mr-2" />
                        {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
                      </div>
                      <p className="text-sm text-gray-500">Time Remaining</p>
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
                        Code Changes
                      </label>
                      <textarea
                        value={codeChanges}
                        onChange={(e) => setCodeChanges(e.target.value)}
                        rows={6}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                        placeholder="Describe any code changes made..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Commands Executed
                      </label>
                      <div className="space-y-2">
                        {commandsExecuted.map((cmd, index) => (
                          <div key={index} className="flex items-center bg-gray-100 p-2 rounded">
                            <Terminal className="h-4 w-4 text-gray-500 mr-2" />
                            <code className="text-sm flex-1">{cmd}</code>
                          </div>
                        ))}
                        <div className="flex">
                          <input
                            type="text"
                            value={newCommand}
                            onChange={(e) => setNewCommand(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && addCommand()}
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                            placeholder="Enter command..."
                          />
                          <button
                            onClick={addCommand}
                            className="px-3 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700"
                          >
                            Add
                          </button>
                        </div>
                      </div>
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
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <Play className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No Active Incident</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Waiting for the next incident to occur...
                </p>
                <button
                  onClick={generateNewIncident}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Generate Incident
                </button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Session Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Session Info</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Company</span>
                  <span className="text-sm font-medium text-gray-900">{company.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Duration</span>
                  <span className="text-sm font-medium text-gray-900">
                    {session.scheduled_duration_hours}h
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Planned Incidents</span>
                  <span className="text-sm font-medium text-gray-900">
                    {session.total_incidents_planned}
                  </span>
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

            {/* Company Details */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Details</h3>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-600">Industry</span>
                  <p className="text-sm font-medium text-gray-900">{company.industry}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Size</span>
                  <p className="text-sm font-medium text-gray-900">{company.company_size}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Description</span>
                  <p className="text-sm text-gray-700">{company.description}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
