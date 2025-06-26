import requests
import time
import json
import os
from datetime import datetime
from dotenv import load_dotenv

TOKENS_FILE = "known_tokens.json"

def load_known_tokens():
    """Kayıtlı tokenları dosyadan yükler"""
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('tokens', []))
        except Exception as e:
            print(f"Token dosyası okuma hatası: {e}")
    return set()

def save_known_tokens(tokens):
    """Tokenları dosyaya kaydeder"""
    try:
        data = {
            'tokens': list(tokens),
            'last_updated': datetime.now().isoformat(),
            'total_count': len(tokens)
        }
        with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Token dosyası kaydetme hatası: {e}")

def get_futures_symbols():
    """MEXC API'dan futures sembollerini alır"""
    url = "https://contract.mexc.com/api/v1/contract/detail"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return [item["symbol"] for item in data["data"]]
    except Exception as e:
        print(f"API isteği hatası: {e}")
    return []

def initialize_known_tokens(output_func):
    """İlk çalıştırmada mevcut tüm tokenları kaydet"""
    output_func("İlk çalıştırma tespit edildi. Mevcut tokenlar kaydediliyor...")
    
    symbols = get_futures_symbols()
    if symbols:
        known_tokens = set(symbols)
        save_known_tokens(known_tokens)
        output_func(f"✓ {len(known_tokens)} adet mevcut token kaydedildi.")
        output_func("Bu tokenlar 'yeni' olarak işlenmeyecek.")
        return known_tokens
    else:
        output_func("⚠ API'dan token listesi alınamadı. Boş liste ile başlatılıyor.")
        return set()

def scan_loop(output_func, running_flag, selenium_func, login_done):
    """Ana tarama döngüsü"""
    
    # Çevre değişkenlerini yükle
    load_dotenv()
    
    # Tarama aralığını al (varsayılan: 10 saniye)
    try:
        scan_interval = int(os.getenv("SCAN_INTERVAL", "10"))
        if scan_interval < 1:
            scan_interval = 10
            output_func("⚠ SCAN_INTERVAL 1'den küçük olamaz. Varsayılan 10 saniye kullanılıyor.")
    except ValueError:
        scan_interval = 10
        output_func("⚠ SCAN_INTERVAL geçersiz değer. Varsayılan 10 saniye kullanılıyor.")
    
    output_func(f"📊 Tarama aralığı: {scan_interval} saniye")
    
    # Bilinen tokenları yükle
    known_tokens = load_known_tokens()
    
    # İlk çalıştırma kontrolü
    if not known_tokens:
        known_tokens = initialize_known_tokens(output_func)
        if not running_flag["running"]:  # Durdurulduysa çık
            return
    else:
        output_func(f"Kayıtlı {len(known_tokens)} token yüklendi. Yeni tokenlar aranıyor...")
    
    # Giriş yapılmasını bekle
    output_func("Tarama başlıyor. Giriş yapılmasını bekleniyor...")
    while running_flag["running"] and not login_done["value"]:
        time.sleep(1)
    
    if not running_flag["running"]:
        return
        
    output_func("✓ Giriş onaylandı. Aktif tarama başlatıldı.")
    
    # Ana tarama döngüsü
    scan_count = 0
    while running_flag["running"]:
        scan_count += 1
        output_func(f"[Tarama #{scan_count}] API sorgulanıyor...")
        
        current_symbols = get_futures_symbols()
        
        if not current_symbols:
            output_func("⚠ API'dan veri alınamadı. 30 saniye beklenecek.")
            time.sleep(30)
            continue
            
        current_tokens = set(current_symbols)
        new_tokens = current_tokens - known_tokens
        
        if new_tokens:
            output_func(f"🚀 {len(new_tokens)} yeni token bulundu!")
            
            for token in new_tokens:
                # Önce kayıtlara ekle
                known_tokens.add(token)
                save_known_tokens(known_tokens)
                
                # Log dosyasına yaz
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("log.txt", "a", encoding='utf-8') as f:
                    f.write(f"{now}: {token} (YENİ TOKEN)\n")
                
                output_func(f"📝 YENİ TOKEN: {token}")
                output_func(f"📊 Toplam kayıtlı token: {len(known_tokens)}")
                
                # Browser işlemini başlat
                try:
                    output_func(f"🔄 {token} için trading işlemi başlatılıyor...")
                    selenium_func(token)
                    output_func(f"✅ {token} işlem tamamlandı.")
                except Exception as e:
                    output_func(f"❌ {token} işlem hatası: {e}")
                
                # Tokenler arası kısa bekleme
                time.sleep(2)
                
        else:
            output_func(f"📊 Yeni token yok. Toplam: {len(current_tokens)} token kontrol edildi.")
        
        # Kayıp token kontrolü (isteğe bağlı)
        removed_tokens = known_tokens - current_tokens
        if removed_tokens:
            output_func(f"⚠ {len(removed_tokens)} token listeden çıkarıldı: {list(removed_tokens)[:3]}...")
        
        # Bir sonraki tarama için bekle
        if running_flag["running"]:
            output_func(f"⏱ {scan_interval} saniye bekleniyor...")
            for i in range(scan_interval):
                if not running_flag["running"]:
                    break
                time.sleep(1)
    
    output_func("🛑 Tarama durduruldu.")