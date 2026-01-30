/**
 * WebSocket Hook for Real-Time Updates
 * Usage: const socket = useWebSocket();
 */
import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const useWebSocket = () => {
  const socketRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    // Initialize Socket.IO connection
    socketRef.current = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    const socket = socketRef.current;

    // Connection events
    socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
      toast.success('Connected to real-time updates');
    });

    socket.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
      setIsConnected(false);
      toast.error('Disconnected from real-time updates');
    });

    socket.on('connection_established', (data) => {
      console.log('🔌 Connection established:', data);
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setIsConnected(false);
    });

    // Cleanup on unmount
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  // Subscribe to product stock updates
  const subscribeToProduct = (productId, callback) => {
    if (!socketRef.current) return;

    socketRef.current.emit('subscribe_product', { product_id: productId });
    
    socketRef.current.on('stock_update', (data) => {
      if (data.product_id === productId) {
        console.log(`📦 Stock update for ${productId}:`, data.stock);
        setLastUpdate(data);
        if (callback) callback(data);
      }
    });
  };

  // Unsubscribe from product updates
  const unsubscribeFromProduct = (productId) => {
    if (!socketRef.current) return;
    
    socketRef.current.emit('unsubscribe_product', { product_id: productId });
    socketRef.current.off('stock_update');
  };

  // Subscribe to user order notifications
  const subscribeToOrders = (userId, callback) => {
    if (!socketRef.current) return;

    socketRef.current.emit('subscribe_user_orders', { user_id: userId });
    
    socketRef.current.on('order_notification', (data) => {
      console.log('📬 Order notification:', data);
      toast.info(data.message);
      if (callback) callback(data);
    });
  };

  // Listen for flash sale announcements
  const subscribeToFlashSales = (callback) => {
    if (!socketRef.current) return;

    socketRef.current.on('flash_sale_start', (data) => {
      console.log('🔥 Flash sale started:', data);
      toast.success(`Flash Sale: ${data.product_name} - ${data.discount}% OFF!`);
      if (callback) callback(data);
    });
  };

  return {
    socket: socketRef.current,
    isConnected,
    lastUpdate,
    subscribeToProduct,
    unsubscribeFromProduct,
    subscribeToOrders,
    subscribeToFlashSales
  };
};

export default useWebSocket;
