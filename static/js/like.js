document.addEventListener('DOMContentLoaded', () => {
    // イベント委譲（親要素でクリックを検知）にすると、動的な変更に強くなります
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.like-btn');
        if (!btn) return;

        e.preventDefault();
        
        const url = btn.getAttribute('data-url');
        const heart = btn.querySelector('.heart');
        const countSpan = btn.querySelector('.like-count');

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // サーバー側でエラー（400など）が起きた場合
            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.error || "エラーが発生しました");
                return;
            }

            const result = await response.json();
            
            // 見た目の更新
            if (result.liked) {
                btn.classList.add('is-liked');
                heart.textContent = '❤️';
            } else {
                btn.classList.remove('is-liked');
                heart.textContent = '🤍';
            }
            
            // サーバーから返ってきた正確な数字を反映
            countSpan.textContent = result.count;

        } catch (err) {
            console.error('通信エラー:', err);
        }
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}