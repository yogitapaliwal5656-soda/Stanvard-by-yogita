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
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Plus, User as UserIcon, Pencil, Trash2, KeyRound, Search } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';

const ROLES = ['super_admin', 'school_admin', 'accountant', 'teacher', 'parent'];

export default function UsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [schools, setSchools] = useState([]);
  const [students, setStudents] = useState([]);
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');
  const [openAdd, setOpenAdd] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [resetUser, setResetUser] = useState(null);

  const load = async () => {
    const [{ data: u }, { data: s }, { data: st }] = await Promise.all([
      api.get('/users'), api.get('/schools'), api.get('/students', { params: { limit: 2000 } })
    ]);
    setUsers(u); setSchools(s); setStudents(st);
  };
  useEffect(() => { load(); }, []);
  const schoolMap = Object.fromEntries(schools.map((s) => [s.id, s.name.replace('Stanvard School - ', '')]));
  const studentMap = Object.fromEntries(students.map((s) => [s.id, `${s.full_name} (${s.admission_number})`]));

  const roleTabs = { all: 'All', school_admin: 'Admins', accountant: 'Accountants', teacher: 'Teachers', parent: 'Parents' };
  const filtered = users.filter((u) => {
    if (tab !== 'all' && u.role !== tab) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!(u.full_name || '').toLowerCase().includes(q) && !(u.email || '').toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const del = async (u) => {
    if (!window.confirm(`Deactivate user ${u.full_name}? (This soft-deletes them.)`)) return;
    try { await api.delete(`/users/${u.id}`); toast.success('User deactivated'); load(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
  };

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="h-font text-2xl font-semibold">Users</h1><p className="text-sm text-muted-foreground">Administrators, staff, teachers, and parents.</p></div>
        <Button onClick={() => setOpenAdd(true)} className="gap-2" data-testid="users-add-button"><Plus className="h-4 w-4" /> New User</Button>
      </div>

      <Card className="p-4 border-border mb-4">
        <Tabs value={tab} onValueChange={setTab}>
          <div className="flex flex-col md:flex-row md:items-center gap-3">
            <TabsList>
              {Object.entries(roleTabs).map(([k, v]) => <TabsTrigger key={k} value={k} data-testid={`users-tab-${k}`}>{v}</TabsTrigger>)}
            </TabsList>
            <div className="relative flex-1 min-w-[240px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search name or email…" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="users-search" />
            </div>
          </div>
        </Tabs>
      </Card>

      <Card className="border-border">
        <Table>
          <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Email</TableHead><TableHead>Role</TableHead><TableHead>School</TableHead><TableHead>Linked</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
          <TableBody>
            {filtered.length === 0 && <TableRow><TableCell colSpan={7} className="py-8 text-center text-muted-foreground text-sm">No users found.</TableCell></TableRow>}
            {filtered.map((u) => (
              <TableRow key={u.id} className="hover:bg-secondary/40">
                <TableCell><div className="flex items-center gap-2"><div className="h-7 w-7 rounded-full bg-secondary flex items-center justify-center"><UserIcon className="h-3.5 w-3.5" /></div><span className="font-medium">{u.full_name}</span></div></TableCell>
                <TableCell className="text-muted-foreground">{u.email}</TableCell>
                <TableCell><Badge variant="secondary" className="capitalize">{(u.role || '').replace('_', ' ')}</Badge></TableCell>
                <TableCell>{schoolMap[u.school_id] || '—'}</TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {u.role === 'parent' && u.linked_student_id ? studentMap[u.linked_student_id] || '—' : '—'}
                </TableCell>
                <TableCell><Badge className={u.status === 'active' ? 'bg-[#E6F6F4] text-[#0F766E] border border-[#BFEAE6]' : 'bg-secondary'}>{u.status}</Badge></TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button size="sm" variant="ghost" onClick={() => setEditUser(u)} data-testid={`user-edit-${u.id}`} title="Edit"><Pencil className="h-3.5 w-3.5" /></Button>
                    <Button size="sm" variant="ghost" onClick={() => setResetUser(u)} title="Reset password"><KeyRound className="h-3.5 w-3.5" /></Button>
                    <Button size="sm" variant="ghost" onClick={() => del(u)} title="Deactivate"><Trash2 className="h-3.5 w-3.5 text-destructive" /></Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <UserFormDialog
        open={openAdd || !!editUser}
        onOpenChange={(v) => { setOpenAdd(v); if (!v) setEditUser(null); }}
        schools={schools}
        students={students}
        isSuper={user?.role === 'super_admin'}
        editUser={editUser}
        onSaved={load}
      />
      <ResetPasswordDialog user={resetUser} onOpenChange={() => setResetUser(null)} />
    </AppShell>
  );
}

function UserFormDialog({ open, onOpenChange, schools, students, isSuper, editUser, onSaved }) {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'teacher', school_id: '', phone: '', linked_student_id: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (editUser) {
      setForm({
        email: editUser.email, password: '', full_name: editUser.full_name || '',
        role: editUser.role, school_id: editUser.school_id || '',
        phone: editUser.phone || '', linked_student_id: editUser.linked_student_id || '',
      });
    } else if (open) {
      setForm({ email: '', password: '', full_name: '', role: 'teacher', school_id: '', phone: '', linked_student_id: '' });
    }
  }, [editUser, open]);

  const filteredStudents = students.filter((s) => !form.school_id || s.school_id === form.school_id);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editUser) {
        const payload = { full_name: form.full_name, role: form.role, school_id: form.school_id || null, phone: form.phone, linked_student_id: form.linked_student_id || null };
        if (form.password) payload.password = form.password;
        await api.patch(`/users/${editUser.id}`, payload);
        toast.success('User updated');
      } else {
        await api.post('/users', form);
        toast.success('User created');
      }
      onOpenChange(false); onSaved();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader><DialogTitle>{editUser ? `Edit ${editUser.full_name}` : 'New User'}</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="grid gap-4">
          <div className="grid gap-1.5"><Label>Full Name</Label><Input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} data-testid="user-form-name" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5"><Label>Email</Label><Input required type="email" disabled={!!editUser} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="user-form-email" /></div>
            <div className="grid gap-1.5"><Label>{editUser ? 'New Password (optional)' : 'Password'}</Label><Input type="password" required={!editUser} minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} data-testid="user-form-password" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5"><Label>Role</Label>
              <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                <SelectTrigger data-testid="user-form-role"><SelectValue /></SelectTrigger>
                <SelectContent>{(isSuper ? ROLES : ROLES.filter((r) => r !== 'super_admin')).map((r) => <SelectItem key={r} value={r}>{r.replace('_', ' ')}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            {isSuper && form.role !== 'super_admin' && (
              <div className="grid gap-1.5"><Label>School</Label>
                <Select value={form.school_id} onValueChange={(v) => setForm({ ...form, school_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Assign school" /></SelectTrigger>
                  <SelectContent>{schools.map((s) => <SelectItem key={s.id} value={s.id}>{s.name.replace('Stanvard School - ', '')}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5"><Label>Phone</Label><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
            {form.role === 'parent' && (
              <div className="grid gap-1.5"><Label>Linked Student</Label>
                <Select value={form.linked_student_id} onValueChange={(v) => setForm({ ...form, linked_student_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Select student" /></SelectTrigger>
                  <SelectContent className="max-h-64">{filteredStudents.slice(0, 200).map((s) => <SelectItem key={s.id} value={s.id}>{s.full_name} ({s.admission_number})</SelectItem>)}</SelectContent>
                </Select>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} data-testid="user-form-submit">{saving ? 'Saving…' : editUser ? 'Save Changes' : 'Create User'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ResetPasswordDialog({ user, onOpenChange }) {
  const [pw, setPw] = useState('');
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (user) setPw(''); }, [user]);
  const submit = async (e) => {
    e.preventDefault(); setSaving(true);
    try { await api.post(`/users/${user.id}/reset-password`, { password: pw }); toast.success(`Password reset for ${user.email}`); onOpenChange(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSaving(false); }
  };
  return (
    <Dialog open={!!user} onOpenChange={() => onOpenChange()}>
      <DialogContent>
        <DialogHeader><DialogTitle>Reset Password</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="grid gap-4">
          <div className="text-sm text-muted-foreground">Set a new password for <b>{user?.email}</b>. The user should change it after next login.</div>
          <div className="grid gap-1.5"><Label>New Password</Label><Input required minLength={6} type="text" value={pw} onChange={(e) => setPw(e.target.value)} data-testid="reset-password-input" /></div>
          <DialogFooter>
            <Button variant="outline" type="button" onClick={onOpenChange}>Cancel</Button>
            <Button type="submit" disabled={saving} data-testid="reset-password-submit">{saving ? 'Saving…' : 'Reset Password'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
