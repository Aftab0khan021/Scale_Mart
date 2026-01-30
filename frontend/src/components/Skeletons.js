/**
 * Loading Skeleton Components
 * Provides better loading UX with skeleton screens
 */
import React from 'react';

export const ProductCardSkeleton = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 animate-pulse">
        <div className="w-full h-48 bg-gray-300 dark:bg-gray-700 rounded-md mb-4"></div>
        <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full mb-2"></div>
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-5/6 mb-4"></div>
        <div className="flex justify-between items-center">
            <div className="h-8 bg-gray-300 dark:bg-gray-700 rounded w-1/3"></div>
            <div className="h-10 bg-gray-300 dark:bg-gray-700 rounded w-1/3"></div>
        </div>
    </div>
);

export const OrderCardSkeleton = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 animate-pulse">
        <div className="flex justify-between items-start mb-4">
            <div className="h-5 bg-gray-300 dark:bg-gray-700 rounded w-1/4"></div>
            <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded-full w-20"></div>
        </div>
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-1/3 mb-2"></div>
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-1/4"></div>
    </div>
);

export const StatCardSkeleton = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-gray-300 dark:bg-gray-700 rounded w-3/4"></div>
    </div>
);

export const TableSkeleton = ({ rows = 5 }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-1/4"></div>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {[...Array(rows)].map((_, i) => (
                <div key={i} className="p-4 flex gap-4 animate-pulse">
                    <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded flex-1"></div>
                    <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded flex-1"></div>
                    <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded flex-1"></div>
                </div>
            ))}
        </div>
    </div>
);

// Usage:
// {loading ? <ProductCardSkeleton /> : <ProductCard product={product} />}
