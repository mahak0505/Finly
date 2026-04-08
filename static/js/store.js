const Store = {
  getDefaults() {
    return {
      expenses: [],
      income: [],
      budgets: {
        Food: 2500,
        Travel: 1000,
        Books: 1000,
        Other: 2000,
        Accommodation: 3000,
        Fun: 1500,
        Health: 1000
      },
      goals: [],
      notifications: []
    };
  },

  init() {
    if (!localStorage.getItem('finly_expenses')) localStorage.setItem('finly_expenses', JSON.stringify(this.getDefaults().expenses));
    if (!localStorage.getItem('finly_income')) localStorage.setItem('finly_income', JSON.stringify(this.getDefaults().income));
    if (!localStorage.getItem('finly_budgets')) localStorage.setItem('finly_budgets', JSON.stringify(this.getDefaults().budgets));
    if (!localStorage.getItem('finly_goals')) localStorage.setItem('finly_goals', JSON.stringify(this.getDefaults().goals));
    if (!localStorage.getItem('finly_notifications')) localStorage.setItem('finly_notifications', JSON.stringify(this.getDefaults().notifications));
  },

  get(key) {
    return JSON.parse(localStorage.getItem(`finly_${key}`));
  },

  set(key, data) {
    localStorage.setItem(`finly_${key}`, JSON.stringify(data));
  },

  addExpense(name, cat, amt, note) {
    const exps = this.get('expenses');
    exps.unshift({
      id: Date.now().toString(),
      name,
      cat,
      amt: parseFloat(amt),
      note,
      date: new Date().toISOString()
    });
    this.set('expenses', exps);
  },

  addGoal(name, target) {
    const goals = this.get('goals');
    goals.push({
      id: Date.now().toString(),
      name: `🎯 ${name}`,
      current: 0,
      target: parseFloat(target),
      colors: ['#3B82F6', '#60A5FA']
    });
    this.set('goals', goals);
  },

  updateBudget(cat, val) {
    const b = this.get('budgets');
    b[cat] = parseFloat(val);
    this.set('budgets', b);
  },

  formatMoney(amt) {
    return '₹' + parseFloat(amt).toLocaleString('en-IN');
  },

  formatDate(isoStr) {
    const d = new Date(isoStr);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) return 'Today';
    const yest = new Date(today); yest.setDate(yest.getDate() - 1);
    if (d.toDateString() === yest.toDateString()) return 'Yesterday';
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  }
};

// Initialize on load - DEACTIVATED FOR NATIVE DJANGO RENDER
// Store.init();

// --- UI HELPERS ---
function toggleDropdown(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const isActive = el.classList.contains('active');
  document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
  if (!isActive) el.classList.add('active');
}

function closeModals() {
  document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
}

function openModal(id) {
  closeModals();
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
}

// Global click to close dropdowns
document.addEventListener('click', (e) => {
  if (!e.target.closest('.tb-notif') && !e.target.closest('.tb-av') && !e.target.closest('.dropdown')) {
    document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
  }
});

// Notification dropdown — no profile overwriting, just notifications
document.addEventListener('DOMContentLoaded', () => {
  const notifDd = document.getElementById('notifDropdown');
  if (notifDd) {
    const notifs = Store.get('notifications');
    let html = '<div class="dd-hdr">Notifications</div>';
    if (!notifs || notifs.length === 0) {
      html += '<div class="no-data">No new notifications</div>';
    } else {
      notifs.forEach(n => {
        html += `<div class="dd-item">
          <div class="dd-note"><span class="dd-note-ico">🤖</span> <span>${n.text}</span></div>
          <div style="font-size:.6rem; color:var(--text-muted); margin-top:4px; padding-left:28px;">${Store.formatDate(n.date)}</div>
        </div>`;
      });
    }
    notifDd.innerHTML = html;
    if (notifs && notifs.length > 0) {
      document.querySelectorAll('.notif-badge').forEach(b => b.style.display = 'block');
    }
  }
});