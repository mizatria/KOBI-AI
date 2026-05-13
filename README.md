#KOPİ: KOBİ'ler İçin Yapay Zeka Destekli Operasyonel Yönetim Platformu
KOPİ, küçük ve orta ölçekli işletmelerin (KOBİ) operasyonel kaosunu yönetmek için geliştirilmiş, AI destekli bir işletme yönetim platformudur. Manuel süreçleri otomatize ederek, işletme sahiplerinin "sipariş nerede?", "stok durumu ne?" gibi sorularla vakit kaybetmesini engeller.

##🎯 Temel Problemler ve Çözümler
Günümüzde KOBİ'ler, verilerini manuel Excel dosyalarında tutmakta ve operasyonel süreçleri yönetirken günde 3 saatini kaybetmektedir. KOPİ bu boşluğu şu şekilde doldurur:
Operasyonel Kaosun Sonu: Müşterileriniz "Siparişim nerede?" diye sorduğunda sistem otomatik yanıt verir; siz telefona bakmak zorunda kalmazsınız.
Gerçek Zamanlı Veri Analitiği: Kağıt üzerindeki verilerden kurtulun. Sipariş geldikçe stok düşer, gelir güncellenir ve dashboard anlık olarak yenilenir.
Akıllı Stok Takibi: Stoklar kritik seviyenin altına düştüğünde, sistem tedarikçiye AI tarafından yazılan WhatsApp mesajını otomatik olarak iletir.

##🚀 Temel Özellikler
AI Destekli Ürün Yönetimi: Ürün eklerken veya güncellerken otomatik açıklama oluşturma.
Akıllı Bildirimler: Kritik stok uyarıları ve otomatik tedarikçi mesajlaşma sistemi.
Dashboard & Performans Analizi: Günlük özetler, geçen ay ile büyüme karşılaştırması ve işletme sağlığı analizi.
WhatsApp Entegrasyonu: Müşteri sipariş sorgulama ve tedarikçi stok bildirimleri.
Kullanıcı Yönetimi: JWT tabanlı güvenli kimlik doğrulama.

##🛠️ Kullanılan Teknolojiler
KOPİ, modern bir yazılım mimarisi üzerine inşa edilmiştir:
Backend: FastAPI (6 modüler router: /auth, /orders, /products, /customers, /suppliers, /tasks).
Frontend: Jinja2 Template Engine (Server-side rendering).
Yapay Zeka: LangChain + Groq (Llama 3.3-70B) ile dashboard analizi, ürün açıklaması ve WhatsApp botu.
Veri: SQLAlchemy ORM.
Güvenlik: JWT + bcrypt şifreleme.
Dış Servisler: Meta WhatsApp Cloud API.

##👥 Hedef Kitle
KOPİ; butik işletmelerden tarım kooperatiflerine, el sanatları üreticilerinden küçük e-ticaret satıcılarına kadar dijitalleşmeye ihtiyaç duyan tüm KOBİ'ler için tasarlanmıştır.

##👨‍💻 Geliştirici Ekip
Bu proje Sudenaz Kalaycık, Nehir Doğan ve Zuhal Tuana Yıldırım tarafından geliştirilmiştir.
