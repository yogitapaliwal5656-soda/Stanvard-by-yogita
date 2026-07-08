import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { api, money } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Wallet, Receipt as ReceiptIcon, Pencil, Plus, Trash2 } from 'lucide-react';
import { EditStudentDialog } from '@/components/EditStudentDialog';
import { AssignFeeDialog } from '@/components/AssignFeeDialog';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

export default function StudentDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const [student, setStudent] = useState(null);
  const [dues, setDues] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [payments, setPayments] = useState([]);
  const [classes, setClasses] = useState([]);
  const [feePlans, setFeePlans] = useState([]);
  const [feeHeads, setFeeHeads] = useState([]);
  const [editOpen, setEditOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState(null);

  const canEdit = ['super_admin', 'school_admin'].includes(user?.role);

  const load = useCallback(async () => {
    const { data: s } = await api.get(`/students/${id}`);
    setStudent(s);
    const [{ data: d }, { data: a }, { data: p }, { data: c }, { data: fp }, { data: fh }] = await Promise.all([
      api.get(`/fees/student/${id}/dues`),
      api.get('/attendance', { params: { student_id: id } }),
      api.get('/payments', { params: { student_id: id } }),
      api.get('/classes'),
      api.get('/fees/plans'),
      api.get('/fees/heads'),
    ]);
    setDues(d); setAttendance(a); setPayments(p); setClasses(c); setFeePlans(fp); setFeeHeads(fh);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (!student) return <AppShell><div className="text-sm text-muted-foreground">Loading…</div></AppShell>;

  const deleteAssignment = async (aid) => {
    if (!window.confirm('Remove this fee assignment?')) return;
    await api.delete(`/fees/assignments/${aid}`);
    toast.success('Assignment removed');
    load();
  };

  const openAssign = (assignment = null) => { setEditingAssignment(assignment); setAssignOpen(true); };

  const classMap = Object.fromEntries(classes.map((c) => [c.id, c.name]));

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
                <Badge variant="secondary">{classMap[student.class_id] || '-'} {student.section && `• ${student.section}`}</Badge>
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                DOB: {student.dob || '—'} • Admitted: {student.admission_date || '—'}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {canEdit && (
              <Button variant="outline" onClick={() => setEditOpen(true)} className="gap-2" data-testid="student-edit-button">
                <Pencil className="h-4 w-4" /> Edit Details
              </Button>
            )}
            {canEdit && (
              <Button variant="outline" onClick={() => openAssign(null)} className="gap-2" data-testid="student-assign-fee-button">
                <Plus className="h-4 w-4" /> Assign Fee
              </Button>
            )}
            {['super_admin', 'school_admin', 'accountant'].includes(user?.role) && (
              <Button onClick={() => nav(`/fees/collect?student=${student.id}`)} className="gap-2" data-testid="student-collect-fee">
                <Wallet className="h-4 w-4" /> Collect Fee
              </Button>
            )}
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
        <Card className="p-4 border-border"><div className="text-xs uppercase text-muted-foreground">Total Expected</div><div className="h-font text-xl font-semibold tabular-nums">{money(dues?.total_expected || 0)}</div></Card>
        <Card className="p-4 border-border bg-[#E6F6F4]"><div className="text-xs uppercase text-[#0F766E]">Total Paid</div><div className="h-font text-xl font-semibold tabular-nums">{money(dues?.total_paid || 0)}</div></Card>
        <Card className="p-4 border-border bg-[#FFF3E0]"><div className="text-xs uppercase text-[#B45309]">Discount</div><div className="h-font text-xl font-semibold tabular-nums">{money(dues?.total_discount || 0)}</div></Card>
        <Card className="p-4 border-border bg-[#FEE4E2]"><div className="text-xs uppercase text-[#B42318]">Balance Due</div><div className="h-font text-xl font-semibold tabular-nums">{money(dues?.balance || 0)}</div></Card>
      </div>

      <Tabs defaultValue="info" data-testid="student-profile-tabs">
        <TabsList>
          <TabsTrigger value="info">Information</TabsTrigger>
          <TabsTrigger value="fees" data-testid="student-profile-fees-tab">Fee Assignments</TabsTrigger>
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
              ['Scholarship', student.scholarship], ['Fee Category', student.fee_category],
              ['Remarks', student.remarks],
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
              <div className="text-sm font-medium">{dues?.assignments?.length || 0} fee assignments</div>
              {canEdit && <Button onClick={() => openAssign(null)} className="gap-2" size="sm"><Plus className="h-3.5 w-3.5" /> New Assignment</Button>}
            </div>
            <div className="space-y-3">
              {(dues?.assignments || []).length === 0 && (
                <div className="text-sm text-muted-foreground py-6 text-center">No fee assignments yet. Click "New Assignment" to add.</div>
              )}
              {(dues?.assignments || []).map((a) => {
                const plan = feePlans.find((p) => p.id === a.fee_plan_id);
                const items = a.custom_items?.length ? a.custom_items : (plan?.items || []);
                const total = items.reduce((s, it) => s + (it.amount || 0), 0);
                return (
                  <Card key={a.id} className="p-4 border-border">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-medium">{plan ? plan.name : 'Custom Assignment'}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {items.length} items • Session {a.academic_session}
                          {a.due_date && ` • Due: ${a.due_date}`}
                          {a.discount_percent > 0 && ` • ${a.discount_percent}% discount`}
                          {a.discount_amount > 0 && ` • ₹${a.discount_amount} discount`}
                        </div>
                        {a.remarks && <div className="text-xs text-muted-foreground mt-1">{a.remarks}</div>}
                      </div>
                      <div className="text-right">
                        <div className="tabular-nums font-semibold">{money(total)}</div>
                        {canEdit && (
                          <div className="flex gap-1 mt-2">
                            <Button size="sm" variant="ghost" onClick={() => openAssign(a)}><Pencil className="h-3 w-3" /></Button>
                            <Button size="sm" variant="ghost" onClick={() => deleteAssignment(a.id)}><Trash2 className="h-3 w-3 text-destructive" /></Button>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 border-t border-border pt-2 space-y-1">
                      {items.slice(0, 6).map((it, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span>{it.fee_head_name} <span className="text-muted-foreground">({it.frequency})</span></span>
                          <span className="tabular-nums">{money(it.amount)}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                );
              })}
            </div>
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
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={async () => {
                        const resp = await api.get(`/payments/${p.id}/receipt.pdf`, { responseType: 'blob' });
                        const url = window.URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
                        window.open(url, '_blank');
                      }} className="gap-1"><ReceiptIcon className="h-3.5 w-3.5" /> PDF</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>

      <EditStudentDialog open={editOpen} onOpenChange={setEditOpen} student={student} classes={classes} onSaved={load} />
      <AssignFeeDialog open={assignOpen} onOpenChange={setAssignOpen} student={student} feePlans={feePlans} feeHeads={feeHeads} existingAssignment={editingAssignment} onSaved={load} />
    </AppShell>
  );
}
