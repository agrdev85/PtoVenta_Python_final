document.addEventListener("DOMContentLoaded", function () {
    const telegramButton = document.querySelector('.telegram-float');
    let scrollTimeout;

    // Evento para detectar cuando se hace scroll
    window.addEventListener('scroll', () => {
        // Ocultar el botón cuando se hace scroll
        telegramButton.classList.add('telegram-hidden');

        // Mostrar el botón después de un pequeño retraso cuando se deja de hacer scroll
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            telegramButton.classList.remove('telegram-hidden');
        }, 200); // 200ms para que el botón vuelva a aparecer tras dejar de hacer scroll
    });
});