'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { companyAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Building2, Users, Clock, Star, ArrowRight, Loader2 } from 'lucide-react';
import { cn, getCompanySizeColor } from '@/lib/utils';
import Image from 'next/image';

interface Company {
  id: number;
  name: string;
  slug: string;
  description: string;
  avatar?: string;
  industry: string;
  company_size: string;
  tech_stack: string[];
  focus_areas: string[];
  incident_frequency: number;
  severity_distribution: Record<string, number>;
  statistics?: {
    total_simulation_sessions: number;
    average_rating: number;
  };
}

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }

    if (isAuthenticated) {
      fetchCompanies();
    }
  }, [isAuthenticated, authLoading, router]);

  const fetchCompanies = async () => {
    try {
      const response = await companyAPI.getCompanies();
      setCompanies(response.companies);
    } catch (err) {
      setError('Failed to load companies. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCompanySelect = (companyId: number) => {
    router.push(`/simulation/${companyId}`);
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="h-8 w-8 flex items-center justify-center rounded-full bg-blue-100">
                <span className="text-lg font-bold text-blue-600">L</span>
              </div>
              <h1 className="ml-3 text-2xl font-bold text-gray-900">LeetOps</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.email}
              </span>
              <button
                onClick={() => {
                  localStorage.removeItem('access_token');
                  localStorage.removeItem('refresh_token');
                  window.location.href = '/login';
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Choose Your Company
          </h2>
          <p className="text-lg text-gray-600">
            Select a company to start your on-call engineering simulation
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
            </div>
          </div>
        )}

        {/* Company Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {companies.map((company) => (
            <div
              key={company.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleCompanySelect(company.id)}
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="h-10 w-10 flex items-center justify-center rounded-full bg-gray-100">
                      {company.avatar && <Image src={`http://127.0.0.1:8000/${company.avatar}`} alt={company.name} height={50} width={50}/>}
                    </div>
                    <h3 className="ml-3 text-lg font-semibold text-gray-900">
                      {company.name}
                    </h3>
                  </div>
                  <ArrowRight className="h-5 w-5 text-gray-400" />
                </div>

                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {company.description}
                </p>

                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Industry</span>
                    <span className="text-xs font-medium text-gray-900">
                      {company.industry}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Size</span>
                    <span
                      className={cn(
                        'text-xs font-medium px-2 py-1 rounded-full border',
                        getCompanySizeColor(company.company_size)
                      )}
                    >
                      {company.company_size}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Incident Rate</span>
                    <span className="text-xs font-medium text-gray-900">
                      {company.incident_frequency.toFixed(1)}/hour
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1 mb-4">
                  {company.tech_stack.slice(0, 3).map((tech, index) => (
                    <span
                      key={index}
                      className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                    >
                      {tech}
                    </span>
                  ))}
                  {company.tech_stack.length > 3 && (
                    <span className="text-xs text-gray-500">
                      +{company.tech_stack.length - 3} more
                    </span>
                  )}
                </div>

                {company.statistics && (
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center">
                      <Users className="h-3 w-3 mr-1" />
                      {company.statistics.total_simulation_sessions} sessions
                    </div>
                    <div className="flex items-center">
                      <Star className="h-3 w-3 mr-1" />
                      Avg: {company.statistics.average_rating}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {companies.length === 0 && !loading && (
          <div className="text-center py-12">
            <Building2 className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No companies available</h3>
            <p className="mt-1 text-sm text-gray-500">
              Companies will appear here once they're loaded.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
