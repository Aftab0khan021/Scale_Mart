/**
 * Global Error Boundary Component
 * Catches React errors and displays fallback UI
 */
import React from 'react';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import { AlertCircle, RefreshCw } from 'lucide-react';

function ErrorFallback({ error, resetErrorBoundary }) {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
                <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                </div>

                <h1 className="mt-4 text-2xl font-bold text-center text-gray-900">
                    Oops! Something went wrong
                </h1>

                <p className="mt-2 text-center text-gray-600">
                    We're sorry for the inconvenience. The error has been logged and we'll look into it.
                </p>

                {process.env.NODE_ENV === 'development' && (
                    <div className="mt-4 p-4 bg-red-50 rounded-md">
                        <p className="text-sm font-mono text-red-800 break-all">
                            {error.message}
                        </p>
                    </div>
                )}

                <button
                    onClick={resetErrorBoundary}
                    className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                    Try Again
                </button>

                <button
                    onClick={() => window.location.href = '/'}
                    className="mt-3 w-full px-4 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                >
                    Go to Homepage
                </button>
            </div>
        </div>
    );
}

function ErrorBoundary({ children }) {
    const handleError = (error, errorInfo) => {
        // Log error to console
        console.error('Error caught by boundary:', error, errorInfo);

        // You can also send to error tracking service (Sentry, etc.)
        // if (window.Sentry) {
        //   window.Sentry.captureException(error);
        // }
    };

    return (
        <ReactErrorBoundary
            FallbackComponent={ErrorFallback}
            onError={handleError}
            onReset={() => {
                // Reset app state if needed
                window.location.reload();
            }}
        >
            {children}
        </ReactErrorBoundary>
    );
}

export default ErrorBoundary;
