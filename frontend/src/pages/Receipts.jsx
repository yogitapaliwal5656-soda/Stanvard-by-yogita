import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api, money } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Search, Download, ExternalLink } from 'lucide-react';
import { useSchool } from '@/contexts/SchoolContext';

export default function Receipts() {
  const { activeSchoolId } = useSchool();
  const [payments, setPayments] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!activeSchoolId) return;
    setLoading(true);
    try {
      const { data } = await api.get('/payments', { params: { limit: 500 } });
      setPayments(data);
    } finally { setLoading(false); }
  }, [activeSchoolId]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const h = () => load();
    window.addEventListener('stv:school-changed', h);
    return () => window.removeEventListener('stv:school-changed', h);
  }, [load]);

  const filtered = payments.filter((p) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (p.receipt_number || '').toLowerCase().includes(q) ||
           (p.student_name || '').toLowerCase().includes(q);
  });

  const openPdf = async (p) => {
    const resp = await api.get(`/payments/${p.id}/receipt.pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
    window.open(url, '_blank');
  };

  const downloadPdf = async (p) => {
    const resp = await api.get(`/payments/${p.id}/receipt.pdf`, { responseType: 'blob' });
    const blob = new Blob([resp.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `receipt_${p.receipt_number}.pdf`; a.click(); a.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="h-font text-2xl font-semibold">Receipts</h1>
        <p className="text-sm text-muted-foreground">All fee payment records with downloadable PDF receipts.</p>
      </div>
      <Card className="p-4 border-border mb-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input data-testid="receipts-search" className="pl-9" placeholder="Search by receipt number or student…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </Card>
      <Card className="border-border" data-testid="receipts-table">
        <Table>
          <TableHeader><TableRow className="bg-secondary/60"><TableHead>Receipt No</TableHead><TableHead>Student</TableHead><TableHead>Date</TableHead><TableHead>Mode</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Amount</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
          <TableBody>
            {filtered.length === 0 && !loading && (<TableRow><TableCell colSpan={7} className="py-8 text-center text-muted-foreground text-sm">No receipts found.</TableCell></TableRow>)}
            {filtered.map((p) => (
              <TableRow key={p.id} className="hover:bg-secondary/40">
                <TableCell className="font-mono text-xs">{p.receipt_number}</TableCell>
                <TableCell className="font-medium">{p.student_name}</TableCell>
                <TableCell>{(p.paid_at || '').slice(0, 10)}</TableCell>
                <TableCell className="capitalize">{String(p.payment_mode).replace('_', ' ')}</TableCell>
                <TableCell><Badge className="bg-[#E6F6F4] text-[#0F766E] border border-[#BFEAE6]">{p.status}</Badge></TableCell>
                <TableCell className="text-right font-semibold tabular-nums">{money(p.total_paid)}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button data-testid={`receipt-view-${p.id}`} size="sm" variant="outline" onClick={() => openPdf(p)} className="h-8 gap-1"><ExternalLink className="h-3.5 w-3.5" />View</Button>
                    <Button data-testid={`receipt-download-${p.id}`} size="sm" variant="outline" onClick={() => downloadPdf(p)} className="h-8 gap-1"><Download className="h-3.5 w-3.5" />PDF</Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </AppShell>
  );
}
