'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { companyAPI, simulationAPI } from '@/lib/api';
import { AlertTriangle, Clock, Code, Terminal, CheckCircle, XCircle, Loader2, Play, Square } from 'lucide-react';
import { cn, formatTime, getSeverityColor, getSeverityLabel } from '@/lib/utils';
import LeetOpsLogo from '@/components/LeetOpsLogo';

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

export default function SimulationPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const companyId = params.companyId as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [currentIncident, setCurrentIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [resolutionApproach, setResolutionApproach] = useState('');
  const [codeChanges, setCodeChanges] = useState('');
  const [commandsExecuted, setCommandsExecuted] = useState<string[]>([]);
  const [newCommand, setNewCommand] = useState('');
  const [solutionType, setSolutionType] = useState<'root_cause' | 'workaround' | 'escalation' | 'abandonment'>('workaround');
  const [isResolving, setIsResolving] = useState(false);
  const [resolutionResult, setResolutionResult] = useState<ResolutionResult | null>(null);
  const [showGradingModal, setShowGradingModal] = useState(false);
  const [currentUserRating, setCurrentUserRating] = useState(800);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchCompanyAndIncidents();
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

  const fetchCompanyAndIncidents = async () => {
    try {
      // Fetch company details
      const companyResponse = await companyAPI.getCompany(parseInt(companyId));
      setCompany(companyResponse);

      // Fetch incidents for this company
      await fetchIncidents();
    } catch (error) {
      console.error('Failed to load company and incidents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchIncidents = async () => {
    try {
      const incidentsResponse = await companyAPI.getCompanyIncidents(parseInt(companyId));
      const incidents = incidentsResponse.incidents;
      
      if (incidents && incidents.length > 0) {
        // Get the first active incident
        const activeIncident = incidents[0];
        setCurrentIncident(activeIncident);
        setTimeRemaining(activeIncident.time_limit_minutes * 60); // Convert to seconds
        setResolutionApproach('');
        setCodeChanges('');
        setCommandsExecuted([]);
        setNewCommand('');
        setSolutionType('workaround');
      } else {
        setCurrentIncident(null);
        setTimeRemaining(0);
      }
    } catch (error) {
      console.error('Failed to fetch incidents:', error);
      setCurrentIncident(null);
    }
  };

  const addCommand = () => {
    if (newCommand.trim()) {
      setCommandsExecuted(prev => [...prev, newCommand.trim()]);
      setNewCommand('');
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
        codeChanges,
        commandsExecuted,
        solutionType: resolutionType,
        wasSuccessful,
      });

      // Store the resolution result with LLM grading
      setResolutionResult(result);
      setCurrentUserRating(result.new_overall_rating);
      setShowGradingModal(true);
    } catch (error) {
      console.error('Failed to resolve incident:', error);
    } finally {
      setIsResolving(false);
    }
  };

  const goBackToDashboard = () => {
    router.push('/dashboard');
  };

  const handleCloseGradingModal = async () => {
    setShowGradingModal(false);
    setResolutionResult(null);
    await fetchIncidents();
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
    <div className="min-h-screen bg-orange-gradient">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm shadow-lg border-b border-orange-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-sm text-gray-500 hover:text-gray-700 mr-4"
              >
                ← Back to Dashboard
              </button>
              <LeetOpsLogo size={32} />
              <div className="ml-3">
                <h1 className="text-xl font-bold text-gray-900">{company.name}</h1>
                <p className="text-sm text-orange-primary">On-Call Simulation</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {/* Current Rating Display */}
              <div className="flex items-center px-3 py-2 bg-orange-light rounded-md border border-orange-200">
                <span className="text-sm font-medium text-orange-primary">Rating:</span>
                <span className="ml-2 text-lg font-bold text-orange-primary">{currentUserRating}</span>
              </div>
              
              {/* Timer Display */}
              {currentIncident && timeRemaining > 0 && (
                <div className={cn(
                  "flex items-center px-3 py-2 rounded-md font-bold text-lg",
                  timeRemaining < 60 ? "bg-red-100 text-red-700" : 
                  timeRemaining < 300 ? "bg-yellow-100 text-yellow-700" : 
                  "bg-green-100 text-green-700"
                )}>
                  <Clock className="h-5 w-5 mr-2" />
                  {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
                </div>
              )}
              
              <button
                onClick={goBackToDashboard}
                className="flex items-center px-3 py-2 border border-orange-300 rounded-md text-sm font-medium text-orange-primary bg-white hover:bg-orange-light"
              >
                <Square className="h-4 w-4 mr-2" />
                Back to Dashboard
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
                      <div className="text-sm text-gray-500">
                        Time Limit: {currentIncident.time_limit_minutes} minutes
                      </div>
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

                    {/* <div>
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
                    </div> */}

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
                  onClick={fetchIncidents}
                  className="mt-4 px-4 py-2 bg-orange-primary text-white rounded-md hover:bg-orange-primary/90"
                >
                  Refresh Incidents
                </button>
              </div>
            )}
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
                  <button
                    onClick={handleCloseGradingModal}
                    className="ml-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                    title="Close grading modal"
                  >
                    <XCircle className="h-6 w-6" />
                  </button>
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
                <div className="text-center">
                  <button
                    onClick={handleCloseGradingModal}
                    className="px-6 py-2 bg-orange-primary text-white rounded-md hover:bg-orange-primary/90 transition-colors"
                  >
                    Continue to Next Incident
                  </button>
                  <div className="text-sm text-gray-500 mt-2">
                    Click the button above or the X in the top-right to continue
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
