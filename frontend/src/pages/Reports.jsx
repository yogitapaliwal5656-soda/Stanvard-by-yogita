import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api, money, shortMoney } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileText, Download, FileSpreadsheet, Printer } from 'lucide-react';
import { useSchool } from '@/contexts/SchoolContext';

export default function ReportsPage() {
  const { activeSchoolId } = useSchool();
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const { data: d } = await api.get('/reports/collection', { params: { start_date: startDate, end_date: endDate } });
      setData(d);
    } finally { setLoading(false); }
  }, [startDate, endDate]);

  useEffect(() => { if (activeSchoolId) run(); }, [activeSchoolId, run]);
  useEffect(() => { const h = () => run(); window.addEventListener('stv:school-changed', h); return () => window.removeEventListener('stv:school-changed', h); }, [run]);

  const dl = async (ext) => {
    const resp = await api.get(`/reports/collection.${ext}`, { params: { start_date: startDate, end_date: endDate }, responseType: 'blob' });
    const mime = ext === 'pdf' ? 'application/pdf' : ext === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    const blob = new Blob([resp.data], { type: mime });
    const url = window.URL.createObjectURL(blob);
    if (ext === 'pdf') { window.open(url, '_blank'); }
    else { const a = document.createElement('a'); a.href = url; a.download = `collection.${ext}`; a.click(); a.remove(); }
  };

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="h-font text-2xl font-semibold">Reports</h1>
        <p className="text-sm text-muted-foreground">Fee collection and attendance analytics with export options.</p>
      </div>
      <Card className="p-4 border-border mb-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="grid gap-1.5"><Label className="text-xs">Start Date</Label><Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></div>
          <div className="grid gap-1.5"><Label className="text-xs">End Date</Label><Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></div>
          <div className="flex items-end"><Button onClick={run} disabled={loading}>{loading ? 'Loading…' : 'Run Report'}</Button></div>
          <div className="flex items-end justify-end gap-2">
            <Button data-testid="report-download-pdf" variant="outline" size="sm" onClick={() => dl('pdf')} className="gap-1"><FileText className="h-3.5 w-3.5" /> PDF</Button>
            <Button data-testid="report-download-csv" variant="outline" size="sm" onClick={() => dl('csv')} className="gap-1"><Download className="h-3.5 w-3.5" /> CSV</Button>
            <Button data-testid="report-download-xlsx" variant="outline" size="sm" onClick={() => dl('xlsx')} className="gap-1"><FileSpreadsheet className="h-3.5 w-3.5" /> Excel</Button>
          </div>
        </div>
      </Card>

      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
            <Card className="p-4 border-border"><div className="text-xs uppercase text-muted-foreground">Total Collection</div><div className="h-font text-xl font-semibold">{shortMoney(data.total)}</div></Card>
            <Card className="p-4 border-border"><div className="text-xs uppercase text-muted-foreground">Transactions</div><div className="h-font text-xl font-semibold">{data.count}</div></Card>
            {Object.entries(data.by_mode || {}).slice(0, 2).map(([k, v]) => (
              <Card key={k} className="p-4 border-border"><div className="text-xs uppercase text-muted-foreground capitalize">{k.replace('_', ' ')}</div><div className="h-font text-xl font-semibold">{shortMoney(v)}</div></Card>
            ))}
          </div>
          <Card className="border-border">
            <Table>
              <TableHeader><TableRow><TableHead>Receipt No</TableHead><TableHead>Date</TableHead><TableHead>Student</TableHead><TableHead>Mode</TableHead><TableHead className="text-right">Amount</TableHead></TableRow></TableHeader>
              <TableBody>
                {data.payments.length === 0 && <TableRow><TableCell colSpan={5} className="py-8 text-center text-muted-foreground text-sm">No transactions in this range.</TableCell></TableRow>}
                {data.payments.slice(0, 100).map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-mono text-xs">{p.receipt_number}</TableCell>
                    <TableCell>{(p.paid_at || '').slice(0, 10)}</TableCell>
                    <TableCell className="font-medium">{p.student_name}</TableCell>
                    <TableCell className="capitalize">{String(p.payment_mode).replace('_', ' ')}</TableCell>
                    <TableCell className="text-right tabular-nums">{money(p.total_paid)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </>
      )}
    </AppShell>
  );
}
