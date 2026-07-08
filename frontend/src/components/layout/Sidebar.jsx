import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard, Users, GraduationCap, Wallet, Receipt, CalendarCheck,
  BookOpen, CalendarDays, Megaphone, Image, Users2, Bell, FileBarChart,
  Settings, ShieldCheck, School, ClipboardList, HeartHandshake
} from 'lucide-react';

const navFor = {
  super_admin: [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/schools', icon: School, label: 'Schools' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/students', icon: GraduationCap, label: 'Students' },
    { to: '/fees', icon: Wallet, label: 'Fee Structures' },
    { to: '/fees/collect', icon: Receipt, label: 'Collect Fee' },
    { to: '/receipts', icon: Receipt, label: 'Receipts' },
    { to: '/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/homework', icon: BookOpen, label: 'Homework' },
    { to: '/timetable', icon: ClipboardList, label: 'Timetable' },
    { to: '/events', icon: CalendarDays, label: 'Events' },
    { to: '/circulars', icon: Megaphone, label: 'Circulars' },
    { to: '/gallery', icon: Image, label: 'Gallery' },
    { to: '/staff', icon: Users2, label: 'Staff' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/reports', icon: FileBarChart, label: 'Reports' },
    { to: '/audit-logs', icon: ShieldCheck, label: 'Audit Logs' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ],
  school_admin: [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/students', icon: GraduationCap, label: 'Students' },
    { to: '/fees', icon: Wallet, label: 'Fee Structures' },
    { to: '/fees/collect', icon: Receipt, label: 'Collect Fee' },
    { to: '/receipts', icon: Receipt, label: 'Receipts' },
    { to: '/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/homework', icon: BookOpen, label: 'Homework' },
    { to: '/timetable', icon: ClipboardList, label: 'Timetable' },
    { to: '/events', icon: CalendarDays, label: 'Events' },
    { to: '/circulars', icon: Megaphone, label: 'Circulars' },
    { to: '/gallery', icon: Image, label: 'Gallery' },
    { to: '/staff', icon: Users2, label: 'Staff' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/reports', icon: FileBarChart, label: 'Reports' },
    { to: '/audit-logs', icon: ShieldCheck, label: 'Audit Logs' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ],
  accountant: [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/fees/collect', icon: Receipt, label: 'Collect Fee' },
    { to: '/receipts', icon: Receipt, label: 'Receipts' },
    { to: '/students', icon: GraduationCap, label: 'Students' },
    { to: '/reports', icon: FileBarChart, label: 'Reports' },
  ],
  teacher: [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/homework', icon: BookOpen, label: 'Homework' },
    { to: '/students', icon: GraduationCap, label: 'Students' },
    { to: '/timetable', icon: ClipboardList, label: 'Timetable' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
  ],
  parent: [
    { to: '/parent', icon: HeartHandshake, label: 'Home' },
    { to: '/parent/pay', icon: Wallet, label: 'Pay Fees' },
    { to: '/parent/receipts', icon: Receipt, label: 'Receipts' },
    { to: '/parent/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/parent/homework', icon: BookOpen, label: 'Homework' },
    { to: '/parent/timetable', icon: ClipboardList, label: 'Timetable' },
    { to: '/parent/events', icon: CalendarDays, label: 'Events' },
    { to: '/parent/circulars', icon: Megaphone, label: 'Circulars' },
    { to: '/parent/gallery', icon: Image, label: 'Gallery' },
    { to: '/parent/notifications', icon: Bell, label: 'Notifications' },
  ],
};

export const Sidebar = () => {
  const { user } = useAuth();
  const items = navFor[user?.role] || [];
  return (
    <aside className="hidden lg:flex w-[260px] flex-col border-r border-border bg-[hsl(var(--secondary))]/40 h-[calc(100vh-56px)] sticky top-14 overflow-y-auto">
      <div className="px-3 py-4">
        <div className="text-xs uppercase tracking-wide text-muted-foreground px-2 mb-2">Navigation</div>
        <nav className="flex flex-col gap-0.5">
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.to === '/' || it.to === '/parent'}
              data-testid={`nav-${it.label.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-card text-foreground font-medium shadow-[0_1px_2px_rgba(16,24,40,0.06)] border border-border'
                    : 'text-foreground/75 hover:bg-card hover:text-foreground'
                }`
              }
            >
              <it.icon className="h-4 w-4 text-[hsl(var(--primary))]" />
              <span>{it.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
};
