/* MyLibrary - Common JavaScript */

// Toggle nav on mobile
function toggleNav() {
  document.getElementById('navMenu').classList.toggle('open');
}

// Toggle password visibility
function togglePass(id, btn) {
  const inp = document.getElementById(id);
  if (!inp) return;
  if (inp.type === 'password') {
    inp.type = 'text';
    btn.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
  } else {
    inp.type = 'password';
    btn.innerHTML = '<i class="fa-solid fa-eye"></i>';
  }
}

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(el => {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    });
  }, 5000);

  // Close nav on outside click (mobile)
  document.addEventListener('click', (e) => {
    const menu = document.getElementById('navMenu');
    if (menu && menu.classList.contains('open')) {
      if (!e.target.closest('.glass-nav')) {
        menu.classList.remove('open');
      }
    }
  });
});
