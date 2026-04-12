/*
Copyright © Sabarna Barik 

This code is open-source for **educational and non-commercial purposes only**.

You may:
- Read, study, and learn from this code.
- Modify or experiment with it for personal learning.

You may NOT:
- Claim this code as your own.
- Use this code in commercial projects or for profit without written permission.
- Distribute this code as your own work.

If you use or adapt this code, you **must give credit** to the original author: Sabarna Barik
For commercial use or special permissions, contact: sabarnabarik@gmail.com

# Copyright © 2026 Sabarna Barik
# Non-commercial use only. Credit required if used.

License:
This project is open-source for learning only.
Commercial use is prohibited.
Credit is required if you use any part of this code.
*/

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
