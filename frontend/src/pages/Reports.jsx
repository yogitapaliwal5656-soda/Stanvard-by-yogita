import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api, money, shortMoney } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText, Download, FileSpreadsheet, Search, Filter } from 'lucide-react';
import { useSchool } from '@/contexts/SchoolContext';

export default function ReportsPage() {
  const { activeSchoolId } = useSchool();
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [mode, setMode] = useState('all');
  const [classes, setClasses] = useState([]);
  const [classFilter, setClassFilter] = useState('all');
  const [sectionFilter, setSectionFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [minDue, setMinDue] = useState('');
  const [maxDue, setMaxDue] = useState('');
  const [search, setSearch] = useState('');
  const [collectionData, setCollectionData] = useState(null);
  const [feeStatusData, setFeeStatusData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadClasses = useCallback(async () => {
    if (!activeSchoolId) return;
    const { data } = await api.get('/classes');
    setClasses(data);
  }, [activeSchoolId]);

  const runCollection = useCallback(async () => {
    setLoading(true);
    try {
      const params = { start_date: startDate, end_date: endDate };
      if (mode !== 'all') params.mode = mode;
      const { data } = await api.get('/reports/collection', { params });
      setCollectionData(data);
    } finally { setLoading(false); }
  }, [startDate, endDate, mode]);

  const runFeeStatus = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (classFilter !== 'all') params.class_id = classFilter;
      if (sectionFilter !== 'all') params.section = sectionFilter;
      if (statusFilter !== 'all') params.status_filter = statusFilter;
      if (minDue) params.min_due = Number(minDue);
      if (maxDue) params.max_due = Number(maxDue);
      const { data } = await api.get('/reports/fee-status', { params });
      setFeeStatusData(data);
    } finally { setLoading(false); }
  }, [classFilter, sectionFilter, statusFilter, minDue, maxDue]);

  useEffect(() => { loadClasses(); }, [loadClasses]);
  useEffect(() => { if (activeSchoolId) { runCollection(); runFeeStatus(); } }, [activeSchoolId, runCollection, runFeeStatus]);
  useEffect(() => { const h = () => { runCollection(); runFeeStatus(); loadClasses(); }; window.addEventListener('stv:school-changed', h); return () => window.removeEventListener('stv:school-changed', h); }, [runCollection, runFeeStatus, loadClasses]);

  const dl = async (ext) => {
    const resp = await api.get(`/reports/collection.${ext}`, { params: { start_date: startDate, end_date: endDate }, responseType: 'blob' });
    const mime = ext === 'pdf' ? 'application/pdf' : ext === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    const blob = new Blob([resp.data], { type: mime });
    const url = window.URL.createObjectURL(blob);
    if (ext === 'pdf') window.open(url, '_blank');
    else { const a = document.createElement('a'); a.href = url; a.download = `collection.${ext}`; a.click(); a.remove(); }
  };

  const searchQ = search.toLowerCase();
  const filteredRows = (feeStatusData?.rows || []).filter((r) => {
    if (!search) return true;
    return (r.full_name || '').toLowerCase().includes(searchQ) || (r.admission_number || '').toLowerCase().includes(searchQ);
  });

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="h-font text-2xl font-semibold">Reports</h1>
        <p className="text-sm text-muted-foreground">Fee collection, pending dues, and detailed financial analytics.</p>
      </div>

      <Tabs defaultValue="collection">
        <TabsList>
          <TabsTrigger value="collection" data-testid="report-tab-collection">Fee Collection</TabsTrigger>
          <TabsTrigger value="fee-status" data-testid="report-tab-fee-status">Student Fee Status</TabsTrigger>
        </TabsList>

        <TabsContent value="collection">
          <Card className="p-4 border-border mb-4">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              <div className="grid gap-1.5"><Label className="text-xs">Start Date</Label><Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></div>
              <div className="grid gap-1.5"><Label className="text-xs">End Date</Label><Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></div>
              <div className="grid gap-1.5"><Label className="text-xs">Payment Mode</Label>
                <Select value={mode} onValueChange={setMode}>
                  <SelectTrigger data-testid="report-mode-filter"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Modes</SelectItem>
                    {['cash', 'upi', 'card', 'cheque', 'bank_transfer', 'razorpay'].map((m) => <SelectItem key={m} value={m}>{m.replace('_', ' ')}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end"><Button onClick={runCollection} disabled={loading} className="w-full">{loading ? 'Loading…' : 'Run Report'}</Button></div>
              <div className="flex items-end gap-1">
                <Button variant="outline" size="sm" onClick={() => dl('pdf')} className="gap-1 flex-1"><FileText className="h-3.5 w-3.5" /> PDF</Button>
                <Button variant="outline" size="sm" onClick={() => dl('csv')} className="gap-1 flex-1"><Download className="h-3.5 w-3.5" /> CSV</Button>
                <Button variant="outline" size="sm" onClick={() => dl('xlsx')} className="gap-1 flex-1"><FileSpreadsheet className="h-3.5 w-3.5" /> XLSX</Button>
              </div>
            </div>
          </Card>

          {collectionData && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <Card className="p-4 border-border"><div className="text-xs uppercase text-muted-foreground">Total Collection</div><div className="h-font text-xl font-semibold tabular-nums">{shortMoney(collectionData.total)}</div></Card>
                <Card className="p-4 border-border"><div className="text-xs uppercase text-muted-foreground">Transactions</div><div className="h-font text-xl font-semibold">{collectionData.count}</div></Card>
                {Object.entries(collectionData.by_mode || {}).slice(0, 2).map(([k, v]) => (
                  <Card key={k} className="p-4 border-border"><div className="text-xs uppercase text-muted-foreground capitalize">{k.replace('_', ' ')}</div><div className="h-font text-xl font-semibold tabular-nums">{shortMoney(v)}</div></Card>
                ))}
              </div>
              <Card className="border-border">
                <Table>
                  <TableHeader><TableRow><TableHead>Receipt No</TableHead><TableHead>Date</TableHead><TableHead>Student</TableHead><TableHead>Mode</TableHead><TableHead className="text-right">Amount</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {collectionData.payments.length === 0 && <TableRow><TableCell colSpan={5} className="py-8 text-center text-muted-foreground text-sm">No transactions.</TableCell></TableRow>}
                    {collectionData.payments.slice(0, 100).map((p) => (
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
        </TabsContent>

        <TabsContent value="fee-status">
          <Card className="p-4 border-border mb-4">
            <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
              <div className="grid gap-1.5 md:col-span-2">
                <Label className="text-xs">Search</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <Input className="pl-9" placeholder="Name / Admission no." value={search} onChange={(e) => setSearch(e.target.value)} data-testid="report-search-input" />
                </div>
              </div>
              <div className="grid gap-1.5"><Label className="text-xs">Class</Label>
                <Select value={classFilter} onValueChange={setClassFilter}>
                  <SelectTrigger data-testid="report-class-filter"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem>{classes.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="grid gap-1.5"><Label className="text-xs">Section</Label>
                <Select value={sectionFilter} onValueChange={setSectionFilter}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem><SelectItem value="A">A</SelectItem><SelectItem value="B">B</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="grid gap-1.5"><Label className="text-xs">Status</Label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger data-testid="report-status-filter"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem><SelectItem value="paid">Paid</SelectItem><SelectItem value="partial">Partial</SelectItem><SelectItem value="unpaid">Unpaid</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="flex items-end"><Button onClick={runFeeStatus} disabled={loading} className="w-full gap-1"><Filter className="h-3.5 w-3.5" />Apply</Button></div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mt-3">
              <div className="grid gap-1.5"><Label className="text-xs">Min Due ₹</Label><Input type="number" value={minDue} onChange={(e) => setMinDue(e.target.value)} data-testid="report-min-due" /></div>
              <div className="grid gap-1.5"><Label className="text-xs">Max Due ₹</Label><Input type="number" value={maxDue} onChange={(e) => setMaxDue(e.target.value)} data-testid="report-max-due" /></div>
            </div>
          </Card>

          {feeStatusData && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
                <Card className="p-3 border-border"><div className="text-xs uppercase text-muted-foreground">Students</div><div className="h-font text-lg font-semibold">{feeStatusData.count}</div></Card>
                <Card className="p-3 border-border"><div className="text-xs uppercase text-muted-foreground">Expected</div><div className="h-font text-lg font-semibold tabular-nums">{shortMoney(feeStatusData.summary.total_expected)}</div></Card>
                <Card className="p-3 border-border bg-[#E6F6F4]"><div className="text-xs uppercase text-[#0F766E]">Paid</div><div className="h-font text-lg font-semibold tabular-nums">{shortMoney(feeStatusData.summary.total_paid)}</div></Card>
                <Card className="p-3 border-border bg-[#FEE4E2]"><div className="text-xs uppercase text-[#B42318]">Due</div><div className="h-font text-lg font-semibold tabular-nums">{shortMoney(feeStatusData.summary.total_due)}</div></Card>
                <Card className="p-3 border-border"><div className="text-xs uppercase text-muted-foreground">Paid/Partial/Unpaid</div><div className="h-font text-lg font-semibold">{feeStatusData.summary.paid_count} / {feeStatusData.summary.partial_count} / {feeStatusData.summary.unpaid_count}</div></Card>
              </div>
              <Card className="border-border overflow-hidden" data-testid="report-fee-status-table">
                <Table>
                  <TableHeader><TableRow className="bg-secondary/60">
                    <TableHead>Student</TableHead><TableHead>Class</TableHead><TableHead>Guardian</TableHead>
                    <TableHead className="text-right">Expected</TableHead><TableHead className="text-right">Discount</TableHead>
                    <TableHead className="text-right">Paid</TableHead><TableHead className="text-right">Due</TableHead>
                    <TableHead>Due Date</TableHead><TableHead>Status</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {filteredRows.length === 0 && <TableRow><TableCell colSpan={9} className="py-8 text-center text-muted-foreground text-sm">No students match filters.</TableCell></TableRow>}
                    {filteredRows.map((r) => (
                      <TableRow key={r.student_id} className="hover:bg-secondary/40">
                        <TableCell>
                          <div className="font-medium">{r.full_name}</div>
                          <div className="text-xs text-muted-foreground font-mono">{r.admission_number}</div>
                        </TableCell>
                        <TableCell>{r.class_name} {r.section && `• ${r.section}`}</TableCell>
                        <TableCell><div>{r.father_name || '—'}</div><div className="text-xs text-muted-foreground">{r.phone || '—'}</div></TableCell>
                        <TableCell className="text-right tabular-nums">{money(r.expected)}</TableCell>
                        <TableCell className="text-right tabular-nums text-[hsl(var(--accent))]">{money(r.discount)}</TableCell>
                        <TableCell className="text-right tabular-nums font-medium">{money(r.paid)}</TableCell>
                        <TableCell className="text-right tabular-nums font-semibold">{money(r.due)}</TableCell>
                        <TableCell className="text-xs">{r.due_date || '—'}</TableCell>
                        <TableCell>
                          <Badge className={r.status === 'paid' ? 'bg-[#E6F6F4] text-[#0F766E] border border-[#BFEAE6]' : r.status === 'partial' ? 'bg-[#FFF3E0] text-[#B45309] border border-[#FFD7A8]' : 'bg-[#FEE4E2] text-[#B42318] border border-[#FECACA]'}>{r.status}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
