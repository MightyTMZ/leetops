'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { ratingAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Star, TrendingUp, Clock, Target, Award, BarChart3, Loader2 } from 'lucide-react';
import { cn, formatRating, formatTime } from '@/lib/utils';

interface UserRating {
  user_id: number;
  email: string;
  overall_rating: number;
  rating_category: string;
  rating_percentile: number;
  rating_range: {
    min: number;
    max: number;
  };
  points_to_next_category: number;
  skill_ratings: {
    debugging_skill: number;
    system_design: number;
    incident_response: number;
    communication: number;
  };
  statistics: {
    total_incidents_resolved: number;
    average_resolution_time: number;
    success_rate: number;
  };
  recent_performance: {
    trend: 'up' | 'down' | 'stable';
    recent_incidents: number;
    average_points: number;
  };
}

export default function RatingPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [rating, setRating] = useState<UserRating | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchUserRating();
  }, [isAuthenticated, router]);

  const fetchUserRating = async () => {
    try {
      const response = await ratingAPI.getUserRating();
      setRating(response);
    } catch (err) {
      setError('Failed to load rating data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 1400) return 'text-purple-600 bg-purple-50 border-purple-200';
    if (rating >= 1200) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (rating >= 1000) return 'text-green-600 bg-green-50 border-green-200';
    if (rating >= 800) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getSkillColor = (skill: string, value: number) => {
    const percentage = ((value - 800) / 800) * 100;
    if (percentage >= 75) return 'bg-green-500';
    if (percentage >= 50) return 'bg-blue-500';
    if (percentage >= 25) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
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
              <button
                onClick={() => router.push('/dashboard')}
                className="text-sm text-gray-500 hover:text-gray-700 mr-4"
              >
                ← Back to Dashboard
              </button>
              <div className="h-8 w-8 flex items-center justify-center rounded-full bg-blue-100">
                <span className="text-lg font-bold text-blue-600">L</span>
              </div>
              <h1 className="ml-3 text-2xl font-bold text-gray-900">LeetOps Rating</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Your Engineering Credibility</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
            </div>
          </div>
        )}

        {rating && (
          <div className="space-y-8">
            {/* Overall Rating Card */}
            <div className="bg-white rounded-lg shadow p-8">
              <div className="text-center">
                <div className="flex items-center justify-center mb-4">
                  <Award className="h-8 w-8 text-blue-600 mr-3" />
                  <h2 className="text-3xl font-bold text-gray-900">Your LeetOps Rating</h2>
                </div>
                
                <div className="mb-6">
                  <div className="text-6xl font-bold text-blue-600 mb-2">
                    {rating.overall_rating}
                  </div>
                  <div
                    className={cn(
                      'inline-flex items-center px-4 py-2 rounded-full border text-lg font-semibold',
                      getRatingColor(rating.overall_rating)
                    )}
                  >
                    <Star className="h-5 w-5 mr-2" />
                    {formatRating(rating.overall_rating)}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-gray-900">
                      {rating.rating_percentile}%
                    </div>
                    <div className="text-sm text-gray-600">Percentile</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-gray-900">
                      {rating.points_to_next_category}
                    </div>
                    <div className="text-sm text-gray-600">Points to Next Level</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-gray-900">
                      {rating.rating_range.min}-{rating.rating_range.max}
                    </div>
                    <div className="text-sm text-gray-600">Rating Range</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Statistics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Target className="h-8 w-8 text-green-600 mr-3" />
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {rating.statistics.total_incidents_resolved}
                    </div>
                    <div className="text-sm text-gray-600">Incidents Resolved</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Clock className="h-8 w-8 text-blue-600 mr-3" />
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {formatTime(rating.statistics.average_resolution_time)}
                    </div>
                    <div className="text-sm text-gray-600">Avg Resolution Time</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-purple-600 mr-3" />
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {rating.statistics.success_rate.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">Success Rate</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Skill Ratings */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center mb-6">
                <BarChart3 className="h-6 w-6 text-gray-600 mr-3" />
                <h3 className="text-xl font-semibold text-gray-900">Skill Breakdown</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(rating.skill_ratings).map(([skill, value]) => (
                  <div key={skill} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {skill.replace('_', ' ')}
                      </span>
                      <span className="text-sm font-semibold text-gray-900">{value}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={cn('h-2 rounded-full transition-all duration-300', getSkillColor(skill, value))}
                        style={{ width: `${((value - 800) / 800) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Performance */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center mb-6">
                <TrendingUp className="h-6 w-6 text-gray-600 mr-3" />
                <h3 className="text-xl font-semibold text-gray-900">Recent Performance</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-semibold text-gray-900">
                    {rating.recent_performance.recent_incidents}
                  </div>
                  <div className="text-sm text-gray-600">Recent Incidents</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-semibold text-gray-900">
                    {rating.recent_performance.average_points.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Avg Points</div>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center">
                    <TrendingUp
                      className={cn('h-6 w-6 mr-2', {
                        'text-green-600': rating.recent_performance.trend === 'up',
                        'text-red-600': rating.recent_performance.trend === 'down',
                        'text-gray-600': rating.recent_performance.trend === 'stable',
                      })}
                    />
                    <span
                      className={cn('text-lg font-semibold', {
                        'text-green-600': rating.recent_performance.trend === 'up',
                        'text-red-600': rating.recent_performance.trend === 'down',
                        'text-gray-600': rating.recent_performance.trend === 'stable',
                      })}
                    >
                      {rating.recent_performance.trend === 'up' ? 'Improving' : 
                       rating.recent_performance.trend === 'down' ? 'Declining' : 'Stable'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">Trend</div>
                </div>
              </div>
            </div>

            {/* Call to Action */}
            <div className="bg-blue-50 rounded-lg p-6 text-center">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Ready for Your Next Challenge?
              </h3>
              <p className="text-blue-700 mb-4">
                Continue practicing to improve your rating and engineering skills.
              </p>
              <button
                onClick={() => router.push('/dashboard')}
                className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
              >
                Start New Simulation
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
