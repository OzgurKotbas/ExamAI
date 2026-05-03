# Supabase Transaction Pooler (PgBouncer) Uyumluluk Düzeltmesi

**Tarih:** 30.04.2026  
**Etkilenen Dosya:** `backendWindsurf2/database.py`  
**Commit:** `574630f`  
**Durum:** ✅ GitHub'a push edildi

---

## Sorun

Render.com üzerinde yapılan her deployment denemesinde şu hata alınıyordu:

```
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
```

Bu hata mesajı son derece yanıltıcıydı. Şifre veya kullanıcı adı yanlış değildi.

---

## Gerçek Neden

Supabase'in **Transaction Pooler** bağlantısı (Port `6543`), arka planda **PgBouncer** adlı bir bağlantı havuzu yöneticisi kullanır.

PgBouncer'ın kritik bir kısıtlaması vardır:
> **PostgreSQL'in "Prepared Statement" özelliğini desteklemez.**

Bizim `asyncpg` kütüphanemiz ise bu özelliği **varsayılan olarak açık** kullanır (`statement_cache_size` varsayılan değeri `100`'dür).

Bu çakışma şöyle bir zincir oluşturuyordu:
1. Uygulama başladı, veritabanına bağlanmaya çalıştı.
2. asyncpg, PgBouncer'a hazırlanmış (prepared) bir sorgu gönderdi.
3. PgBouncer bunu reddetti.
4. asyncpg bu reddi "şifre hatası" olarak yorumlayıp yukarı fırlattı.

### Neden Doğrudan Bağlantıda (Port 5432) da Hata Aldık?
İlk denemelerde Port 5432 (Direct Connection) kullanılmıştı. Bu bağlantı tipi IPv6 üzerinden çalışır. Render'ın ücretsiz sunucuları IPv6 desteği olmadığından `[Errno 101] Network is unreachable` hatası alınmıştı.

---

## Uygulanan Çözüm

`backendWindsurf2/database.py` dosyasındaki **iki** SQLAlchemy engine yapılandırmasına `connect_args={"statement_cache_size": 0}` parametresi eklendi.

Bu parametre, asyncpg'ye "prepared statement önbelleğini devre dışı bırak" talimatı verir ve böylece PgBouncer ile tam uyumluluk sağlanır.

### Değişiklik (Diff)

```python
# ÖNCE
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

# SONRA
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    # Required for Supabase Transaction Pooler (PgBouncer) compatibility.
    # PgBouncer does not support prepared statements; setting cache size to 0 disables them.
    connect_args={"statement_cache_size": 0},
)
```

Aynı değişiklik `get_task_engine()` fonksiyonuna da uygulandı.

---

## Doğru DATABASE_URL Formatı

Render'daki `DATABASE_URL` ortam değişkeni şu formatta olmalıdır:

```
postgresql+asyncpg://postgres.[PROJE_KODU]:[SIFRE]@aws-1-eu-central-1.pooler.supabase.com:6543/postgres
```

| Parça | Açıklama |
|---|---|
| `postgresql+asyncpg://` | asyncpg sürücüsünü belirtir |
| `postgres.[PROJE_KODU]` | Supabase proje referansı (noktadan sonraki kısım kritik!) |
| `:[SIFRE]@` | Supabase veritabanı şifresi |
| `aws-1-eu-central-1.pooler.supabase.com` | Transaction Pooler host adresi |
| `:6543` | Transaction Pooler portu (Direct Connection 5432'dir, bu kullanılmaz!) |
| `/postgres` | Veritabanı adı |

> [!WARNING]
> URL'nin sonuna `?pgbouncer=true` gibi ek parametreler eklemeyin. asyncpg bu parametreyi desteklemez ve bağlantıyı bozabilir.

---

## Hata Teşhis Özeti

| Hata Mesajı | Gerçek Neden |
|---|---|
| `[Errno 111] Connection refused` | Yanlış port veya IPv6/IPv4 uyumsuzluğu |
| `[Errno 101] Network is unreachable` | Render sunucusu IPv6 desteklemiyor, Direct Connection kullanıldı |
| `tenant/user not found` | DATABASE_URL içindeki proje kodu eksik/hatalı |
| `password authentication failed` | PgBouncer, prepared statement'ları reddetti (gerçek neden şifre değil!) |

---

*Rapor Hazırlayan: Antigravity AI*
