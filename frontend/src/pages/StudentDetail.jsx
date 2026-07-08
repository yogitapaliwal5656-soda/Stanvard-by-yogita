import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { api, money } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Wallet, Receipt as ReceiptIcon } from 'lucide-react';

export default function StudentDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [student, setStudent] = useState(null);
  const [dues, setDues] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    (async () => {
      const { data: s } = await api.get(`/students/${id}`);
      setStudent(s);
      const [{ data: d }, { data: a }, { data: p }] = await Promise.all([
        api.get(`/fees/student/${id}/dues`),
        api.get('/attendance', { params: { student_id: id } }),
        api.get('/payments', { params: { student_id: id } }),
      ]);
      setDues(d); setAttendance(a); setPayments(p);
    })();
  }, [id]);

  if (!student) return <AppShell><div className="text-sm text-muted-foreground">Loading…</div></AppShell>;

  const paidTotal = dues?.total_paid || 0;

  return (
    <AppShell>
      <button onClick={() => nav(-1)} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <Card className="p-6 border-border mb-4">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={student.photo_url} />
              <AvatarFallback className="bg-secondary">{(student.full_name || 'S').split(' ').map((x) => x[0]).slice(0, 2).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h1 className="h-font text-2xl font-semibold">{student.full_name}</h1>
              <div className="flex items-center flex-wrap gap-2 mt-1">
                <Badge variant="secondary">{student.admission_number}</Badge>
                <Badge variant="secondary">{student.gender}</Badge>
                {student.category && <Badge variant="secondary">{student.category}</Badge>}
                {student.blood_group && <Badge variant="secondary">Blood: {student.blood_group}</Badge>}
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                DOB: {student.dob || '—'} • Admitted: {student.admission_date || '—'}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button data-testid="student-collect-fee" onClick={() => nav(`/fees/collect?student=${student.id}`)} className="gap-2">
              <Wallet className="h-4 w-4" /> Collect Fee
            </Button>
          </div>
        </div>
      </Card>

      <Tabs defaultValue="info" data-testid="student-profile-tabs">
        <TabsList>
          <TabsTrigger value="info">Information</TabsTrigger>
          <TabsTrigger value="fees" data-testid="student-profile-fees-tab">Fees</TabsTrigger>
          <TabsTrigger value="attendance" data-testid="student-profile-attendance-tab">Attendance</TabsTrigger>
          <TabsTrigger value="payments">Payment History</TabsTrigger>
        </TabsList>
        <TabsContent value="info">
          <Card className="p-6 border-border grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {[
              ['Father', student.father_name], ['Mother', student.mother_name], ['Guardian', student.guardian_name],
              ['Phone', student.phone], ['Email', student.email], ['Address', student.address],
              ['Religion', student.religion], ['Transport', student.transport_route],
              ['Previous School', student.previous_school], ['Medical', student.medical_info],
            ].map(([k, v]) => (
              <div key={k}>
                <div className="text-xs uppercase text-muted-foreground tracking-wide">{k}</div>
                <div className="mt-0.5">{v || '—'}</div>
              </div>
            ))}
          </Card>
        </TabsContent>
        <TabsContent value="fees">
          <Card className="p-6 border-border">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-xs uppercase text-muted-foreground tracking-wide">Total Paid</div>
                <div className="h-font text-2xl font-semibold">{money(paidTotal)}</div>
              </div>
              <Button variant="outline" onClick={() => nav(`/fees/collect?student=${student.id}`)} className="gap-2">
                <Wallet className="h-4 w-4" /> Collect Fee
              </Button>
            </div>
            <div className="text-sm font-medium mb-2">Fee Plan Items</div>
            <Table>
              <TableHeader><TableRow><TableHead>Fee Head</TableHead><TableHead>Frequency</TableHead><TableHead className="text-right">Amount</TableHead></TableRow></TableHeader>
              <TableBody>
                {(dues?.dues || []).map((d, i) => (
                  <TableRow key={i}>
                    <TableCell>{d.fee_head_name}</TableCell>
                    <TableCell className="capitalize">{d.frequency}</TableCell>
                    <TableCell className="text-right tabular-nums">{money(d.amount)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
        <TabsContent value="attendance">
          <Card className="p-6 border-border">
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[['Present', attendance.filter((a) => a.status === 'present').length, 'bg-[#E6F6F4] text-[#0F766E]'],
                ['Absent', attendance.filter((a) => a.status === 'absent').length, 'bg-[#FEE4E2] text-[#B42318]'],
                ['Leave', attendance.filter((a) => a.status === 'leave').length, 'bg-[#FFF3E0] text-[#B45309]']].map(([label, val, cls]) => (
                <div key={label} className={`p-4 rounded-md ${cls}`}>
                  <div className="text-xs">{label}</div>
                  <div className="h-font text-xl font-semibold">{val}</div>
                </div>
              ))}
            </div>
            <Table>
              <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Status</TableHead><TableHead>Remarks</TableHead></TableRow></TableHeader>
              <TableBody>
                {attendance.slice(0, 20).map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>{a.date}</TableCell>
                    <TableCell><Badge className={a.status === 'present' ? 'bg-[#E6F6F4] text-[#0F766E] border border-[#BFEAE6]' : a.status === 'absent' ? 'bg-[#FEE4E2] text-[#B42318] border border-[#FECACA]' : 'bg-[#FFF3E0] text-[#B45309] border border-[#FFD7A8]'}>{a.status}</Badge></TableCell>
                    <TableCell className="text-sm text-muted-foreground">{a.remarks || '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
        <TabsContent value="payments">
          <Card className="p-6 border-border">
            <Table>
              <TableHeader><TableRow><TableHead>Receipt</TableHead><TableHead>Date</TableHead><TableHead>Mode</TableHead><TableHead className="text-right">Amount</TableHead><TableHead></TableHead></TableRow></TableHeader>
              <TableBody>
                {payments.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-mono text-xs">{p.receipt_number}</TableCell>
                    <TableCell>{(p.paid_at || '').slice(0, 10)}</TableCell>
                    <TableCell className="capitalize">{String(p.payment_mode).replace('_', ' ')}</TableCell>
                    <TableCell className="text-right font-semibold tabular-nums">{money(p.total_paid)}</TableCell>
                    <TableCell><Button size="sm" variant="outline" onClick={() => window.open(`${api.defaults.baseURL}/payments/${p.id}/receipt.pdf?token=${localStorage.getItem('stv_token')}`, '_blank')} className="gap-1"><ReceiptIcon className="h-3.5 w-3.5" /> PDF</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
