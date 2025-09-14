"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  ArrowRight,
  Shield,
  Clock,
  Target,
  Users,
  Building2,
  Star,
} from "lucide-react";
import Image from "next/image";
import LeetOpsLogo from "@/components/LeetOpsLogo";
import { currentYear } from "@/data/constants";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-orange-gradient">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              {/* <div className="h-8 w-8 flex items-center justify-center rounded-full bg-blue-100">
                <span className="text-lg font-bold text-blue-600">L</span>
              </div>
              <h1 className="ml-3 text-xl font-bold text-gray-900">LeetOps</h1> */}
              <LeetOpsLogo />
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="/login"
                className="text-sm text-gray-600 hover:text-orange-900"
              >
                Sign In
              </a>
              <a
                href="/register"
                className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 text-sm font-medium"
              >
                Get Started
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            The New Currency of
            <span className="text-orange-600"> Engineering Credibility</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            LeetOps is the standardized benchmark for on-call engineering
            reliability. Practice real-world incident response scenarios at <strong>top
            tech companies </strong> and prove your production skills.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/register"
              className="px-8 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium text-lg flex items-center justify-center"
            >
              Start Practicing
              <ArrowRight className="ml-2 h-5 w-5" />
            </a>
            <a
              href="#how-it-works"
              className="px-8 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium text-lg"
            >
              Learn More
            </a>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div id="how-it-works" className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Incidents don’t wait. Neither should you.
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Experience realistic on-call scenarios that mirror real-world
              engineering challenges
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="h-16 w-100vw rounded-full flex items-center justify-center mx-auto mb-4 overflow-hidden">
                <div className="flex animate-slide">
                  {[
                    "/logos/amzn.jpg",
                    "/logos/bloomberg.jpg",
                    "/logos/coinbase.png",
                    "/logos/federato.jpg",
                    "/logos/google.png",
                    "/logos/intact.png",
                    "/logos/meta.png",
                    "/logos/rbc.png",
                    "/logos/rox.jpg",
                    "/logos/shopify.png",
                    "/logos/td.webp",
                    "/logos/uber_logo.png",
                  ].map((image, n) => (
                    <div key={n} className="flex-shrink-0 mx-1">
                      <Image
                        src={image}
                        height={50}
                        width={50}
                        alt="Company Logo"
                        className="rounded-full"
                      />
                    </div>
                  ))}
                  {/* Duplicate the logos for seamless loop */}
                  {[
                    "/logos/amzn.jpg",
                    "/logos/bloomberg.jpg",
                    "/logos/coinbase.png",
                    "/logos/federato.jpg",
                    "/logos/google.png",
                    "/logos/intact.png",
                    "/logos/meta.png",
                    "/logos/rbc.png",
                    "/logos/rox.jpg",
                    "/logos/shopify.png",
                    "/logos/td.webp",
                    "/logos/uber_logo.png",
                  ].map((image, n) => (
                    <div key={`duplicate-${n}`} className="flex-shrink-0 mx-1">
                      <Image
                        src={image}
                        height={50}
                        width={50}
                        alt="Company Logo"
                        className="rounded-full"
                      />
                    </div>
                  ))}
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Choose Your Company
              </h3>
              <p className="text-gray-600">
                Select from top tech companies like Google, Amazon, Shopify, and
                more. Each company has unique tech stacks and incident patterns.
              </p>
            </div>

            <div className="text-center">
              <div className="h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Handle Real Incidents
              </h3>
              <p className="text-gray-600">
                Respond to realistic incidents with actual error logs,
                monitoring dashboards, and codebase context. The clock is always
                ticking.
              </p>
            </div>

            <div className="text-center">
              <div className="h-16 w-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Star className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Build Your Rating
              </h3>
              <p className="text-gray-600">
                Earn points based on resolution speed, solution quality, and
                approach. Your LeetOps rating becomes your engineering
                credibility score.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      {/* <div className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">40+</div>
              <div className="text-gray-600">Companies</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600 mb-2">1000+</div>
              <div className="text-gray-600">Engineers</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">50k+</div>
              <div className="text-gray-600">Incidents Resolved</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-orange-600 mb-2">95%</div>
              <div className="text-gray-600">Success Rate</div>
            </div>
          </div>
        </div>
      </div> */}

      {/* CTA Section */}
      {/* <div className="bg-blue-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Prove Your Engineering Skills?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of engineers who are building their credibility through 
            realistic on-call simulations.
          </p>
          <a
            href="/register"
            className="px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-gray-100 font-medium text-lg inline-flex items-center"
          >
            Start Your Journey
            <ArrowRight className="ml-2 h-5 w-5" />
          </a>
        </div>
      </div> */}

      {/* Footer */}
      <footer className="bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-400">
            <p>
              &copy; {currentYear} LeetOps. The standardized benchmark for on-call
              engineering reliability.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
