/**
 * Analytics Dashboard Component
 * Displays charts and statistics for admin
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    TrendingUp,
    DollarSign,
    ShoppingCart,
    Package,
    AlertTriangle,
    Download
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const AnalyticsDashboard = ({ token }) => {
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState(7);

    useEffect(() => {
        fetchAnalytics();
    }, [days]);

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_URL}/api/admin/analytics?days=${days}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setAnalytics(response.data);
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    const exportCSV = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/admin/orders/export`, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob'
            });

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `orders_${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Failed to export CSV:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!analytics) {
        return <div>Failed to load analytics</div>;
    }

    const { summary, daily_revenue, top_products, low_stock_products } = analytics;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
                    <p className="text-gray-600">Last {days} days</p>
                </div>
                <div className="flex gap-2">
                    <select
                        value={days}
                        onChange={(e) => setDays(Number(e.target.value))}
                        className="px-4 py-2 border border-gray-300 rounded-lg"
                    >
                        <option value={7}>Last 7 days</option>
                        <option value={30}>Last 30 days</option>
                        <option value={90}>Last 90 days</option>
                    </select>
                    <button
                        onClick={exportCSV}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                        <Download className="w-4 h-4" />
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    icon={<ShoppingCart className="w-6 h-6" />}
                    title="Total Orders"
                    value={summary.total_orders}
                    color="blue"
                />
                <StatCard
                    icon={<DollarSign className="w-6 h-6" />}
                    title="Total Revenue"
                    value={`$${summary.total_revenue.toLocaleString()}`}
                    color="green"
                />
                <StatCard
                    icon={<TrendingUp className="w-6 h-6" />}
                    title="Confirmed Orders"
                    value={summary.confirmed_orders}
                    color="purple"
                />
                <StatCard
                    icon={<Package className="w-6 h-6" />}
                    title="Pending Orders"
                    value={summary.pending_orders}
                    color="orange"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Daily Revenue Chart */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-4">Daily Revenue</h3>
                    <div className="space-y-2">
                        {daily_revenue.map((day, index) => (
                            <div key={index} className="flex items-center gap-2">
                                <span className="text-sm text-gray-600 w-24">{day.date}</span>
                                <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                                    <div
                                        className="bg-blue-600 h-full flex items-center justify-end pr-2"
                                        style={{
                                            width: `${(day.revenue / Math.max(...daily_revenue.map(d => d.revenue))) * 100}%`
                                        }}
                                    >
                                        <span className="text-xs text-white font-medium">
                                            ${day.revenue}
                                        </span>
                                    </div>
                                </div>
                                <span className="text-sm text-gray-600 w-16">{day.orders} orders</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Top Products */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-4">Top Products</h3>
                    <div className="space-y-3">
                        {top_products.map((product, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">{product.product_name}</p>
                                    <p className="text-sm text-gray-600">{product.total_sold} sold</p>
                                </div>
                                <div className="text-right">
                                    <p className="font-semibold text-green-600">${product.revenue}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Low Stock Alert */}
            {low_stock_products.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="w-5 h-5 text-yellow-600" />
                        <h3 className="text-lg font-semibold text-yellow-900">Low Stock Alert</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {low_stock_products.map((product, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg">
                                <span className="font-medium text-gray-900">{product.name}</span>
                                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                                    {product.stock} left
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const StatCard = ({ icon, title, value, color }) => {
    const colorClasses = {
        blue: 'bg-blue-100 text-blue-600',
        green: 'bg-green-100 text-green-600',
        purple: 'bg-purple-100 text-purple-600',
        orange: 'bg-orange-100 text-orange-600'
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-gray-600 mb-1">{title}</p>
                    <p className="text-2xl font-bold text-gray-900">{value}</p>
                </div>
                <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
                    {icon}
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
