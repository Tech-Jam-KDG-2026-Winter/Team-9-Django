document.addEventListener('DOMContentLoaded', () => {
    let startTime, timerInterval, elapsedTime = 0;

    const display = document.getElementById('timerDisplay');
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const finishBtn = document.getElementById('finishBtn');

    // ボタンが存在しないページでのエラーを防ぐ
    if (!startBtn) return;

    function timeToString(time) {
        let hh = Math.floor(time / 3600000);
        let mm = Math.floor((time % 3600000) / 60000);
        let ss = Math.floor((time % 60000) / 1000);
        return `${hh.toString().padStart(2, "0")}:${mm.toString().padStart(2, "0")}:${ss.toString().padStart(2, "0")}`;
    }

    function updateTimer() {
        elapsedTime = Date.now() - startTime;
        display.textContent = timeToString(elapsedTime);
    }

    startBtn.addEventListener('click', () => {
        startTime = Date.now() - elapsedTime;
        timerInterval = setInterval(updateTimer, 1000);
        
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'inline-block';
        finishBtn.style.display = 'inline-block';
        
        window.onbeforeunload = () => "運動中ですが終了しますか？";
    });

    pauseBtn.addEventListener('click', () => {
        clearInterval(timerInterval);
        startBtn.textContent = '再開';
        startBtn.style.display = 'inline-block';
        pauseBtn.style.display = 'none';
    });

    finishBtn.addEventListener('click', () => {
        if (!confirm("運動を終了して記録を入力しますか？")) return;
        
        clearInterval(timerInterval);
        window.onbeforeunload = null;

        const finalTime = display.textContent;
        const resId = document.getElementById('resId').value;
        
        window.location.href = `/reservations/${resId}/complete/?time=${finalTime}`;
    });
});