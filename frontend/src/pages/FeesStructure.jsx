import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api, money } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Wallet, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { useSchool } from '@/contexts/SchoolContext';

export default function FeesStructure() {
  const { activeSchoolId } = useSchool();
  const [heads, setHeads] = useState([]);
  const [plans, setPlans] = useState([]);
  const [classes, setClasses] = useState([]);
  const [openHead, setOpenHead] = useState(false);
  const [openPlan, setOpenPlan] = useState(false);

  const load = useCallback(async () => {
    if (!activeSchoolId) return;
    const [{ data: h }, { data: p }, { data: c }] = await Promise.all([
      api.get('/fees/heads'), api.get('/fees/plans'), api.get('/classes'),
    ]);
    setHeads(h); setPlans(p); setClasses(c);
  }, [activeSchoolId]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const h = () => load();
    window.addEventListener('stv:school-changed', h);
    return () => window.removeEventListener('stv:school-changed', h);
  }, [load]);

  const classMap = Object.fromEntries(classes.map((c) => [c.id, c.name]));

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="h-font text-2xl font-semibold">Fee Structures</h1>
        <p className="text-sm text-muted-foreground">Configure fee heads and fee plans for each class.</p>
      </div>
      <Tabs defaultValue="plans">
        <TabsList><TabsTrigger value="plans">Fee Plans</TabsTrigger><TabsTrigger value="heads">Fee Heads</TabsTrigger></TabsList>
        <TabsContent value="plans">
          <Card className="p-4 border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium">{plans.length} plans configured</div>
              <Button data-testid="add-fee-plan" onClick={() => setOpenPlan(true)} className="gap-2"><Plus className="h-4 w-4" /> Add Plan</Button>
            </div>
            <Table>
              <TableHeader><TableRow><TableHead>Plan Name</TableHead><TableHead>Class</TableHead><TableHead>Session</TableHead><TableHead>Items</TableHead><TableHead>Annual Discount</TableHead><TableHead>Late Fee</TableHead></TableRow></TableHeader>
              <TableBody>
                {plans.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.name}</TableCell>
                    <TableCell>{classMap[p.class_id] || '—'}</TableCell>
                    <TableCell>{p.academic_session}</TableCell>
                    <TableCell><Badge variant="secondary">{p.items?.length || 0} items</Badge></TableCell>
                    <TableCell className="tabular-nums">{p.annual_discount_percent}%</TableCell>
                    <TableCell className="tabular-nums">{money(p.late_fee_amount)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
        <TabsContent value="heads">
          <Card className="p-4 border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium">{heads.length} fee heads</div>
              <Button data-testid="add-fee-head" onClick={() => setOpenHead(true)} className="gap-2"><Plus className="h-4 w-4" /> Add Head</Button>
            </div>
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Category</TableHead><TableHead>Active</TableHead></TableRow></TableHeader>
              <TableBody>
                {heads.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell className="font-medium">{h.name}</TableCell>
                    <TableCell className="capitalize">{h.category}</TableCell>
                    <TableCell>{h.is_active ? <Badge className="bg-[#E6F6F4] text-[#0F766E] border border-[#BFEAE6]">Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>

      <AddFeeHead open={openHead} onOpenChange={setOpenHead} onSaved={load} />
      <AddFeePlan open={openPlan} onOpenChange={setOpenPlan} heads={heads} classes={classes} onSaved={load} />
    </AppShell>
  );
}

function AddFeeHead({ open, onOpenChange, onSaved }) {
  const [name, setName] = useState(''); const [category, setCategory] = useState('general'); const [saving, setSaving] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setSaving(true);
    try { await api.post('/fees/heads', { name, category }); toast.success('Fee head added'); onOpenChange(false); onSaved(); setName(''); }
    catch (err) { toast.error(err.response?.data?.detail || 'Failed'); } finally { setSaving(false); }
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>Add Fee Head</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="grid gap-4">
          <div className="grid gap-1.5"><Label>Name</Label><Input required value={name} onChange={(e) => setName(e.target.value)} /></div>
          <div className="grid gap-1.5"><Label>Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {['general', 'transport', 'hostel', 'exam', 'activity'].map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter><Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save'}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function AddFeePlan({ open, onOpenChange, heads, classes, onSaved }) {
  const [form, setForm] = useState({ name: '', class_id: '', annual_discount_percent: 10, late_fee_amount: 50, items: [] });
  const [item, setItem] = useState({ fee_head_id: '', amount: '', frequency: 'monthly' });
  const [saving, setSaving] = useState(false);
  const addItem = () => {
    if (!item.fee_head_id || !item.amount) return;
    const h = heads.find((x) => x.id === item.fee_head_id);
    setForm({ ...form, items: [...form.items, { fee_head_id: item.fee_head_id, fee_head_name: h.name, amount: Number(item.amount), frequency: item.frequency, installments: item.frequency === 'monthly' ? 12 : item.frequency === 'quarterly' ? 4 : 1 }] });
    setItem({ fee_head_id: '', amount: '', frequency: 'monthly' });
  };
  const removeItem = (i) => setForm({ ...form, items: form.items.filter((_, idx) => idx !== i) });
  const submit = async (e) => {
    e.preventDefault(); setSaving(true);
    try { await api.post('/fees/plans', form); toast.success('Fee plan added'); onOpenChange(false); onSaved(); setForm({ name: '', class_id: '', annual_discount_percent: 10, late_fee_amount: 50, items: [] }); }
    catch (err) { toast.error(err.response?.data?.detail || 'Failed'); } finally { setSaving(false); }
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader><DialogTitle>Add Fee Plan</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="grid gap-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="grid gap-1.5"><Label>Plan Name</Label><Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
            <div className="grid gap-1.5"><Label>Class</Label>
              <Select value={form.class_id} onValueChange={(v) => setForm({ ...form, class_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select class" /></SelectTrigger>
                <SelectContent>{classes.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="grid gap-1.5"><Label>Annual Discount %</Label><Input type="number" value={form.annual_discount_percent} onChange={(e) => setForm({ ...form, annual_discount_percent: Number(e.target.value) })} /></div>
            <div className="grid gap-1.5"><Label>Late Fee (₹)</Label><Input type="number" value={form.late_fee_amount} onChange={(e) => setForm({ ...form, late_fee_amount: Number(e.target.value) })} /></div>
          </div>
          <div>
            <div className="text-sm font-medium mb-2">Fee Items</div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
              <Select value={item.fee_head_id} onValueChange={(v) => setItem({ ...item, fee_head_id: v })}>
                <SelectTrigger><SelectValue placeholder="Fee Head" /></SelectTrigger>
                <SelectContent>{heads.map((h) => <SelectItem key={h.id} value={h.id}>{h.name}</SelectItem>)}</SelectContent>
              </Select>
              <Input type="number" placeholder="Amount" value={item.amount} onChange={(e) => setItem({ ...item, amount: e.target.value })} />
              <Select value={item.frequency} onValueChange={(v) => setItem({ ...item, frequency: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{['monthly', 'quarterly', 'half_yearly', 'yearly', 'one_time'].map((f) => <SelectItem key={f} value={f}>{f}</SelectItem>)}</SelectContent>
              </Select>
              <Button type="button" variant="outline" onClick={addItem}>Add</Button>
            </div>
            <div className="mt-3 divide-y divide-border">
              {form.items.map((it, i) => (
                <div key={i} className="flex items-center justify-between py-2 text-sm">
                  <div>{it.fee_head_name} · <span className="text-muted-foreground">{it.frequency}</span></div>
                  <div className="flex items-center gap-3"><span className="tabular-nums">{money(it.amount)}</span>
                    <button type="button" onClick={() => removeItem(i)}><Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter><Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save Plan'}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
