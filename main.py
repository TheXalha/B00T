import os
import threading
import warnings
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.widgets import TextArea, Label
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.buffer import Document
import time

import browser
import scan

warnings.filterwarnings("ignore")
os.system('clear')

running_flag = {"running": False}
scan_thread = None
test_mode = {"active": False}
test_thread = None
login_done = {"value": False}
waiting_for_test_end = {"value": False}
browser_started = {"value": False}  # Browser'ın başlatılıp başlatılmadığını takip eder

output_field = TextArea(
    style="class:output-field",
    scrollbar=True,
    wrap_lines=True,
    read_only=False,
    focusable=False,
)

input_field = TextArea(
    height=1,
    prompt='Komut (1=Başlat, 2=Durdur, 3=Test, q=Çık): ',
    style='class:input-field',
    multiline=False,
)

def output_func(text):
    output_field.buffer.insert_text(text + "\n")

def start_scan_thread():
    global scan_thread
    scan_thread = threading.Thread(target=scan.scan_loop, args=(output_func, running_flag, browser.browser_handle_pair, login_done), daemon=True)
    scan_thread.start()
    output_func("Tarama başlatıldı.")

def start_bot():
    global scan_thread, test_mode, login_done, browser_started
    if running_flag["running"]:
        output_func("Bot zaten çalışıyor.")
        return

    if test_mode["active"]:
        output_func("Test modu aktif, bot başlatılamaz.")
        return

    running_flag["running"] = True
    test_mode["active"] = False
    waiting_for_test_end["value"] = False

    # Eğer browser zaten başlatılmışsa, sadece giriş kontrolü yap
    if browser_started["value"]:
        if login_done["value"]:
            output_func("Mevcut browser kullanılıyor, tarama başlıyor.")
            start_scan_thread()
        else:
            output_func("Browser zaten açık. Lütfen giriş yapıp ardından Enter'a basın.")
    else:
        login_done["value"] = False
        browser.start_browser()
        browser_started["value"] = True
        output_func("Browser başlatıldı. Lütfen giriş yapıp ardından Enter'a basın.")

def stop_bot():
    global scan_thread, test_mode, test_thread, login_done, waiting_for_test_end, browser_started
    if not running_flag["running"] and not test_mode["active"]:
        output_func("Bot zaten duruyor.")
        return

    running_flag["running"] = False
    test_mode["active"] = False
    login_done["value"] = False
    waiting_for_test_end["value"] = False
    browser_started["value"] = False

    if scan_thread:
        scan_thread.join()

    if test_thread:
        test_thread.join()

    browser.stop_browser()
    output_func("Bot ve browser durduruldu.")

def on_enter_after_login():
    global browser_started
    if not login_done["value"] and browser_started["value"]:
        login_done["value"] = True
        output_func("Giriş onaylandı.")
        
        if running_flag["running"]:
            output_func("Tarama başlıyor.")
            start_scan_thread()
        elif test_mode["active"]:
            output_func("Test devam ediyor.")
            
    elif waiting_for_test_end["value"]:
        waiting_for_test_end["value"] = False
        test_mode["active"] = False
        output_func("Test tamamlandı. Browser açık kalmaya devam ediyor.")

def test_process():
    global browser_started, login_done
    
    test_mode["active"] = True
    running_flag["running"] = False
    waiting_for_test_end["value"] = True

    # Eğer browser zaten başlatılmışsa yeniden başlatma
    if not browser_started["value"]:
        browser.start_browser()
        browser_started["value"] = True
        login_done["value"] = False
        output_func("Browser başlatıldı. Lütfen giriş yapıp ardından Enter'a basın.")
        
        # Giriş yapılmasını bekle
        while not login_done["value"] and test_mode["active"]:
            time.sleep(0.5)
    else:
        if not login_done["value"]:
            output_func("Browser zaten açık. Lütfen giriş yapıp ardından Enter'a basın.")
            while not login_done["value"] and test_mode["active"]:
                time.sleep(0.5)
        else:
            output_func("Mevcut browser kullanılıyor.")

    if not test_mode["active"]:  # Test iptal edildiyse
        return

    pair = "ETH_USDT"
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as f:
        f.write(f"{now}: {pair} (test)\n")
    output_func(f"Test modu: Yeni token bulundu ve loglandı: {pair}")

    browser.browser_handle_pair(pair)
    output_func("Test tamamlandı. Testi bitirmek için Enter'a basın...")

    # Test bitişini bekle
    while waiting_for_test_end["value"] and test_mode["active"]:
        time.sleep(0.5)

kb = KeyBindings()

@kb.add('enter')
def _(event):
    global scan_thread, test_thread
    cmd = input_field.text.strip()
    input_field.buffer.document = Document(text='')

    if cmd == '':
        # Enter tek başına basıldı, login onayı veya test sonu için
        on_enter_after_login()
        return

    if cmd == '1':
        start_bot()
    elif cmd == '2':
        stop_bot()
    elif cmd == '3':
        if running_flag["running"]:
            output_func("Bot çalışırken test başlatılamaz.")
            return
        # Test modu aktifse yeni test başlatma kontrolünü kaldır
        test_thread = threading.Thread(target=test_process, daemon=True)
        test_thread.start()
    elif cmd == 'q':
        stop_bot()
        event.app.exit()
    else:
        output_func(f"Bilinmeyen komut: {cmd}")

root_container = VSplit([
    HSplit([
        Label(text="Komut Girişi", style="class:title"),
        input_field,
    ], width=40, style="class:input-panel"),
    HSplit([
        Label(text="Çıktı", style="class:title"),
        output_field,
    ], style="class:output-panel"),
])

layout = Layout(root_container)

style = Style.from_dict({
    "input-panel": "bg:#444444 #ffffff",
    "output-panel": "bg:#222222 #00ff00",
    "title": "bold underline",
    "input-field": "bg:#555555 #ffffff",
    "output-field": "bg:#222222 #00ff00",
})

app = Application(layout=layout, key_bindings=kb, style=style, full_screen=True)

if __name__ == '__main__':
    app.run()