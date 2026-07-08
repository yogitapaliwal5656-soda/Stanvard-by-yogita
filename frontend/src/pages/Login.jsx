import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { GraduationCap, ShieldCheck, Building2, CreditCard } from 'lucide-react';
import { toast } from 'sonner';

const demoAccounts = [
  { role: 'Super Admin', email: 'superadmin@stanvard.school', password: 'super123' },
  { role: 'School Admin (GN)', email: 'admin.gn@stanvard.school', password: 'admin123' },
  { role: 'Accountant (GN)', email: 'accountant.gn@stanvard.school', password: 'acc123' },
  { role: 'Teacher (GN)', email: 'teacher.gn@stanvard.school', password: 'teacher123' },
  { role: 'Parent (GN)', email: 'parent.gn20250001@stanvard.school', password: 'parent123' },
];

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const u = await login(email, password);
      toast.success(`Welcome, ${u.full_name}`);
      const dest = u.role === 'parent' ? '/parent' : (loc.state?.from?.pathname || '/');
      nav(dest, { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (a) => { setEmail(a.email); setPassword(a.password); };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* left panel */}
      <div className="login-band relative hidden lg:flex flex-col justify-between p-10">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-md bg-[hsl(var(--primary))] flex items-center justify-center">
            <GraduationCap className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="h-font font-semibold text-foreground">Stanvard School</div>
            <div className="text-xs text-muted-foreground">Multi-branch ERP & Parent Portal</div>
          </div>
        </div>
        <div>
          <h1 className="h-font text-3xl xl:text-4xl font-semibold text-foreground max-w-md leading-tight">
            Excellence in education, powered by modern school management.
          </h1>
          <p className="mt-3 text-sm text-muted-foreground max-w-md">
            Manage students, fees, attendance, and communication across all Stanvard branches from a single, secure platform.
          </p>
          <div className="mt-8 grid gap-2">
            {[
              { icon: ShieldCheck, t: 'Secure payments & audit-ready records' },
              { icon: Building2, t: 'Multi-branch: Ganesh Nagar · Kanpur · Ayar' },
              { icon: CreditCard, t: 'Cash, UPI, Card, Cheque, Bank Transfer, Online' },
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-foreground/80">
                <f.icon className="h-4 w-4 text-[hsl(var(--accent))]" />
                <span>{f.t}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="text-xs text-muted-foreground">© {new Date().getFullYear()} Stanvard School Society. All rights reserved.</div>
      </div>
      {/* form */}
      <div className="flex items-center justify-center p-6">
        <Card className="w-full max-w-md p-6 sm:p-8 border-border shadow-sm">
          <div className="mb-6 text-center lg:hidden">
            <div className="inline-flex h-10 w-10 rounded-md bg-[hsl(var(--primary))] items-center justify-center mb-2">
              <GraduationCap className="h-5 w-5 text-white" />
            </div>
            <div className="h-font font-semibold">Stanvard School ERP</div>
          </div>
          <h2 className="h-font text-2xl font-semibold">Welcome back</h2>
          <p className="text-sm text-muted-foreground mt-1">Sign in to your account to continue.</p>

          <form onSubmit={submit} className="mt-6 grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email" type="email" required autoFocus
                data-testid="login-email-input"
                value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@stanvard.school"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password" type="password" required
                data-testid="login-password-input"
                value={password} onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <Button data-testid="login-submit-button" type="submit" disabled={loading} className="h-10">
              {loading ? 'Signing in…' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-border">
            <div className="text-xs font-medium text-muted-foreground mb-2">Demo accounts — tap to fill</div>
            <div className="grid gap-1.5">
              {demoAccounts.map((a) => (
                <button
                  key={a.email} type="button" onClick={() => fillDemo(a)}
                  data-testid={`demo-${a.role.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}
                  className="text-left text-xs px-3 py-2 rounded-md border border-border hover:bg-secondary transition-colors"
                >
                  <span className="font-medium text-foreground">{a.role}</span>
                  <span className="text-muted-foreground ml-2">{a.email}</span>
                </button>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
