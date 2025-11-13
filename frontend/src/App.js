import { useState, useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { ShoppingCart, TrendingUp, Clock, Shield, Zap, BarChart3, Package, Users, DollarSign, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', name: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/signup';
      const response = await axios.post(`${API}${endpoint}`, formData);
      
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      toast.success(isLogin ? 'Welcome back!' : 'Account created successfully!');
      onLogin(response.data.user, response.data.token);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page" data-testid="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="logo-section">
              <Zap className="logo-icon" />
              <h1>ScaleMart</h1>
            </div>
            <p className="tagline">Lightning-Fast Flash Sales</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            {!isLogin && (
              <div className="form-group">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  data-testid="name-input"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required={!isLogin}
                />
              </div>
            )}

            <div className="form-group">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                data-testid="email-input"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                data-testid="password-input"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </div>

            <Button
              type="submit"
              data-testid="auth-submit-button"
              className="auth-submit-btn"
              disabled={loading}
            >
              {loading ? 'Processing...' : isLogin ? 'Login' : 'Sign Up'}
            </Button>
          </form>

          <div className="auth-toggle">
            <button
              data-testid="toggle-auth-mode"
              onClick={() => setIsLogin(!isLogin)}
              className="toggle-link"
            >
              {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Login'}
            </button>
          </div>
        </div>

        <div className="features-panel">
          <h3>Why ScaleMart?</h3>
          <div className="feature-item">
            <Clock />
            <div>
              <h4>Real-Time Updates</h4>
              <p>Live stock indicators and instant order processing</p>
            </div>
          </div>
          <div className="feature-item">
            <Shield />
            <div>
              <h4>Secure Checkout</h4>
              <p>JWT authentication and atomic inventory locking</p>
            </div>
          </div>
          <div className="feature-item">
            <TrendingUp />
            <div>
              <h4>Flash Sales</h4>
              <p>Exclusive deals with massive discounts</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProductCard = ({ product, onBuy }) => {
  const discountedPrice = product.flash_sale
    ? product.price * (1 - product.discount_percent / 100)
    : product.price;

  const stockPercentage = (product.stock / 100) * 100;
  const isLowStock = product.stock < 10;

  return (
    <Card className="product-card" data-testid={`product-card-${product.id}`}>
      {product.flash_sale && (
        <Badge className="flash-badge" data-testid="flash-sale-badge">
          <Zap size={14} /> FLASH SALE - {product.discount_percent}% OFF
        </Badge>
      )}
      
      <div className="product-image">
        <img src={product.image_url} alt={product.name} />
      </div>

      <CardContent className="product-content">
        <h3 className="product-name" data-testid="product-name">{product.name}</h3>
        <p className="product-description">{product.description}</p>

        <div className="price-section">
          {product.flash_sale ? (
            <>
              <span className="original-price">${product.price.toFixed(2)}</span>
              <span className="discounted-price" data-testid="discounted-price">
                ${discountedPrice.toFixed(2)}
              </span>
            </>
          ) : (
            <span className="regular-price" data-testid="regular-price">${product.price.toFixed(2)}</span>
          )}
        </div>

        <div className="stock-section">
          <div className="stock-header">
            <span className={isLowStock ? 'low-stock' : 'stock-text'} data-testid="stock-count">
              {product.stock > 0 ? `Only ${product.stock} left!` : 'Out of Stock'}
            </span>
          </div>
          <Progress value={stockPercentage} className="stock-progress" />
        </div>

        <Button
          data-testid={`buy-button-${product.id}`}
          className="buy-button"
          onClick={() => onBuy(product)}
          disabled={product.stock === 0}
        >
          {product.stock > 0 ? (
            <>
              <ShoppingCart size={18} />
              Flash Buy Now
            </>
          ) : (
            'Sold Out'
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

const ProductCatalog = ({ token, user }) => {
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('catalog');

  useEffect(() => {
    fetchProducts();
    if (view === 'orders') {
      fetchOrders();
    }
    // Refresh products every 3 seconds for real-time updates
    const interval = setInterval(fetchProducts, 3000);
    return () => clearInterval(interval);
  }, [view]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load products');
      setLoading(false);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrders(response.data);
    } catch (error) {
      toast.error('Failed to load orders');
    }
  };

  const handleBuy = async (product) => {
    try {
      const response = await axios.post(
        `${API}/flash-buy`,
        { product_id: product.id, quantity: 1 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(response.data.message);
      fetchProducts();
      fetchOrders();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Purchase failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.reload();
  };

  const getStatusBadge = (status) => {
    const statusColors = {
      pending: 'bg-yellow-500',
      processing: 'bg-blue-500',
      confirmed: 'bg-green-500',
      failed: 'bg-red-500'
    };
    return <Badge className={statusColors[status]} data-testid={`order-status-${status}`}>{status.toUpperCase()}</Badge>;
  };

  if (loading) {
    return <div className="loading" data-testid="loading-indicator">Loading amazing deals...</div>;
  }

  return (
    <div className="catalog-page" data-testid="catalog-page">
      <nav className="navbar">
        <div className="nav-content">
          <div className="nav-brand">
            <Zap size={32} />
            <span>ScaleMart</span>
          </div>
          <div className="nav-actions">
            <Button
              data-testid="catalog-view-button"
              variant={view === 'catalog' ? 'default' : 'outline'}
              onClick={() => setView('catalog')}
            >
              <Package size={18} /> Catalog
            </Button>
            <Button
              data-testid="orders-view-button"
              variant={view === 'orders' ? 'default' : 'outline'}
              onClick={() => setView('orders')}
            >
              <ShoppingCart size={18} /> My Orders
            </Button>
            <Button
              data-testid="admin-view-button"
              variant={view === 'admin' ? 'default' : 'outline'}
              onClick={() => setView('admin')}
            >
              <BarChart3 size={18} /> Admin
            </Button>
            <Button
              data-testid="logout-button"
              variant="outline"
              onClick={handleLogout}
            >
              Logout
            </Button>
          </div>
        </div>
      </nav>

      <div className="main-content">
        {view === 'catalog' && (
          <div className="catalog-view" data-testid="catalog-view">
            <div className="hero-section">
              <div className="hero-content">
                <h1>Flash Sale Extravaganza</h1>
                <p>Lightning deals on premium products. Limited stock. Act fast!</p>
              </div>
            </div>

            <div className="products-grid">
              {products.map(product => (
                <ProductCard key={product.id} product={product} onBuy={handleBuy} />
              ))}
            </div>
          </div>
        )}

        {view === 'orders' && (
          <div className="orders-view" data-testid="orders-view">
            <h2>My Orders</h2>
            <div className="orders-list">
              {orders.length === 0 ? (
                <div className="empty-state" data-testid="empty-orders">No orders yet. Start shopping!</div>
              ) : (
                orders.map(order => (
                  <Card key={order.id} className="order-card" data-testid={`order-card-${order.id}`}>
                    <CardContent className="order-content">
                      <div className="order-header">
                        <div>
                          <h3 data-testid="order-product-name">{order.product_name}</h3>
                          <p className="order-id">Order ID: {order.id}</p>
                        </div>
                        {getStatusBadge(order.status)}
                      </div>
                      <div className="order-details">
                        <div className="detail-item">
                          <span className="label">Quantity:</span>
                          <span data-testid="order-quantity">{order.quantity}</span>
                        </div>
                        <div className="detail-item">
                          <span className="label">Total:</span>
                          <span className="price" data-testid="order-total">${order.total_price.toFixed(2)}</span>
                        </div>
                        <div className="detail-item">
                          <span className="label">Date:</span>
                          <span data-testid="order-date">{new Date(order.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {view === 'admin' && <AdminDashboard token={token} />}
      </div>
    </div>
  );
};

const AdminDashboard = ({ token }) => {
  const [stats, setStats] = useState(null);
  const [restockData, setRestockData] = useState({ product_id: '', quantity: 0 });

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load admin stats');
    }
  };

  const handleRestock = async () => {
    try {
      await axios.post(
        `${API}/admin/restock`,
        restockData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Product restocked successfully');
      fetchStats();
      setRestockData({ product_id: '', quantity: 0 });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Restock failed');
    }
  };

  if (!stats) return <div className="loading" data-testid="admin-loading">Loading stats...</div>;

  return (
    <div className="admin-dashboard" data-testid="admin-dashboard">
      <h2>Admin Dashboard</h2>
      
      <div className="stats-grid">
        <Card className="stat-card">
          <CardHeader>
            <CardTitle className="stat-title">
              <Users />
              Total Orders
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value" data-testid="total-orders">{stats.total_orders}</div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardHeader>
            <CardTitle className="stat-title">
              <Activity />
              Pending Orders
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value" data-testid="pending-orders">{stats.pending_orders}</div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardHeader>
            <CardTitle className="stat-title">
              <DollarSign />
              Total Revenue
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value" data-testid="total-revenue">${stats.total_revenue.toFixed(2)}</div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardHeader>
            <CardTitle className="stat-title">
              <TrendingUp />
              Sales Velocity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="stat-value" data-testid="sales-velocity">{stats.sales_velocity} orders/min</div>
          </CardContent>
        </Card>
      </div>

      <Card className="restock-card">
        <CardHeader>
          <CardTitle>Restock Products</CardTitle>
          <CardDescription>Add inventory to products</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="restock-form">
            <div className="form-group">
              <Label htmlFor="product_id">Product ID</Label>
              <Input
                id="product_id"
                data-testid="restock-product-id"
                value={restockData.product_id}
                onChange={(e) => setRestockData({ ...restockData, product_id: e.target.value })}
                placeholder="e.g., prod_1"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="quantity">Quantity</Label>
              <Input
                id="quantity"
                data-testid="restock-quantity"
                type="number"
                value={restockData.quantity}
                onChange={(e) => setRestockData({ ...restockData, quantity: parseInt(e.target.value) })}
              />
            </div>
            <Button
              data-testid="restock-submit-button"
              onClick={handleRestock}
              disabled={!restockData.product_id || restockData.quantity <= 0}
            >
              Restock
            </Button>
          </div>
        </CardContent>
      </Card>

      {stats.products_low_stock.length > 0 && (
        <Card className="low-stock-card">
          <CardHeader>
            <CardTitle>Low Stock Alert</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="low-stock-list" data-testid="low-stock-list">
              {stats.products_low_stock.map(product => (
                <div key={product.id} className="low-stock-item" data-testid={`low-stock-${product.id}`}>
                  <span>{product.name}</span>
                  <Badge variant="destructive" data-testid={`stock-count-${product.id}`}>{product.stock} left</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogin = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
  };

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              token ? (
                <ProductCatalog token={token} user={user} />
              ) : (
                <AuthPage onLogin={handleLogin} />
              )
            }
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;