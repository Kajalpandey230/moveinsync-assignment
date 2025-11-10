/**
 * Home Page
 * Landing with Login and Signup buttons
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, LogIn, UserPlus } from 'lucide-react';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center px-4">
      <div className="max-w-3xl w-full">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 md:p-12">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-primary p-3 rounded-xl shadow-sm">
              <ShieldCheck className="h-8 w-8 text-white" />
            </div>
          </div>

          <h1 className="text-3xl md:text-4xl font-extrabold text-center text-gray-900">
            Alert Management Dashboard
          </h1>
          <p className="mt-3 text-center text-gray-600">
            Monitor, analyze, and act on alerts in real time.
          </p>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={() => navigate('/login')}
              className="w-full inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-lg text-base font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition"
            >
              <LogIn className="h-5 w-5 mr-2 text-white" />
              Login
            </button>

            <button
              onClick={() => navigate('/signup')}
              className="w-full inline-flex items-center justify-center px-6 py-3 border border-primary rounded-lg text-base font-medium text-primary bg-white hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition"
            >
              <UserPlus className="h-5 w-5 mr-2" />
              Sign up
            </button>
          </div>

          {token && (
            <div className="mt-6 text-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 border border-gray-300"
              >
                Continue to Dashboard
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Home;


