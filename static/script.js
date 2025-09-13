document.addEventListener('DOMContentLoaded', function() {
    const buyButtons = document.querySelectorAll('.buy-btn');
    buyButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.id;
            if (confirm(`Вы уверены, что хотите купить товар за ${this.dataset.price} кибиков?`)) {
                window.location.href = `/buy/${productId}`;
            }
        });
    });
});
