import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { api, money, downloadBlob } from '@/lib/api';
import { Card, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Wallet, Search, User, Receipt, Trash2, IndianRupee } from 'lucide-react';
import { toast } from 'sonner';
import { useSchool } from '@/contexts/SchoolContext';

const PAYMENT_MODES = [
  { value: 'cash', label: 'Cash' },
  { value: 'upi', label: 'UPI' },
  { value: 'card', label: 'Card' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'razorpay', label: 'Online (Razorpay)' },
];

export default function FeeCollection() {
  const [params] = useSearchParams();
  const { activeSchoolId } = useSchool();
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState(params.get('student') || '');
  const [selected, setSelected] = useState(null);
  const [dues, setDues] = useState(null);
  const [items, setItems] = useState([]);
  const [discount, setDiscount] = useState(0);
  const [lateFee, setLateFee] = useState(0);
  const [mode, setMode] = useState('cash');
  const [txnRef, setTxnRef] = useState('');
  const [remarks, setRemarks] = useState('');
  const [saving, setSaving] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);

  const loadStudents = useCallback(async () => {
    if (!activeSchoolId) return;
    const { data } = await api.get('/students', { params: { limit: 500 } });
    setStudents(data);
  }, [activeSchoolId]);
  useEffect(() => { loadStudents(); }, [loadStudents]);
  useEffect(() => {
    const h = () => { loadStudents(); setStudentId(''); setSelected(null); setItems([]); };
    window.addEventListener('stv:school-changed', h);
    return () => window.removeEventListener('stv:school-changed', h);
  }, [loadStudents]);

  useEffect(() => {
    if (!studentId) { setSelected(null); setDues(null); setItems([]); return; }
    (async () => {
      const { data } = await api.get(`/fees/student/${studentId}/dues`);
      setDues(data); setSelected(data.student);
      // Pre-fill items with plan items (current month)
      const now = new Date();
      const monthLabel = now.toLocaleString('en-US', { month: 'long', year: 'numeric' });
      setItems((data.dues || []).slice(0, 3).map((d) => ({
        fee_head_id: d.fee_head_id, fee_head_name: d.fee_head_name,
        period: d.frequency === 'yearly' ? '2025-26' : monthLabel,
        amount: d.amount, selected: true,
      })));
    })();
  }, [studentId]);

  const toggleItem = (i) => {
    const next = [...items]; next[i].selected = !next[i].selected; setItems(next);
  };
  const updateAmount = (i, v) => {
    const next = [...items]; next[i].amount = Number(v); setItems(next);
  };
  const removeItem = (i) => setItems(items.filter((_, idx) => idx !== i));
  const activeItems = items.filter((i) => i.selected);
  const subtotal = activeItems.reduce((s, i) => s + Number(i.amount || 0), 0);
  const total = subtotal + Number(lateFee || 0) - Number(discount || 0);

  const submit = async () => {
    if (!studentId || activeItems.length === 0) { toast.error('Select student and at least one fee item'); return; }
    setSaving(true);
    const payload = {
      student_id: studentId,
      items: activeItems.map((i) => ({ fee_head_id: i.fee_head_id, fee_head_name: i.fee_head_name, period: i.period, amount: Number(i.amount) })),
      discount: Number(discount || 0),
      late_fee: Number(lateFee || 0),
      payment_mode: mode,
      txn_ref: txnRef,
      remarks,
    };
    try {
      if (mode === 'razorpay') {
        const { data: order } = await api.post('/payments/razorpay/order', payload);
        const rzp = new window.Razorpay({
          key: order.key_id, amount: order.amount, currency: order.currency,
          order_id: order.order_id, name: 'Stanvard School',
          description: `Fee payment for ${order.student_name}`,
          prefill: { name: order.student_name },
          handler: async (r) => {
            try {
              const { data: payment } = await api.post('/payments/razorpay/verify', {
                razorpay_order_id: r.razorpay_order_id,
                razorpay_payment_id: r.razorpay_payment_id,
                razorpay_signature: r.razorpay_signature,
              });
              toast.success(`Payment successful! Receipt: ${payment.receipt_number}`, {
                action: { label: 'Download Receipt', onClick: () => openReceipt(payment.id) },
              });
              resetForm();
            } catch (e) { toast.error('Verification failed'); }
          },
          theme: { color: '#0B2F4A' },
        });
        rzp.open();
      } else {
        const { data: payment } = await api.post('/payments/collect', payload);
        toast.success(`Receipt ${payment.receipt_number} generated`, {
          action: { label: 'View PDF', onClick: () => openReceipt(payment.id) },
        });
        resetForm();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to collect payment');
    } finally { setSaving(false); }
  };

  const openReceipt = async (id) => {
    const resp = await api.get(`/payments/${id}/receipt.pdf`, { responseType: 'blob' });
    const blob = new Blob([resp.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  const resetForm = () => {
    setDiscount(0); setLateFee(0); setMode('cash'); setTxnRef(''); setRemarks('');
    if (studentId) {
      // refresh dues
      api.get(`/fees/student/${studentId}/dues`).then(({ data }) => setDues(data));
    }
  };

  const filteredStudents = students;

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="h-font text-2xl font-semibold">Collect Fee</h1>
        <p className="text-sm text-muted-foreground">Select student, add fee items, choose payment mode.</p>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 space-y-4">
          <Card className="p-5 border-border">
            <Label className="mb-2 block">Student</Label>
            <Popover open={pickerOpen} onOpenChange={setPickerOpen}>
              <PopoverTrigger asChild>
                <button data-testid="fee-collect-student-picker" className="w-full flex items-center gap-2 h-11 px-3 rounded-md border border-border bg-card hover:bg-secondary text-sm text-left">
                  <User className="h-4 w-4 text-muted-foreground" />
                  {selected ? (
                    <span><span className="font-medium">{selected.full_name}</span> <span className="text-muted-foreground">· {selected.admission_number}</span></span>
                  ) : <span className="text-muted-foreground">Search & select student</span>}
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-[420px] p-0">
                <Command>
                  <CommandInput placeholder="Search by name or admission number…" />
                  <CommandList>
                    <CommandEmpty>No students found</CommandEmpty>
                    <CommandGroup>
                      {filteredStudents.slice(0, 100).map((s) => (
                        <CommandItem key={s.id} value={`${s.full_name} ${s.admission_number}`} onSelect={() => { setStudentId(s.id); setPickerOpen(false); }}>
                          <div className="flex flex-col">
                            <span className="font-medium">{s.full_name}</span>
                            <span className="text-xs text-muted-foreground">{s.admission_number}</span>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
            {dues && (
              <div className="mt-3 text-xs text-muted-foreground">Previously paid: <span className="font-medium text-foreground tabular-nums">{money(dues.total_paid)}</span></div>
            )}
          </Card>

          <Card className="p-5 border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium">Fee Items</div>
              <Button type="button" variant="outline" size="sm" onClick={() => setItems([...items, { fee_head_name: 'Custom', period: '', amount: 0, selected: true }])}>+ Add Item</Button>
            </div>
            {items.length === 0 && <div className="py-6 text-sm text-muted-foreground text-center">Select a student to load fee items.</div>}
            <div className="divide-y divide-border">
              {items.map((it, i) => (
                <div key={i} className="py-3 grid grid-cols-12 items-center gap-2">
                  <input type="checkbox" checked={it.selected} onChange={() => toggleItem(i)} className="col-span-1" />
                  <Input className="col-span-5" value={it.fee_head_name} onChange={(e) => { const nx = [...items]; nx[i].fee_head_name = e.target.value; setItems(nx); }} />
                  <Input className="col-span-3" placeholder="Period" value={it.period} onChange={(e) => { const nx = [...items]; nx[i].period = e.target.value; setItems(nx); }} />
                  <div className="col-span-2 relative">
                    <IndianRupee className="h-3.5 w-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <Input className="pl-7 tabular-nums text-right" type="number" value={it.amount} onChange={(e) => updateAmount(i, e.target.value)} />
                  </div>
                  <button className="col-span-1 text-muted-foreground hover:text-destructive" onClick={() => removeItem(i)}><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div>
          <Card className="p-5 border-border sticky top-20">
            <div className="text-sm font-semibold mb-3">Payment Summary</div>
            <div className="space-y-2 text-sm">
              <Row label="Subtotal" value={money(subtotal)} />
              <div className="grid gap-1.5">
                <Label className="text-xs">Discount (₹)</Label>
                <Input data-testid="fee-collect-discount-input" type="number" value={discount} onChange={(e) => setDiscount(e.target.value)} />
              </div>
              <div className="grid gap-1.5">
                <Label className="text-xs">Late Fee (₹)</Label>
                <Input data-testid="fee-collect-latefee-input" type="number" value={lateFee} onChange={(e) => setLateFee(e.target.value)} />
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <span className="text-sm font-medium">Total Payable</span>
                <span className="h-font text-xl font-semibold tabular-nums">{money(total)}</span>
              </div>
            </div>
            <div className="mt-4">
              <Label className="text-xs mb-2 block">Payment Mode</Label>
              <RadioGroup value={mode} onValueChange={setMode} className="grid grid-cols-2 gap-1.5" data-testid="fee-collect-payment-mode">
                {PAYMENT_MODES.map((m) => (
                  <label key={m.value} className={`flex items-center gap-2 rounded-md border border-border px-3 py-2 cursor-pointer text-sm ${mode === m.value ? 'bg-secondary border-[hsl(var(--primary))]' : ''}`}>
                    <RadioGroupItem value={m.value} />
                    <span>{m.label}</span>
                  </label>
                ))}
              </RadioGroup>
            </div>
            {(mode !== 'cash' && mode !== 'razorpay') && (
              <div className="mt-3 grid gap-1.5">
                <Label className="text-xs">Reference / Cheque No.</Label>
                <Input value={txnRef} onChange={(e) => setTxnRef(e.target.value)} />
              </div>
            )}
            <div className="mt-3 grid gap-1.5">
              <Label className="text-xs">Remarks</Label>
              <Textarea rows={2} value={remarks} onChange={(e) => setRemarks(e.target.value)} />
            </div>
            <Button data-testid="fee-collect-generate-receipt-button" onClick={submit} disabled={saving || !studentId || activeItems.length === 0} className="w-full mt-4 h-11 gap-2">
              <Receipt className="h-4 w-4" /> {saving ? 'Processing…' : mode === 'razorpay' ? 'Pay Online' : 'Generate Receipt'}
            </Button>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}

const Row = ({ label, value }) => (
  <div className="flex items-center justify-between"><span className="text-muted-foreground">{label}</span><span className="tabular-nums font-medium">{value}</span></div>
);
