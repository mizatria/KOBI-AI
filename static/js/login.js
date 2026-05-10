document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    // FastAPI OAuth2PasswordRequestForm veriyi form-urlencoded formatında bekler
    const formData = new URLSearchParams();
    formData.append('username', document.getElementById('username').value);
    formData.append('password', document.getElementById('password').value);

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            // Başarılı: Token'ı tarayıcıya kaydet
            localStorage.setItem('access_token', result.access_token);
            alert("Giriş Başarılı!");
            window.location.href = "/"; // Başarılıysa ana sayfaya git
        } else {
            // Hata: FastAPI'den gelen hata mesajını göster
            alert("Hata: " + (result.detail || "Giriş başarısız. Bilgilerinizi kontrol edin."));
        }
    } catch (error) {
        console.error("İstek hatası:", error);
        alert("Sunucuyla iletişim kurulamadı.");
    }
});