const YEARS = ['1st Year','2nd Year','3rd Year','4th Year'];

/* ---- Animated Counter ---- */
function animateCounter(el, target, duration = 1200) {
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start += step;
    if (start >= target) { el.textContent = target; clearInterval(timer); return; }
    el.textContent = Math.floor(start);
  }, 16);
}

function initCounters() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10);
    if (!isNaN(target)) animateCounter(el, target);
  });
}

/* ---- Year Tabs ---- */
function showYear(y) {
  YEARS.forEach(yr => {
    const el = document.getElementById(yr);
    if (el) el.classList.add('d-none');
  });
  const section = document.getElementById(y);
  if (section) {
    section.classList.remove('d-none');
    section.classList.remove('year-section');
    void section.offsetWidth;
    section.classList.add('year-section');
  }
  document.querySelectorAll('.year-tab').forEach(b => b.classList.remove('active'));
  const btn = [...document.querySelectorAll('.year-tab')].find(b => b.textContent.trim() === y);
  if (btn) btn.classList.add('active');
  const navEl = document.querySelector('.year-nav-wrap');
  if (navEl) window.scrollTo({ top: navEl.offsetTop - 20, behavior: 'smooth' });
}

/* ---- Section Tabs within Group Cards ---- */
function showSection(groupId, secDivId) {
  document.querySelectorAll('[data-group="' + groupId + '"]').forEach(el => el.classList.add('d-none'));
  const target = document.getElementById(secDivId);
  if (target) target.classList.remove('d-none');
  document.querySelectorAll('[data-sec-tab="' + groupId + '"]').forEach(tab => {
    tab.classList.remove('active');
    if (tab.dataset.secTarget === secDivId) tab.classList.add('active');
  });
}

/* ---- Generate with Loading Overlay ---- */
function generateTimetable() {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) overlay.classList.add('active');
  window.location.href = '/generate';
}

/* ---- PDF: Single Section ---- */
function downloadSection(secDivId, filename) {
  const el = document.getElementById(secDivId);
  if (!el) { alert('Element not found!'); return; }
  const opt = {
    margin: 8,
    filename: filename || 'timetable.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, logging: false },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
  };
  html2pdf().set(opt).from(el).save();
}

/* ---- PDF: All ---- */
function downloadAll() {
  const el = document.getElementById('all');
  if (!el) return;
  const opt = {
    margin: 8,
    filename: 'All_Timetables.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, logging: false },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
  };
  html2pdf().set(opt).from(el).save();
}

/* ---- PDF: Instructor ---- */
function downloadInstructor(name) {
  const cards = document.querySelectorAll('.group-card');
  let target = null;
  cards.forEach(card => {
    const header = card.querySelector('.group-card-header');
    if (header && header.textContent.trim().startsWith(name)) target = card;
  });
  if (!target) { alert('Card not found!'); return; }
  const opt = {
    margin: 8,
    filename: name.replace(/\s+/g, '_') + '_Schedule.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, logging: false },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
  };
  html2pdf().set(opt).from(target).save();
}

/* ---- Instructor Search ---- */
function searchInstructors(query) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll('.instructor-card').forEach(card => {
    const name = card.dataset.instructor || '';
    card.closest('.group-card').style.display = (!q || name.toLowerCase().includes(q)) ? '' : 'none';
  });
}

/* ---- Ripple Effect ---- */
document.addEventListener('click', function(e) {
  const btn = e.target.closest('.btn-glass, .btn-white, .btn-gen, .btn-dl, .year-tab, .sec-tab, .jump-pill');
  if (!btn) return;
  const circle = document.createElement('span');
  const d = Math.max(btn.clientWidth, btn.clientHeight);
  const rect = btn.getBoundingClientRect();
  circle.style.cssText =
    'width:' + d + 'px;height:' + d + 'px;' +
    'left:' + (e.clientX - rect.left - d/2) + 'px;' +
    'top:'  + (e.clientY - rect.top  - d/2) + 'px;' +
    'position:absolute;border-radius:50%;' +
    'background:rgba(255,255,255,0.3);pointer-events:none;' +
    'transform:scale(0);animation:ripple 0.5s linear;';
  const prev = btn.style.cssText;
  btn.style.position = 'relative';
  btn.style.overflow  = 'hidden';
  btn.appendChild(circle);
  setTimeout(() => { circle.remove(); }, 520);
});

/* ---- Init ---- */
document.addEventListener('DOMContentLoaded', () => {
  initCounters();
  const searchEl = document.getElementById('instructorSearch');
  if (searchEl) searchEl.addEventListener('input', e => searchInstructors(e.target.value));
});

/* Add ripple keyframe */
const _style = document.createElement('style');
_style.textContent = '@keyframes ripple{to{transform:scale(4);opacity:0;}}';
document.head.appendChild(_style);
