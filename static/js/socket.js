document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    // Обработка новых постов
    socket.on('post_added', function(data) {
        if (window.location.pathname === '/' + data.board + '/') {
            location.reload();
        }
    });
    
    // Обработка новых ответов
    socket.on('reply_added', function(data) {
        if (window.location.pathname === '/' + data.board + '/' + data.thread + '/') {
            location.reload();
        }
    });
    
    // Обработка ошибок соединения
    socket.on('connect_error', function(error) {
        console.error('Ошибка соединения:', error);
    });
    
    // Автоматическое переподключение
    socket.on('disconnect', function() {
        console.log('Отключено от сервера. Попытка переподключения...');
    });
});