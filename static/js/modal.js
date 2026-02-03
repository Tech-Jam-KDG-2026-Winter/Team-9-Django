// 要素の取得
const modal = document.getElementById('checkinModal');
const openModalBtn = document.getElementById('openModalBtn');
const confirmBtn = document.getElementById('confirmCheckin');
const cancelBtn = document.getElementById('cancelCheckin');
const checkinForm = document.getElementById('checkinForm');

// 1. チェックインボタンを押したらモーダルを表示
openModalBtn.addEventListener('click', () => {
  modal.style.display = 'block';
});

// 2. キャンセルを押したらモーダルを閉じる
cancelBtn.addEventListener('click', () => {
  modal.style.display = 'none';
});

// 3. 「開始」を押したらフォームを送信
confirmBtn.addEventListener('click', () => {
  checkinForm.submit();
});

// モーダルの外側をクリックした時に閉じる（お好みで）
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = 'none';
  }
}