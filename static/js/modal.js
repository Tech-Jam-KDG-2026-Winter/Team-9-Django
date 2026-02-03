document.addEventListener('DOMContentLoaded', () => {
  /**
   * 1. チェックイン用モーダルの制御
   * 共通のモーダル (globalCheckinModal) をボタンごとにURLを書き換えて使い回します
   */
  const checkinModal = document.getElementById('globalCheckinModal');
  const checkinForm = document.getElementById('globalCheckinForm');
  const openCheckinButtons = document.querySelectorAll('.open-modal-btn');

  if (checkinModal && checkinForm) {
    openCheckinButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const actionUrl = btn.getAttribute('data-url');
        checkinForm.setAttribute('action', actionUrl);
        checkinModal.style.display = 'flex';
      });
    });
  }

  /**
   * 2. リカバリー用モーダルの制御
   * 未達成の予約を復活させるためのポップアップ
   */
  const recoveryModal = document.getElementById('globalRecoveryModal');
  const recoveryForm = document.getElementById('globalRecoveryForm');
  const openRecoveryButtons = document.querySelectorAll('.open-recovery-modal-btn');

  if (recoveryModal && recoveryForm) {
    openRecoveryButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const actionUrl = btn.getAttribute('data-url');
        recoveryForm.setAttribute('action', actionUrl);
        recoveryModal.style.display = 'flex';
      });
    });
  }

  /**
   * 3. 自動成功ポップアップの制御
   * Djangoからメッセージが届いている場合にページ読み込み時に自動で表示
   */
  const successModal = document.getElementById('successModal');
  const messageText = document.getElementById('successMessageText');

  // メッセージの中身が存在する場合のみ表示
  if (successModal && messageText && messageText.textContent.trim() !== "") {
    successModal.style.display = 'flex';
  }

  /**
   * 4. 閉じる処理の共通化
   * 「×ボタン」「キャンセルボタン」「背景クリック」のすべてに対応
   */
  const allModals = [checkinModal, recoveryModal, successModal];

  // 全モーダル内の「閉じる」系要素をすべて取得
  // (IDが closeModalX, closeModalBtn, closeRecoveryModalX, closeRecoveryModalBtn など)
  const closeElements = document.querySelectorAll(`
    [id^="closeModal"], 
    [id^="closeRecoveryModal"], 
    .close-x, 
    .btn-link
  `);

  closeElements.forEach(el => {
    el.addEventListener('click', () => {
      allModals.forEach(modal => {
        if (modal) modal.style.display = 'none';
      });
    });
  });

  // モーダルの外側（暗い背景）をクリックした時に閉じる
  window.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal')) {
      event.target.style.display = 'none';
    }
  });
});