"""
limiter.py – Merkezi Rate Limiter modülü.

Bu dosya, main.py ve router'lar arasındaki döngüsel import (circular import)
sorununu çözmek için oluşturulmuştur. slowapi Limiter nesnesi burada tek bir
noktada tanımlanır; hem main.py hem de tüm router'lar bu dosyadan import eder.

Kullanım:
    from limiter import limiter
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Client IP'ye göre istek sınırlaması yapar.
# In-memory sayaçlar kullanılır (yeterli); Redis tabanlı kalıcı sayaçlara
# geçmek için key_func yerine storage_uri parametresi eklenebilir.
limiter = Limiter(key_func=get_remote_address)
