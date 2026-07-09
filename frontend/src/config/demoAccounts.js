// Demo account presets for the login screen "click-to-fill" helper.
// These are seeded demo accounts only, not production secrets.
// To disable the demo panel, set REACT_APP_SHOW_DEMO_ACCOUNTS="false".
// To point at your own demo accounts, override via a JSON string in
// REACT_APP_DEMO_ACCOUNTS_JSON (array of {role,email,password}).
const DEFAULT_DEMO = [
  { id: 'super', role: 'Super Admin', email: 'superadmin@stanvard.school', password: 'super123' },
  { id: 'admin-gn', role: 'School Admin (GN)', email: 'admin.gn@stanvard.school', password: 'admin123' },
  { id: 'acc-gn', role: 'Accountant (GN)', email: 'accountant.gn@stanvard.school', password: 'acc123' },
  { id: 'teacher-gn', role: 'Teacher (GN)', email: 'teacher.gn@stanvard.school', password: 'teacher123' },
  { id: 'parent-gn', role: 'Parent (GN)', email: 'parent.gn20250001@stanvard.school', password: 'parent123' },
];

export const DEMO_ACCOUNTS_ENABLED = String(process.env.REACT_APP_SHOW_DEMO_ACCOUNTS ?? 'true') !== 'false';

export function getDemoAccounts() {
  if (!DEMO_ACCOUNTS_ENABLED) return [];
  const override = process.env.REACT_APP_DEMO_ACCOUNTS_JSON;
  if (override) {
    try {
      const parsed = JSON.parse(override);
      if (Array.isArray(parsed)) {
        return parsed.map((a, i) => ({ id: a.id || `demo-${i}`, role: a.role || 'User', email: a.email, password: a.password }));
      }
    } catch (e) {
      // fall through to default
    }
  }
  return DEFAULT_DEMO;
}
