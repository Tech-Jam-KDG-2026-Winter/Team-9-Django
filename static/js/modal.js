document.addEventListener('DOMContentLoaded', () => {
  // ページ内のすべての「チェックインボタン」を取得
  const openButtons = document.querySelectorAll('.open-modal-btn');

  // modal.js の表示部分を修正
  openButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const container = btn.closest('.checkin-container');
      const modal = container.querySelector('.checkin-modal');
      if (modal) {
        modal.style.display = 'flex'; // blockではなくflexにすることで中央揃えを維持
        
        // キャンセルボタン（×とリンク両方）
        modal.querySelectorAll('.cancel-checkin').forEach(el => {
          el.onclick = () => modal.style.display = 'none';
        });

        // 開始ボタン
        modal.querySelector('.confirm-checkin').onclick = () => {
          container.querySelector('.checkin-form').submit();
        };
      }
    });
  });

  // モーダルの外側（暗い背景部分）をクリックした時に閉じる共通処理
  window.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal')) {
      event.target.style.display = 'none';
    }
  });
});

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

async function logout() {
  const csrftoken = getCookie("csrftoken");
  const res = await fetch("/auth/logout/", {
    method: "POST",
    headers: { "X-CSRFToken": csrftoken },
    credentials: "include"
  });

  if (res.ok) {
    window.location.href = "/auth/login/";
  }
}