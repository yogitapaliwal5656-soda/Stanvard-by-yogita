import React, { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, User as UserIcon } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';

export default function UsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [schools, setSchools] = useState([]);
  const [open, setOpen] = useState(false);
  const load = async () => { const [{ data: u }, { data: s }] = await Promise.all([api.get('/users'), api.get('/schools')]); setUsers(u); setSchools(s); };
  useEffect(() => { load(); }, []);
  const schoolMap = Object.fromEntries(schools.map((s) => [s.id, s.name.replace('Stanvard School - ', '')]));
  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="h-font text-2xl font-semibold">Users</h1><p className="text-sm text-muted-foreground">All administrators, staff, and parents.</p></div>
        <Button onClick={() => setOpen(true)} className="gap-2"><Plus className="h-4 w-4" /> New User</Button>
      </div>
      <Card className="border-border">
        <Table>
          <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Email</TableHead><TableHead>Role</TableHead><TableHead>School</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id}>
                <TableCell><div className="flex items-center gap-2"><div className="h-7 w-7 rounded-full bg-secondary flex items-center justify-center"><UserIcon className="h-3.5 w-3.5" /></div><span className="font-medium">{u.full_name}</span></div></TableCell>
                <TableCell className="text-muted-foreground">{u.email}</TableCell>
                <TableCell><Badge variant="secondary" className="capitalize">{(u.role || '').replace('_', ' ')}</Badge></TableCell>
                <TableCell>{schoolMap[u.school_id] || '— (Super)'}</TableCell>
                <TableCell><Badge className={u.status === 'active' ? 'bg-[#E6F6F4] text-[#0F766E] border border-[#BFEAE6]' : 'bg-secondary'}>{u.status}</Badge></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
      <AddUser open={open} onOpenChange={setOpen} schools={schools} isSuper={user?.role === 'super_admin'} onSaved={load} />
    </AppShell>
  );
}

function AddUser({ open, onOpenChange, schools, isSuper, onSaved }) {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'school_admin', school_id: '' });
  const [saving, setSaving] = useState(false);
  const submit = async (e) => { e.preventDefault(); setSaving(true);
    try { await api.post('/users', form); toast.success('User created'); onOpenChange(false); onSaved(); setForm({ email: '', password: '', full_name: '', role: 'school_admin', school_id: '' }); }
    catch (err) { toast.error(err.response?.data?.detail || 'Failed'); } finally { setSaving(false); }
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent><DialogHeader><DialogTitle>New User</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="grid gap-4">
          <div className="grid gap-1.5"><Label>Full Name</Label><Input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5"><Label>Email</Label><Input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
            <div className="grid gap-1.5"><Label>Password</Label><Input required type="password" minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5"><Label>Role</Label>
              <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>
                {(isSuper ? ['super_admin', 'school_admin', 'accountant', 'teacher', 'parent'] : ['school_admin', 'accountant', 'teacher', 'parent']).map((r) => <SelectItem key={r} value={r}>{r.replace('_', ' ')}</SelectItem>)}
              </SelectContent></Select>
            </div>
            {isSuper && form.role !== 'super_admin' && (
              <div className="grid gap-1.5"><Label>School</Label>
                <Select value={form.school_id} onValueChange={(v) => setForm({ ...form, school_id: v })}><SelectTrigger><SelectValue placeholder="Assign school" /></SelectTrigger><SelectContent>{schools.map((s) => <SelectItem key={s.id} value={s.id}>{s.name.replace('Stanvard School - ', '')}</SelectItem>)}</SelectContent></Select>
              </div>
            )}
          </div>
          <DialogFooter><Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Create User'}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
