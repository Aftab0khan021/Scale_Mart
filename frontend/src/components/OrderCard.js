/**
 * Order Card Component with Cancel Button
 * Enhanced version with cancellation functionality
 */
import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { X, Clock, CheckCircle, XCircle, Package } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const OrderCard = ({ order, token, onOrderCancelled }) => {
    const [cancelling, setCancelling] = useState(false);
    const [showCancelDialog, setShowCancelDialog] = useState(false);

    const getStatusIcon = (status) => {
        switch (status) {
            case 'pending':
                return <Clock className="w-5 h-5 text-yellow-500" />;
            case 'confirmed':
                return <CheckCircle className="w-5 h-5 text-green-500" />;
            case 'cancelled':
                return <XCircle className="w-5 h-5 text-red-500" />;
            default:
                return <Package className="w-5 h-5 text-gray-500" />;
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'confirmed':
                return 'bg-green-100 text-green-800';
            case 'cancelled':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const canCancel = (order) => {
        if (order.status !== 'pending') return false;

        // Check if within 5 minutes
        const createdAt = new Date(order.created_at);
        const now = new Date();
        const diffMinutes = (now - createdAt) / 1000 / 60;

        return diffMinutes <= 5;
    };

    const handleCancelOrder = async () => {
        try {
            setCancelling(true);
            const response = await axios.post(
                `${API_URL}/api/orders/${order.id}/cancel`,
                {},
                {
                    headers: { Authorization: `Bearer ${token}` }
                }
            );

            toast.success(response.data.message);
            setShowCancelDialog(false);

            if (onOrderCancelled) {
                onOrderCancelled(order.id);
            }
        } catch (error) {
            const message = error.response?.data?.detail || 'Failed to cancel order';
            toast.error(message);
        } finally {
            setCancelling(false);
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <>
            <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <p className="text-sm text-gray-600">Order ID</p>
                        <p className="font-mono text-sm font-medium text-gray-900">{order.id}</p>
                    </div>
                    <div className="flex items-center gap-2">
                        {getStatusIcon(order.status)}
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                            {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                        </span>
                    </div>
                </div>

                <div className="space-y-2 mb-4">
                    <div className="flex justify-between">
                        <span className="text-gray-600">Product:</span>
                        <span className="font-medium text-gray-900">{order.product_name}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-600">Quantity:</span>
                        <span className="font-medium text-gray-900">{order.quantity}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-600">Total:</span>
                        <span className="font-bold text-green-600">${order.total_price.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-600">Ordered:</span>
                        <span className="text-sm text-gray-900">{formatDate(order.created_at)}</span>
                    </div>
                </div>

                {canCancel(order) && (
                    <button
                        onClick={() => setShowCancelDialog(true)}
                        className="w-full mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
                    >
                        <X className="w-4 h-4" />
                        Cancel Order
                    </button>
                )}

                {order.status === 'pending' && !canCancel(order) && (
                    <p className="mt-4 text-sm text-gray-500 text-center">
                        Orders can only be cancelled within 5 minutes
                    </p>
                )}
            </div>

            {/* Cancel Confirmation Dialog */}
            {showCancelDialog && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-md w-full p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Cancel Order?</h3>
                        <p className="text-gray-600 mb-6">
                            Are you sure you want to cancel this order? This action cannot be undone.
                        </p>

                        <div className="bg-gray-50 rounded-lg p-4 mb-6">
                            <p className="text-sm text-gray-600 mb-1">Order: {order.product_name}</p>
                            <p className="text-sm text-gray-600">Amount: ${order.total_price.toFixed(2)}</p>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowCancelDialog(false)}
                                disabled={cancelling}
                                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                Keep Order
                            </button>
                            <button
                                onClick={handleCancelOrder}
                                disabled={cancelling}
                                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                            >
                                {cancelling ? 'Cancelling...' : 'Yes, Cancel'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default OrderCard;
