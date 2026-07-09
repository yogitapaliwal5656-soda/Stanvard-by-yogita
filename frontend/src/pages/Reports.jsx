import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api, money, shortMoney } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  FileText, Download, FileSpreadsheet, Search, Filter, ChevronDown, X, Layers,
} from 'lucide-react';
import { useSchool } from '@/contexts/SchoolContext';
import { toast } from 'sonner';

// -------------- Helpers --------------
const buildClassSectionsParam = (selections) => {
  // selections: [{ class_id, section }] — section may be null (means "all sections of that class")
  if (!selections || selections.length === 0) return '';
  return selections.map((s) => `${s.class_id}:${s.section || ''}`).join(',');
};

const dedupeSelections = (list) => {
  const seen = new Set();
  const out = [];
  list.forEach((s) => {
    const k = `${s.class_id}:${s.section || ''}`;
    if (!seen.has(k)) { seen.add(k); out.push(s); }
  });
  return out;
};

export default function ReportsPage() {
  const { activeSchoolId } = useSchool();

  // Fee Collection tab state (unchanged)
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [mode, setMode] = useState('all');

  // Fee Status tab state
  const [classes, setClasses] = useState([]);
  const [selections, setSelections] = useState([]); // [{class_id, class_name, section}]
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [selectorSearch, setSelectorSearch] = useState('');

  const [collectionData, setCollectionData] = useState(null);
  const [feeStatusData, setFeeStatusData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dlLoading, setDlLoading] = useState(false);

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
      const csParam = buildClassSectionsParam(selections);
      if (csParam) params.class_sections = csParam;
      if (statusFilter !== 'all') params.status_filter = statusFilter;
      const { data } = await api.get('/reports/fee-status', { params });
      setFeeStatusData(data);
    } finally { setLoading(false); }
  }, [selections, statusFilter]);

  useEffect(() => { loadClasses(); }, [loadClasses]);
  useEffect(() => { if (activeSchoolId) { runCollection(); runFeeStatus(); } }, [activeSchoolId, runCollection, runFeeStatus]);
  useEffect(() => {
    const h = () => {
      loadClasses();
      setSelections([]);
      runCollection();
      runFeeStatus();
    };
    window.addEventListener('stv:school-changed', h);
    return () => window.removeEventListener('stv:school-changed', h);
  }, [runCollection, runFeeStatus, loadClasses]);

  // Selection helpers
  const isSectionSelected = (classId, section) =>
    selections.some((s) => s.class_id === classId && s.section === section);

  const isClassAllSelected = (klass) => {
    const secs = klass.sections || [];
    if (secs.length === 0) return isSectionSelected(klass.id, null);
    return secs.every((sec) => isSectionSelected(klass.id, sec));
  };

  const toggleSection = (klass, section) => {
    setSelections((prev) => {
      const exists = prev.some((s) => s.class_id === klass.id && s.section === section);
      if (exists) return prev.filter((s) => !(s.class_id === klass.id && s.section === section));
      return dedupeSelections([...prev, { class_id: klass.id, class_name: klass.name, section }]);
    });
  };

  const toggleClassAllSections = (klass) => {
    const secs = klass.sections || [];
    const allSelected = isClassAllSelected(klass);
    setSelections((prev) => {
      const withoutClass = prev.filter((s) => s.class_id !== klass.id);
      if (allSelected) return withoutClass;
      if (secs.length === 0) {
        return dedupeSelections([...withoutClass, { class_id: klass.id, class_name: klass.name, section: null }]);
      }
      const additions = secs.map((sec) => ({ class_id: klass.id, class_name: klass.name, section: sec }));
      return dedupeSelections([...withoutClass, ...additions]);
    });
  };

  const removeSelection = (item) => {
    setSelections((prev) => prev.filter((s) => !(s.class_id === item.class_id && s.section === item.section)));
  };

  const clearSelections = () => setSelections([]);

  const filteredClassesForSelector = useMemo(() => {
    const q = selectorSearch.trim().toLowerCase();
    if (!q) return classes;
    return classes.filter((c) => (c.name || '').toLowerCase().includes(q));
  }, [classes, selectorSearch]);

  // Download for fee-status
  const dlFeeStatus = async (ext) => {
    setDlLoading(true);
    try {
      const params = {};
      const csParam = buildClassSectionsParam(selections);
      if (csParam) params.class_sections = csParam;
      if (statusFilter !== 'all') params.status_filter = statusFilter;
      const resp = await api.get(`/reports/fee-status.${ext}`, { params, responseType: 'blob' });
      const mime = ext === 'pdf' ? 'application/pdf'
        : ext === 'csv' ? 'text/csv'
          : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      const blob = new Blob([resp.data], { type: mime });
      const url = window.URL.createObjectURL(blob);
      if (ext === 'pdf') {
        window.open(url, '_blank');
      } else {
        const a = document.createElement('a');
        a.href = url;
        a.download = `fee_status_report.${ext}`;
        a.click();
        a.remove();
      }
      toast.success(`Downloaded ${ext.toUpperCase()} report`);
    } catch (err) {
      toast.error(`Failed to download ${ext.toUpperCase()}: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setDlLoading(false);
    }
  };

  const dl = async (ext) => {
    const resp = await api.get(`/reports/collection.${ext}`, {
      params: { start_date: startDate, end_date: endDate },
      responseType: 'blob',
    });
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

  const selectionSummary = useMemo(() => {
    if (selections.length === 0) return 'All Classes & Sections';
    // Group by class
    const byClass = {};
    selections.forEach((s) => {
      if (!byClass[s.class_id]) byClass[s.class_id] = { name: s.class_name, sections: [] };
      byClass[s.class_id].sections.push(s.section || 'All');
    });
    return Object.values(byClass)
      .map((c) => `${c.name} (${c.sections.join(', ')})`)
      .join(' · ');
  }, [selections]);

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

        {/* --------- Fee Collection --------- */}
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

        {/* --------- Student Fee Status --------- */}
        <TabsContent value="fee-status">
          <Card className="p-4 border-border mb-4">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
              <div className="md:col-span-3 grid gap-1.5">
                <Label className="text-xs">Search</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <Input className="pl-9" placeholder="Name / Admission no." value={search} onChange={(e) => setSearch(e.target.value)} data-testid="report-search-input" />
                </div>
              </div>

              <div className="md:col-span-5 grid gap-1.5">
                <Label className="text-xs flex items-center gap-1">
                  <Layers className="h-3 w-3" /> Classes &amp; Sections
                </Label>
                <Popover open={selectorOpen} onOpenChange={setSelectorOpen}>
                  <PopoverTrigger asChild>
                    <button
                      type="button"
                      className="w-full flex items-center justify-between gap-2 h-10 px-3 rounded-md border border-border bg-card hover:bg-secondary text-sm text-left transition-colors"
                      data-testid="report-classes-multiselect"
                    >
                      <span className="truncate">
                        {selections.length === 0 ? (
                          <span className="text-muted-foreground">All classes &amp; sections</span>
                        ) : (
                          <span className="font-medium">{selections.length} selection{selections.length === 1 ? '' : 's'}</span>
                        )}
                      </span>
                      <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    </button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[420px] p-0" align="start">
                    <div className="p-3 border-b border-border">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                        <Input
                          value={selectorSearch}
                          onChange={(e) => setSelectorSearch(e.target.value)}
                          placeholder="Search class name…"
                          className="pl-9 h-9"
                          data-testid="class-selector-search"
                        />
                      </div>
                      <div className="flex items-center justify-between mt-2 text-xs">
                        <div className="text-muted-foreground">
                          {selections.length} selected of {classes.reduce((n, c) => n + (c.sections?.length || 1), 0)} available
                        </div>
                        {selections.length > 0 && (
                          <button
                            className="text-[hsl(var(--primary))] hover:underline"
                            onClick={clearSelections}
                            data-testid="class-selector-clear"
                          >
                            Clear all
                          </button>
                        )}
                      </div>
                    </div>
                    <div
                      className="max-h-[360px] overflow-y-auto overscroll-contain"
                      data-testid="class-selector-scroll"
                      style={{ scrollbarGutter: 'stable' }}
                    >
                      <div className="p-2">
                        {filteredClassesForSelector.length === 0 && (
                          <div className="py-6 text-center text-sm text-muted-foreground">No classes match.</div>
                        )}
                        {filteredClassesForSelector.map((klass) => {
                          const secs = klass.sections || [];
                          const allSel = isClassAllSelected(klass);
                          return (
                            <div key={klass.id} className="py-2 px-2 rounded-md hover:bg-secondary/60">
                              <div className="flex items-center justify-between">
                                <label className="flex items-center gap-2 cursor-pointer flex-1">
                                  <Checkbox
                                    checked={allSel}
                                    onCheckedChange={() => toggleClassAllSections(klass)}
                                    data-testid={`class-toggle-${klass.name.replace(/\s+/g, '-')}`}
                                  />
                                  <span className="font-medium text-sm">{klass.name}</span>
                                </label>
                                <span className="text-xs text-muted-foreground">
                                  {secs.length ? `${secs.length} section${secs.length === 1 ? '' : 's'}` : 'no sections'}
                                </span>
                              </div>
                              {secs.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 mt-2 pl-6">
                                  {secs.map((sec) => {
                                    const on = isSectionSelected(klass.id, sec);
                                    return (
                                      <button
                                        key={sec}
                                        type="button"
                                        onClick={() => toggleSection(klass, sec)}
                                        data-testid={`section-toggle-${klass.name.replace(/\s+/g, '-')}-${sec}`}
                                        className={`px-2.5 py-1 text-xs rounded-md border transition-colors ${
                                          on
                                            ? 'bg-[hsl(var(--primary))] text-white border-[hsl(var(--primary))]'
                                            : 'border-border hover:bg-secondary'
                                        }`}
                                      >
                                        Sec {sec}
                                      </button>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                    <div className="p-2 border-t border-border flex justify-end">
                      <Button size="sm" onClick={() => setSelectorOpen(false)} data-testid="class-selector-done">
                        Done
                      </Button>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>

              <div className="md:col-span-2 grid gap-1.5">
                <Label className="text-xs">Status</Label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger data-testid="report-status-filter"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="paid">Paid</SelectItem>
                    <SelectItem value="partial">Partial</SelectItem>
                    <SelectItem value="unpaid">Unpaid</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="md:col-span-2 flex items-end">
                <Button onClick={runFeeStatus} disabled={loading} className="w-full gap-1" data-testid="report-apply-btn">
                  <Filter className="h-3.5 w-3.5" />{loading ? 'Loading…' : 'Apply'}
                </Button>
              </div>
            </div>

            {/* Selected chips */}
            {selections.length > 0 && (
              <div className="mt-3 pt-3 border-t border-border">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-xs text-muted-foreground mr-1">Selected:</span>
                  {selections.map((s) => (
                    <Badge
                      key={`${s.class_id}:${s.section || ''}`}
                      variant="secondary"
                      className="gap-1 pl-2 pr-1 h-6 text-xs"
                      data-testid={`selection-chip-${s.class_name.replace(/\s+/g, '-')}-${s.section || 'All'}`}
                    >
                      {s.class_name}{s.section ? ` · ${s.section}` : ' · All'}
                      <button
                        type="button"
                        onClick={() => removeSelection(s)}
                        className="ml-0.5 hover:bg-muted rounded p-0.5"
                        aria-label={`Remove ${s.class_name} ${s.section || 'All'}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Download row */}
            <div className="mt-3 pt-3 border-t border-border flex flex-wrap items-center justify-between gap-2">
              <div className="text-xs text-muted-foreground truncate max-w-[70%]">
                Showing: <b>{selectionSummary}</b>
                {statusFilter !== 'all' && <> · Status: <b className="capitalize">{statusFilter}</b></>}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => dlFeeStatus('pdf')}
                  disabled={dlLoading || loading}
                  className="gap-1"
                  data-testid="fee-status-download-pdf"
                >
                  <FileText className="h-3.5 w-3.5" /> PDF
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => dlFeeStatus('xlsx')}
                  disabled={dlLoading || loading}
                  className="gap-1"
                  data-testid="fee-status-download-xlsx"
                >
                  <FileSpreadsheet className="h-3.5 w-3.5" /> XLSX
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => dlFeeStatus('csv')}
                  disabled={dlLoading || loading}
                  className="gap-1"
                  data-testid="fee-status-download-csv"
                >
                  <Download className="h-3.5 w-3.5" /> CSV
                </Button>
              </div>
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
