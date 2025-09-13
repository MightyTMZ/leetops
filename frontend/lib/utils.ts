import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
}

export function formatRating(rating: number): string {
  if (rating >= 1400) return 'Expert';
  if (rating >= 1200) return 'Advanced';
  if (rating >= 1000) return 'Intermediate';
  if (rating >= 800) return 'Beginner';
  return 'Novice';
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'P0':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'P1':
      return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'P2':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'P3':
      return 'text-blue-600 bg-blue-50 border-blue-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}

export function getSeverityLabel(severity: string): string {
  switch (severity) {
    case 'P0':
      return 'Critical - Service Down';
    case 'P1':
      return 'High - Major Impact';
    case 'P2':
      return 'Medium - Minor Impact';
    case 'P3':
      return 'Low - Cosmetic Issue';
    default:
      return 'Unknown';
  }
}

export function getCompanySizeColor(size: string): string {
  switch (size.toLowerCase()) {
    case 'startup':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'mid-size':
      return 'text-blue-600 bg-blue-50 border-blue-200';
    case 'large':
      return 'text-purple-600 bg-purple-50 border-purple-200';
    case 'enterprise':
      return 'text-gray-600 bg-gray-50 border-gray-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}
