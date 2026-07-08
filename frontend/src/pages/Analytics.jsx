import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api, money, shortMoney } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useSchool } from '@/contexts/SchoolContext';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
  AreaChart, Area, PieChart, Pie, Cell, LineChart, Line, ComposedChart,
} from 'recharts';
import { TrendingUp, TrendingDown, IndianRupee, Wallet, Users, CalendarCheck, Percent, AlertCircle } from 'lucide-react';

const COLORS = ['#0B2F4A', '#0F766E', '#B45309', '#1D4ED8', '#7C3AED', '#DC2626', '#059669', '#D97706'];

export default function AnalyticsPage() {
  const { activeSchoolId, activeSchool } = useSchool();
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!activeSchoolId) return;
    setLoading(true);
    try {
      const { data: d } = await api.get('/analytics', { params: { year } });
      setData(d);
    } finally { setLoading(false); }
  }, [activeSchoolId, year]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { const h = () => load(); window.addEventListener('stv:school-changed', h); return () => window.removeEventListener('stv:school-changed', h); }, [load]);

  const modeData = data ? Object.entries(data.by_mode).map(([name, value]) => ({ name: name.replace('_', ' '), value })) : [];
  const headData = data ? Object.entries(data.by_head).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 6) : [];

  return (
    <AppShell>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
        <div>
          <h1 className="h-font text-2xl font-semibold">Analytics</h1>
          <p className="text-sm text-muted-foreground">Financial · Academic · Enrolment insights for {activeSchool?.name || 'your school'}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Year</span>
          <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
            <SelectTrigger className="w-[120px]" data-testid="analytics-year-select"><SelectValue /></SelectTrigger>
            <SelectContent>{[currentYear + 1, currentYear, currentYear - 1, currentYear - 2].map((y) => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}</SelectContent>
          </Select>
        </div>
      </div>

      {!data && loading && <div className="text-sm text-muted-foreground">Loading analytics…</div>}
      {data && (
        <>
          {/* KPI ROW */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <KPI icon={IndianRupee} label="Received" value={shortMoney(data.total_received)} accent="green" data-testid="analytics-kpi-received" />
            <KPI icon={AlertCircle} label="Outstanding" value={shortMoney(data.total_due)} accent="red" data-testid="analytics-kpi-due" />
            <KPI icon={Wallet} label="Expected" value={shortMoney(data.total_expected)} data-testid="analytics-kpi-expected" />
            <KPI icon={Percent} label="Collection Rate" value={`${data.total_expected ? Math.round(data.total_received / data.total_expected * 100) : 0}%`} accent="blue" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <KPI icon={Users} label="Total Students" value={data.total_students} />
            <KPI icon={CalendarCheck} label="Attendance Rate" value={`${data.attendance.rate}%`} accent="green" />
            <KPI icon={TrendingUp} label="Transactions" value={data.total_transactions} />
            <KPI icon={TrendingDown} label="Discounts Given" value={shortMoney(data.total_discount)} accent="amber" />
          </div>

          {/* Monthly Trend */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-4">
            <Card className="xl:col-span-2 p-5 border-border">
              <CardHeader className="p-0 mb-3"><CardTitle className="text-sm font-semibold">Monthly Collection ({year})</CardTitle></CardHeader>
              <CardContent className="p-0 h-[320px]" data-testid="analytics-monthly-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={data.months}>
                    <defs>
                      <linearGradient id="recGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#0F766E" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#0F766E" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E6EAF0" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => money(v)} contentStyle={{ background: '#fff', border: '1px solid #E6EAF0', borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Area yAxisId="left" type="monotone" dataKey="received" name="Received" fill="url(#recGrad)" stroke="#0F766E" strokeWidth={2} />
                    <Bar yAxisId="left" dataKey="discount" name="Discount" fill="#F59E0B" barSize={12} />
                    <Bar yAxisId="left" dataKey="late_fee" name="Late Fee" fill="#DC2626" barSize={12} />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="p-5 border-border">
              <CardHeader className="p-0 mb-3"><CardTitle className="text-sm font-semibold">Payment Modes</CardTitle></CardHeader>
              <CardContent className="p-0 h-[320px]" data-testid="analytics-mode-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={modeData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
                      {modeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={(v) => money(v)} contentStyle={{ background: '#fff', border: '1px solid #E6EAF0', borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Row 2: Fee heads + Admissions */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-4">
            <Card className="p-5 border-border">
              <CardHeader className="p-0 mb-3"><CardTitle className="text-sm font-semibold">Collection by Fee Head</CardTitle></CardHeader>
              <CardContent className="p-0 h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={headData} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E6EAF0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                    <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={100} />
                    <Tooltip formatter={(v) => money(v)} contentStyle={{ background: '#fff', border: '1px solid #E6EAF0', borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="value" name="Amount" fill="#0B2F4A" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="p-5 border-border">
              <CardHeader className="p-0 mb-3"><CardTitle className="text-sm font-semibold">New Admissions ({year})</CardTitle></CardHeader>
              <CardContent className="p-0 h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.months}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E6EAF0" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#fff', border: '1px solid #E6EAF0', borderRadius: 8, fontSize: 12 }} />
                    <Line type="monotone" dataKey="admissions" name="New Admissions" stroke="#1D4ED8" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Row 3: Class-wise pending */}
          <Card className="p-5 border-border mb-4">
            <CardHeader className="p-0 mb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-semibold">Class-wise Fee Status</CardTitle>
              <Badge variant="secondary">{data.by_class.length} classes</Badge>
            </CardHeader>
            <CardContent className="p-0 h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.by_class}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E6EAF0" />
                  <XAxis dataKey="class_name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#fff', border: '1px solid #E6EAF0', borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="paying_students" name="Paying" stackId="a" fill="#0F766E" />
                  <Bar dataKey="pending_students" name="Pending" stackId="a" fill="#DC2626" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Attendance breakdown */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <Card className="p-5 border-border">
              <CardHeader className="p-0 mb-3"><CardTitle className="text-sm font-semibold">Attendance Breakdown</CardTitle></CardHeader>
              <CardContent className="p-0 h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={[
                      { name: 'Present', value: data.attendance.present, color: '#0F766E' },
                      { name: 'Absent', value: data.attendance.absent, color: '#DC2626' },
                      { name: 'Leave', value: data.attendance.leave, color: '#F59E0B' },
                    ]} dataKey="value" nameKey="name" outerRadius={100} innerRadius={60}>
                      {[{ color: '#0F766E' }, { color: '#DC2626' }, { color: '#F59E0B' }].map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#fff', border: '1px solid #E6EAF0', borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card className="p-5 border-border">
              <CardHeader className="p-0 mb-3"><CardTitle className="text-sm font-semibold">Financial Summary</CardTitle></CardHeader>
              <CardContent className="p-0 space-y-3">
                <Row label="Expected (annual)" value={money(data.total_expected)} />
                <Row label="Discounts Applied" value={`- ${money(data.total_discount)}`} className="text-[hsl(var(--accent))]" />
                <Row label="Late Fees Collected" value={`+ ${money(data.total_late_fee)}`} className="text-[#B45309]" />
                <div className="pt-2 border-t border-border">
                  <Row label="Amount Received" value={money(data.total_received)} big />
                  <Row label="Outstanding Balance" value={money(data.total_due)} big className="text-[#B42318]" />
                </div>
                <div className="text-xs text-muted-foreground pt-2">
                  Based on all active fee assignments and successful payments in {year}.
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </AppShell>
  );
}

const KPI = ({ icon: Icon, label, value, accent, ...rest }) => {
  const cls = accent === 'green' ? 'bg-[#E6F6F4] text-[#0F766E]' : accent === 'red' ? 'bg-[#FEE4E2] text-[#B42318]' : accent === 'blue' ? 'bg-[#E8F0FF] text-[#1D4ED8]' : accent === 'amber' ? 'bg-[#FFF3E0] text-[#B45309]' : 'bg-secondary text-foreground';
  return (
    <Card className="p-4 border-border" {...rest}>
      <div className="flex items-center gap-3">
        <div className={`h-9 w-9 rounded-md flex items-center justify-center ${cls}`}><Icon className="h-4 w-4" /></div>
        <div>
          <div className="text-xs uppercase text-muted-foreground tracking-wide">{label}</div>
          <div className="h-font text-lg font-semibold tabular-nums">{value}</div>
        </div>
      </div>
    </Card>
  );
};

const Row = ({ label, value, className = '', big }) => (
  <div className="flex items-center justify-between">
    <span className={`${big ? 'text-sm font-medium' : 'text-sm text-muted-foreground'}`}>{label}</span>
    <span className={`tabular-nums ${big ? 'text-lg font-semibold' : 'font-medium'} ${className}`}>{value}</span>
  </div>
);
