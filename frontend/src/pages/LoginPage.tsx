// SETMS — Login Page
import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Shield, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useToast } from '../store/ToastContext';
import { getErrorMessage } from '../api/client';

export function LoginPage() {
  const { login } = useAuth();
  const { error: showError, info } = useToast();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (params.get('session') === 'expired') {
      showError('Session expired. Please log in again.');
    }
  }, [params, showError]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (role: string) => {
    const credentials: Record<string, [string, string]> = {
      admin: ['admin@setms.org', 'Admin1234!'],
      operator: ['operator@setms.org', 'Operator1234!'],
      driver: ['driver@setms.org', 'Driver1234!'],
      hospital: ['hospital@setms.org', 'Hospital1234!'],
    };
    const [e, p] = credentials[role];
    setEmail(e);
    setPassword(p);
    info(`Demo credentials for ${role} filled.`);
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: 'linear-gradient(135deg, #020817 0%, #0f172a 40%, #0a1628 100%)',
      }}
    >
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #3b82f6 0%, transparent 70%)' }} />
      </div>

      <div className="relative w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/30 mb-4">
            <Shield size={28} className="text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">SETMS</h1>
          <p className="text-slate-400 text-sm mt-1">Smart Emergency Traffic Management System</p>
        </div>

        {/* Card */}
        <div className="card-glass p-8">
          <h2 className="text-lg font-semibold text-white mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-xs font-medium text-slate-400 mb-1.5">
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2.5 rounded-lg text-sm text-slate-200 placeholder-slate-600 outline-none transition-all"
                style={{ background: '#0f172a', border: '1px solid #334155' }}
                placeholder="operator@setms.org"
                onFocus={e => e.target.style.borderColor = '#3b82f6'}
                onBlur={e => e.target.style.borderColor = '#334155'}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-medium text-slate-400 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2.5 pr-10 rounded-lg text-sm text-slate-200 placeholder-slate-600 outline-none transition-all"
                  style={{ background: '#0f172a', border: '1px solid #334155' }}
                  placeholder="••••••••"
                  onFocus={e => e.target.style.borderColor = '#3b82f6'}
                  onBlur={e => e.target.style.borderColor = '#334155'}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  aria-label={showPw ? 'Hide password' : 'Show password'}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          {/* Demo Accounts */}
          <div className="mt-6 pt-5 border-t border-slate-800">
            <p className="text-xs text-slate-500 mb-3 text-center">Demo accounts (development only)</p>
            <div className="grid grid-cols-2 gap-2">
              {['admin', 'operator', 'driver', 'hospital'].map(role => (
                <button
                  key={role}
                  onClick={() => fillDemo(role)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-700 transition-all capitalize"
                >
                  {role === 'hospital' ? 'Hospital Op.' : role.charAt(0).toUpperCase() + role.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-4">
          ⚠️ This is a simulation system. Signal commands do not control real traffic infrastructure.
        </p>
      </div>
    </div>
  );
}
