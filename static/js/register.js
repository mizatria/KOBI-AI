document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (response.ok) {
        alert("Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz.");
        window.location.href = "/auth/login";
    } else {
        const error = await response.json();
        alert("Hata: " + error.detail);
    }
});