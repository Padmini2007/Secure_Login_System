// ── Password Visibility Toggle ───────────────────────────────────────────────
function togglePassword(id) {
  const inp = document.getElementById(id);
  if (!inp) return;
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

// ── Password Strength Meter ───────────────────────────────────────────────────
function checkStrength(val) {
  const bar   = document.getElementById('strength-bar');
  const label = document.getElementById('strength-label');
  if (!bar || !label) return;

  let score = 0;
  if (val.length >= 8)                          score++;
  if (/[A-Z]/.test(val))                        score++;
  if (/[a-z]/.test(val))                        score++;
  if (/\d/.test(val))                           score++;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(val))      score++;

  const levels = [
    { pct: '0%',   color: 'transparent',                   text: '' },
    { pct: '20%',  color: '#ef4444',                        text: 'Very weak' },
    { pct: '40%',  color: '#f97316',                        text: 'Weak' },
    { pct: '60%',  color: '#eab308',                        text: 'Fair' },
    { pct: '80%',  color: '#22c55e',                        text: 'Strong' },
    { pct: '100%', color: '#00d1ff',                        text: 'Very strong ✓' },
  ];

  const lvl = levels[score] || levels[0];
  bar.style.width      = lvl.pct;
  bar.style.background = lvl.color;
  label.textContent    = lvl.text;
  label.style.color    = lvl.color;
}

// ── Auto-dismiss Flash Messages ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.5s ease';
    setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });

  // OTP input: auto-format spacing
  const otpInput = document.querySelector('.mono-input');
  if (otpInput) {
    otpInput.addEventListener('input', e => {
      e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
    });
  }

  // Animate stat cards on load
  document.querySelectorAll('.stat-card').forEach((card, i) => {
    card.style.opacity   = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = `opacity 0.4s ease ${i * 0.08}s, transform 0.4s ease ${i * 0.08}s`;
    requestAnimationFrame(() => {
      card.style.opacity   = '1';
      card.style.transform = 'translateY(0)';
    });
  });

  // Animate security rows
  document.querySelectorAll('.security-row').forEach((row, i) => {
    row.style.opacity   = '0';
    row.style.transform = 'translateX(-12px)';
    row.style.transition = `opacity 0.4s ease ${0.3 + i * 0.1}s, transform 0.4s ease ${0.3 + i * 0.1}s`;
    requestAnimationFrame(() => {
      row.style.opacity   = '1';
      row.style.transform = 'translateX(0)';
    });
  });
});
