import React, { useState, useEffect } from 'react';
import { api, money } from '@/lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { Trash2, Plus } from 'lucide-react';
import { toast } from 'sonner';

// Helpers for month-wise preview
const MONTH_ORDER = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3];
function sessionYear(dueDate) {
  if (dueDate) {
    try {
      const d = new Date(dueDate);
      const y = d.getFullYear();
      return d.getMonth() + 1 >= 4 ? y : y - 1;
    } catch (_e) { /* ignore */ }
  }
  const now = new Date();
  return now.getMonth() + 1 >= 4 ? now.getFullYear() : now.getFullYear() - 1;
}
function monthLabels(startYear) {
  return MONTH_ORDER.map((m, idx) => {
    const y = m >= 4 ? startYear : startYear + 1;
    return new Date(y, m - 1, 1).toLocaleString('en-US', { month: 'short', year: '2-digit' });
  });
}


export function AssignFeeDialog({ open, onOpenChange, student, feePlans, feeHeads, existingAssignment, onSaved }) {
  const [mode, setMode] = useState('plan');  // 'plan' or 'custom'
  const [planId, setPlanId] = useState('');
  const [items, setItems] = useState([]);
  const [discountPercent, setDiscountPercent] = useState(0);
  const [discountAmount, setDiscountAmount] = useState(0);
  const [dueDate, setDueDate] = useState('');
  const [remarks, setRemarks] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (existingAssignment) {
      setMode(existingAssignment.custom_items?.length ? 'custom' : 'plan');
      setPlanId(existingAssignment.fee_plan_id || '');
      setItems((existingAssignment.custom_items || []).map((it, i) => ({ ...it, key: it.key || `it-existing-${i}` })));
      setDiscountPercent(existingAssignment.discount_percent || 0);
      setDiscountAmount(existingAssignment.discount_amount || 0);
      setDueDate(existingAssignment.due_date || '');
      setRemarks(existingAssignment.remarks || '');
    } else {
      setMode('plan'); setPlanId(''); setItems([]);
      setDiscountPercent(0); setDiscountAmount(0); setDueDate(''); setRemarks('');
    }
  }, [existingAssignment, open]);

  const addItem = () => setItems([...items, { key: `it-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, fee_head_name: '', amount: 0, frequency: 'monthly', due_date: dueDate }]);
  const removeItem = (key) => setItems(items.filter((it) => it.key !== key));
  const upd = (key, k, v) => setItems((prev) => prev.map((it) => it.key === key ? { ...it, [k]: v } : it));

  const selectedPlan = feePlans.find((p) => p.id === planId);
  const planTotal = (selectedPlan?.items || []).reduce((s, it) => s + Number(it.amount || 0), 0);
  const customTotal = items.reduce((s, it) => s + Number(it.amount || 0), 0);
  const grossTotal = mode === 'plan' ? planTotal : customTotal;
  const discAmt = Number(discountAmount || 0) + (grossTotal * Number(discountPercent || 0) / 100);
  const netTotal = Math.max(grossTotal - discAmt, 0);

  const submit = async () => {
    if (mode === 'plan' && !planId) { toast.error('Select a fee plan'); return; }
    if (mode === 'custom' && items.length === 0) { toast.error('Add at least one fee item'); return; }
    setSaving(true);
    try {
      const payload = {
        student_id: student.id,
        fee_plan_id: mode === 'plan' ? planId : null,
        custom_items: mode === 'custom' ? items.map((it) => ({
          fee_head_id: it.fee_head_id || null,
          fee_head_name: it.fee_head_name || 'Custom',
          amount: Number(it.amount || 0),
          frequency: it.frequency || 'one_time',
          due_date: it.due_date || dueDate || null,
        })) : [],
        discount_percent: Number(discountPercent || 0),
        discount_amount: Number(discountAmount || 0),
        due_date: dueDate || null,
        remarks,
      };
      if (existingAssignment) {
        await api.patch(`/fees/assignments/${existingAssignment.id}`, payload);
        toast.success('Fee assignment updated');
      } else {
        await api.post('/fees/assignments', payload);
        toast.success('Fee assigned to student');
      }
      onOpenChange(false);
      onSaved && onSaved();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    } finally {
      setSaving(false);
    }
  };

  if (!student) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{existingAssignment ? 'Edit Fee Assignment' : 'Assign Fees'} — {student.full_name}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4">
          <div className="grid grid-cols-2 gap-2">
            <label className={`flex items-center gap-2 p-3 rounded-md border cursor-pointer ${mode === 'plan' ? 'border-[hsl(var(--primary))] bg-secondary' : 'border-border'}`}>
              <input type="radio" checked={mode === 'plan'} onChange={() => setMode('plan')} />
              <div><div className="text-sm font-medium">Use Fee Plan</div><div className="text-xs text-muted-foreground">Apply an existing plan</div></div>
            </label>
            <label className={`flex items-center gap-2 p-3 rounded-md border cursor-pointer ${mode === 'custom' ? 'border-[hsl(var(--primary))] bg-secondary' : 'border-border'}`}>
              <input type="radio" checked={mode === 'custom'} onChange={() => setMode('custom')} />
              <div><div className="text-sm font-medium">Custom Items</div><div className="text-xs text-muted-foreground">Define specific fees</div></div>
            </label>
          </div>

          {mode === 'plan' && (
            <div className="grid gap-1.5">
              <Label>Fee Plan</Label>
              <Select value={planId} onValueChange={setPlanId}>
                <SelectTrigger data-testid="assign-fee-plan-select"><SelectValue placeholder="Select a fee plan" /></SelectTrigger>
                <SelectContent>{feePlans.map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
              </Select>
              {selectedPlan && (
                <Card className="p-3 border-border mt-2 text-xs">
                  <div className="font-medium mb-1">{selectedPlan.items?.length} items • Total {money(planTotal)}</div>
                  <div className="text-muted-foreground space-y-0.5">
                    {(selectedPlan.items || []).slice(0, 5).map((it) => (
                      <div key={`${it.fee_head_id || it.fee_head_name}-${it.frequency}`}>{it.fee_head_name} – {money(it.amount)} ({it.frequency})</div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          )}

          {mode === 'custom' && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Custom Fee Items</Label>
                <Button type="button" size="sm" variant="outline" onClick={addItem} className="gap-1"><Plus className="h-3.5 w-3.5" />Add Item</Button>
              </div>
              {items.length === 0 && <div className="text-xs text-muted-foreground py-2">No items yet. Click Add Item.</div>}
              <div className="space-y-2">
                {items.map((it) => (
                  <div key={it.key} className="grid grid-cols-12 gap-2 items-center">
                    <Input className="col-span-4" placeholder="Fee name" value={it.fee_head_name} onChange={(e) => upd(it.key, 'fee_head_name', e.target.value)} />
                    <Input className="col-span-3" type="number" placeholder="Amount" value={it.amount} onChange={(e) => upd(it.key, 'amount', e.target.value)} />
                    <Select value={it.frequency} onValueChange={(v) => upd(it.key, 'frequency', v)}>
                      <SelectTrigger className="col-span-2"><SelectValue /></SelectTrigger>
                      <SelectContent>{['monthly', 'quarterly', 'yearly', 'one_time'].map((f) => <SelectItem key={f} value={f}>{f}</SelectItem>)}</SelectContent>
                    </Select>
                    <Input className="col-span-2" type="date" value={it.due_date || ''} onChange={(e) => upd(it.key, 'due_date', e.target.value)} />
                    <button type="button" className="col-span-1 text-muted-foreground hover:text-destructive" onClick={() => removeItem(it.key)}><Trash2 className="h-4 w-4" /></button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-3 gap-3 pt-2 border-t border-border">
            <div className="grid gap-1.5"><Label>Discount %</Label><Input type="number" value={discountPercent} onChange={(e) => setDiscountPercent(e.target.value)} data-testid="assign-fee-discount-percent" /></div>
            <div className="grid gap-1.5"><Label>Discount ₹</Label><Input type="number" value={discountAmount} onChange={(e) => setDiscountAmount(e.target.value)} data-testid="assign-fee-discount-amount" /></div>
            <div className="grid gap-1.5"><Label>Due Date</Label><Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} data-testid="assign-fee-due-date" /></div>
          </div>

          <div className="grid gap-1.5"><Label>Remarks</Label><Textarea rows={2} value={remarks} onChange={(e) => setRemarks(e.target.value)} /></div>

          <Card className="p-3 border-border bg-secondary/50">
            <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Gross Total</span><span className="tabular-nums font-medium">{money(grossTotal)}</span></div>
            <div className="flex items-center justify-between text-sm mt-1"><span className="text-muted-foreground">Discount</span><span className="tabular-nums text-[hsl(var(--accent))]">- {money(discAmt)}</span></div>
            <div className="flex items-center justify-between pt-2 border-t border-border mt-2"><span className="text-sm font-semibold">Net Payable (Annual)</span><span className="h-font text-lg font-semibold tabular-nums">{money(netTotal)}</span></div>
            <div className="flex items-center justify-between pt-2 border-t border-border mt-2">
              <span className="text-xs text-muted-foreground">Monthly (÷12)</span>
              <span className="tabular-nums text-sm font-medium">{money(netTotal / 12)} × 12</span>
            </div>
          </Card>

          {/* Month-wise breakdown preview */}
          {netTotal > 0 && (
            <div>
              <div className="text-xs font-medium mb-2 text-muted-foreground">Month-wise breakdown (Apr → Mar)</div>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-1.5">
                {monthLabels(sessionYear(dueDate)).map((label, i) => (
                  <div key={i} className="rounded border border-border px-2 py-1.5 text-[11px]">
                    <div className="font-semibold truncate">{label}</div>
                    <div className="tabular-nums text-muted-foreground">{money(netTotal / 12)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={submit} disabled={saving} data-testid="assign-fee-submit">{saving ? 'Saving…' : (existingAssignment ? 'Update Assignment' : 'Assign Fees')}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
