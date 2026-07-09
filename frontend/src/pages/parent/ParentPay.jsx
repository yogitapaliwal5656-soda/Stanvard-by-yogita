import React, { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api, money } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Wallet, IndianRupee, CreditCard } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';

export default function ParentPay() {
  const { user } = useAuth();
  const [dues, setDues] = useState(null);
  const [items, setItems] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user?.linked_student_id) return;
    (async () => {
      const { data } = await api.get(`/fees/student/${user.linked_student_id}/dues`);
      setDues(data);
      const now = new Date();
      const monthLabel = now.toLocaleString('en-US', { month: 'long', year: 'numeric' });
      setItems((data.dues || []).slice(0, 6).map((d, i) => ({
        key: `pp-${d.fee_head_id || 'x'}-${i}`,
        fee_head_id: d.fee_head_id, fee_head_name: d.fee_head_name,
        period: d.frequency === 'yearly' ? '2025-26' : monthLabel,
        amount: d.amount, selected: true,
        due_date: d.due_date,
      })));
    })();
  }, [user]);

  const activeItems = items.filter((i) => i.selected);
  const total = activeItems.reduce((s, i) => s + Number(i.amount || 0), 0);

  const pay = async () => {
    if (activeItems.length === 0) return toast.error('Select at least one item');
    setSaving(true);
    try {
      const { data: order } = await api.post('/payments/razorpay/order', {
        student_id: user.linked_student_id,
        items: activeItems.map((i) => ({ fee_head_id: i.fee_head_id, fee_head_name: i.fee_head_name, period: i.period, amount: Number(i.amount) })),
        discount: 0, late_fee: 0,
      });
      const rzp = new window.Razorpay({
        key: order.key_id, amount: order.amount, currency: order.currency, order_id: order.order_id,
        name: 'Stanvard School', description: 'Fee Payment', prefill: { name: order.student_name },
        handler: async (r) => {
          try {
            const { data: payment } = await api.post('/payments/razorpay/verify', {
              razorpay_order_id: r.razorpay_order_id,
              razorpay_payment_id: r.razorpay_payment_id,
              razorpay_signature: r.razorpay_signature,
            });
            toast.success(`Payment successful! Receipt: ${payment.receipt_number}`, {
              action: { label: 'View Receipt', onClick: () => openReceipt(payment.id) },
            });
          } catch (e) { toast.error('Verification failed'); }
        },
        theme: { color: '#0B2F4A' },
      });
      rzp.open();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to initiate payment');
    } finally { setSaving(false); }
  };

  const openReceipt = async (id) => {
    const resp = await api.get(`/payments/${id}/receipt.pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
    window.open(url, '_blank');
  };

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="h-font text-2xl font-semibold">Pay Fees</h1>
        <p className="text-sm text-muted-foreground">Review and pay pending fees securely.</p>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <Card className="p-5 border-border">
            <div className="font-medium mb-3">Select Fee Items</div>
            {items.length === 0 && <div className="py-6 text-sm text-muted-foreground text-center">Loading fee details…</div>}
            {items.map((it) => (
              <label key={it.key} className="flex items-center gap-3 py-3 border-t border-border first:border-t-0 cursor-pointer">
                <input type="checkbox" checked={it.selected} onChange={() => setItems((prev) => prev.map((x) => x.key === it.key ? { ...x, selected: !x.selected } : x))} />
                <div className="flex-1">
                  <div className="font-medium">{it.fee_head_name}</div>
                  <div className="text-xs text-muted-foreground">{it.period} {it.due_date && <span className="ml-1 text-[#B45309]">• Due by {it.due_date}</span>}</div>
                </div>
                <div className="font-semibold tabular-nums">{money(it.amount)}</div>
              </label>
            ))}
          </Card>
        </div>
        <div>
          <Card className="p-5 border-border sticky top-20">
            <div className="text-sm font-semibold mb-3">Payment Summary</div>
            <div className="flex items-center justify-between text-sm text-muted-foreground"><span>Items</span><span>{activeItems.length}</span></div>
            <div className="flex items-center justify-between pt-3 border-t border-border mt-3">
              <span className="text-sm font-medium">Total Payable</span>
              <span className="h-font text-xl font-semibold tabular-nums">{money(total)}</span>
            </div>
            <Button data-testid="parent-pay-submit" onClick={pay} disabled={saving || total <= 0} className="w-full mt-4 h-11 gap-2">
              <CreditCard className="h-4 w-4" /> {saving ? 'Processing…' : 'Pay Online (Razorpay)'}
            </Button>
            <p className="text-xs text-muted-foreground mt-3">Secure payments powered by Razorpay. UPI, Cards, Netbanking, Wallets accepted.</p>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
