document.addEventListener('DOMContentLoaded', function () {

  // Валидация форм login и register
  const authForm = document.getElementById('login-form') ||
                   document.getElementById('register-form');

  if (authForm) {
    authForm.addEventListener('submit', function (e) {
      const username = document.getElementById('username');
      const password = document.getElementById('password');
      let valid = true;

      if (username && username.value.trim().length < 3) {
        showFieldError(username, 'Minimum 3 characters');
        valid = false;
      }
      if (password && password.value.length < 6) {
        showFieldError(password, 'Minimum 6 characters');
        valid = false;
      }
      if (!valid) e.preventDefault();
    });
  }

  function showFieldError(input, message) {
    input.style.borderColor = 'var(--danger-color)';
    let hint = input.parentElement.querySelector('.field-error');
    if (!hint) {
      hint = document.createElement('span');
      hint.className = 'hint field-error';
      hint.style.color = 'var(--danger-color)';
      input.parentElement.appendChild(hint);
    }
    hint.textContent = message;
    input.addEventListener('input', function () {
      input.style.borderColor = '';
      if (hint) hint.remove();
    }, { once: true });
  }

  // Подтверждение перед удалением
  function bindDeleteConfirm(scope) {
    scope.querySelectorAll('.delete-form').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        if (!confirm('Delete? This action cannot be undone.')) {
          e.preventDefault();
        }
      });
    });
  }
  bindDeleteConfirm(document);

  // Поиск по таблице пользователей (fetch)
  const searchInput = document.getElementById('search-input');
  const tbody       = document.getElementById('users-tbody');

  if (searchInput && tbody) {
    let timer;
    searchInput.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        const q = searchInput.value.trim();
        fetch('/admin/users/search?q=' + encodeURIComponent(q))
          .then(function (res) { return res.json(); })
          .then(function (users) { renderUsers(users); })
          .catch(function (err) { console.error('Search error:', err); });
      }, 300);
    });
  }

  function renderUsers(users) {
    tbody.innerHTML = '';
    if (users.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="muted" style="padding:1rem;text-align:center">Nothing found</td></tr>';
      return;
    }
    const currentUser = tbody.dataset.currentUser;
    users.forEach(function (u) {
      const isSelf = currentUser === u.id;
      const dept   = u.department ? u.department : '—';
      const salary = u.salary ? u.salary : '—';
      tbody.innerHTML += `
        <tr>
          <td><span style="font-family:var(--font-mono);font-size:0.8rem">${u.id.slice(0, 8)}</span></td>
          <td>
            <div class="cell-user">
              <div class="avatar">${u.username[0].toUpperCase()}</div>
              <span class="meta-name">${u.username}</span>
            </div>
          </td>
          <td>${dept}</td>
          <td>${salary}</td>
          <td><span class="badge ${u.role}">${u.role}</span></td>
          <td>${u.created_at.slice(0, 10)}</td>
          <td>
            <div class="toolbar">
              <button type="button" class="btn btn-secondary btn-sm"
                      onclick="openEditModal('${u.id}','${u.username}','${u.role}','${u.department || ''}','${u.salary || ''}')">Edit</button>
              ${isSelf ? '<span class="muted">—</span>' : `
              <form method="POST" action="/admin/users/delete/${u.id}" class="delete-form">
                <button type="submit" class="btn btn-danger btn-sm">Delete</button>
              </form>`}
            </div>
          </td>
        </tr>`;
    });
    // переподключаем confirm для новых форм
    bindDeleteConfirm(tbody);
  }

  // Закрытие flash-сообщений
  document.querySelectorAll('.flash .close').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.closest('.flash').remove();
    });
  });

  // Мобильное меню
  const menuToggle = document.getElementById('menu-toggle');
  const navLinks   = document.getElementById('navbar-links');
  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', function () {
      navLinks.classList.toggle('open');
    });
  }

});