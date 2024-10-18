document.querySelectorAll('.star').forEach(star => {
    star.addEventListener('mouseenter', () => {
        star.style.transform = 'scale(1.2)';
    });
    
    star.addEventListener('mouseleave', () => {
        star.style.transform = 'scale(1)';
    });
});
