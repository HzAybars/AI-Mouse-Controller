# ==============================================================================
# PROJE: AI Mouse - Derinlik Algılı Sanal Fare
# YAZAR: Hz.Aybars
# TARİH: 2026
#
# AÇIKLAMA:
# Bu proje, bilgisayar kamerasını kullanarak el hareketleriyle mouse kontrolü sağlar.
# Standart projelerden farkı, elin kameraya olan uzaklığını (derinliği) hesaplayarak
# tıklama hassasiyetini dinamik olarak ayarlamasıdır.
#
# GEREKSİNİMLER:
# - opencv-python
# - mediapipe
# - numpy
# - pywin32
# ==============================================================================

import cv2
import mediapipe as mp
import numpy as np
import win32api, win32con
import time
import math
from threading import Thread

# ==========================================
#               AYARLAR (CONFIG)
# ==========================================
class Config:
    """
    Projenin tüm hassasiyet ve ekran ayarları burada tutulur.
    Değerleri değiştirerek mouse'un hızını ve tepki süresini ayarlayabilirsiniz.
    """
    CAM_WIDTH, CAM_HEIGHT = 640, 480    # Kamera çözünürlüğü
    
    # -- HAREKET ALANI AYARLARI --
    # Ekranın tamamını kullanmak yerine, kamerada belirli bir kare içinde
    # elinizi hareket ettirmeniz yeterlidir. Bu değerler o karenin kenar boşluklarıdır.
    FRAME_REDUCTION_X = 100  
    FRAME_REDUCTION_Y = 80   
    
    # -- HAREKET YUMUŞATMA --
    # Mouse titremesini önlemek için kullanılır. Değer artarsa mouse daha "ağır" ve pürüzsüz hareket eder.
    SMOOTHING = 7            
    JITTER_THRESHOLD = 3.5   # Çok küçük el titremelerini görmezden gelmek için eşik değeri.
    
    # -- DİNAMİK TIKLAMA AYARLARI (Hz.Aybars Özel Algoritması) --
    # Sabit piksel değeri yerine, elin büyüklüğüne göre oran kullanılır.
    # Örnek: Başparmak ve işaret parmağı arasındaki mesafe, elin %25'i kadarsa TIKLA.
    CLICK_RATIO = 0.25      # Tıklama tetikleme oranı
    FREEZE_RATIO = 0.40     # Mouse'u kilitleme oranı (Tıklama yaparken imleç kaymasın diye)
    GESTURE_THRESHOLD = 0.35 # Kayıtlı jestleri tanıma benzerlik oranı (Daha düşük = Daha katı)

    # Windows ekran boyutlarını otomatik çeker
    SCREEN_WIDTH = win32api.GetSystemMetrics(0)
    SCREEN_HEIGHT = win32api.GetSystemMetrics(1)

# ==========================================
#           1. KAMERA MODÜLÜ (THREAD)
# ==========================================
class CameraStream:
    """
    Kamera okuma işlemini ayrı bir işlemci ipliğinde (thread) çalıştırır.
    Bu sayede görüntü işlenirken kamera donmaz, FPS artışı sağlanır.
    """
    def __init__(self):
        self.stream = cv2.VideoCapture(0)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAM_WIDTH)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAM_HEIGHT)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Gecikmeyi önlemek için buffer 1
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        # Güncelleme fonksiyonunu arka planda başlatır
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped: return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # Ayna etkisi için görüntüyü ters çeviriyoruz (flip)
        return cv2.flip(self.frame, 1) if self.frame is not None else None

    def stop(self):
        self.stopped = True
        self.stream.release()

# ==========================================
#           2. MOUSE KONTROL MODÜLÜ
# ==========================================
class MouseController:
    """
    Windows API'lerini kullanarak imleci hareket ettirir ve tıklama yapar.
    Matematiksel interpolasyon ile kamera koordinatlarını ekran koordinatlarına çevirir.
    """
    def __init__(self):
        self.pLocX, self.pLocY = 0, 0 # Önceki lokasyon (Yumuşatma için)
        self.last_click_time = 0
        self.is_dragging = False

    def move(self, x, y):
        # 1. Adım: Koordinat Dönüşümü (Kamera -> Ekran)
        # np.interp fonksiyonu, kameradaki küçük kareyi tüm ekrana yayar (Map işlemi).
        targetX = np.interp(x, (Config.FRAME_REDUCTION_X, Config.CAM_WIDTH - Config.FRAME_REDUCTION_X), (0, Config.SCREEN_WIDTH))
        targetY = np.interp(y, (Config.FRAME_REDUCTION_Y, Config.CAM_HEIGHT - Config.FRAME_REDUCTION_Y), (0, Config.SCREEN_HEIGHT))
        
        # 2. Adım: Titreme Kontrolü
        dist_moved = math.hypot(targetX - self.pLocX, targetY - self.pLocY)
        if dist_moved < Config.JITTER_THRESHOLD: return # Çok az hareket varsa işlem yapma

        # 3. Adım: Yumuşatma (Smoothing)
        # Hedefe anında gitmek yerine, yavaş yavaş yaklaşarak daha doğal bir hareket sağlar.
        cLocX = self.pLocX + (targetX - self.pLocX) / Config.SMOOTHING
        cLocY = self.pLocY + (targetY - self.pLocY) / Config.SMOOTHING
        
        # Ekran dışına taşmayı engelle
        cLocX = np.clip(cLocX, 0, Config.SCREEN_WIDTH)
        cLocY = np.clip(cLocY, 0, Config.SCREEN_HEIGHT)
        
        # Windows imlecini taşı
        win32api.SetCursorPos((int(cLocX), int(cLocY)))
        self.pLocX, self.pLocY = cLocX, cLocY

    def click(self, button='left'):
        # Peş peşe hatalı tıklamaları önlemek için zaman kontrolü (0.3 saniye bekleme)
        if time.time() - self.last_click_time > 0.3:
            if button == 'left':
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            elif button == 'right':
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
            self.last_click_time = time.time()
            return True
        return False

    def drag_start(self):
        if not self.is_dragging:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            self.is_dragging = True

    def drag_end(self):
        if self.is_dragging:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            self.is_dragging = False

# ==========================================
#           3. JEST VE HAREKET MOTORU
# ==========================================
class GestureEngine:
    """
    El şekillerini kaydeder ve tanır.
    Kullanıcı 'K' veya 'T' tuşuna bastığında o anki el şeklini vektörel olarak kaydeder.
    """
    def __init__(self):
        self.saved_gestures = {} 

    def _normalize(self, landmarks):
        # Elin ekrandaki yerinden bağımsız olması için koordinatları normalize eder.
        # Böylece el ekranın neresinde olursa olsun şekli tanıyabiliriz.
        pts = np.array([[lm.x, lm.y] for lm in landmarks])
        pts = pts - pts[0] # Başlangıç noktasını bilek (0) yap
        max_dist = np.max(np.linalg.norm(pts, axis=1)) # Ölçekleme
        if max_dist > 0: pts = pts / max_dist
        return pts.flatten()

    def save(self, name, landmarks):
        data = self._normalize(landmarks)
        self.saved_gestures[name] = data
        print(f"Hz.Aybars Sistemi: {name} jesti başarıyla kaydedildi.")

    def detect(self, landmarks):
        if not self.saved_gestures: return None, 0.0
        current_data = self._normalize(landmarks)
        best_match, min_dist = None, 100.0
        
        # Kayıtlı tüm jestlerle şu anki eli karşılaştır
        for name, saved_data in self.saved_gestures.items():
            dist = np.linalg.norm(current_data - saved_data)
            if dist < min_dist:
                min_dist = dist
                best_match = name
        
        # Benzerlik eşiğin altındaysa (yani çok benziyorsa) eşleşmeyi döndür
        if min_dist < Config.GESTURE_THRESHOLD:
            return best_match, min_dist
        return None, min_dist

    def is_fist(self, lmList, scale_ref):
        """
        Dinamik Yumruk Tespiti:
        Parmak uçlarının bileğe olan uzaklığını, elin o anki boyutuyla (scale_ref) kıyaslar.
        """
        if len(lmList) < 21: return False
        fingers_closed = 0
        threshold = scale_ref * 0.9 # Eşik değeri elin boyutuna göre değişir

        # İşaret, Orta, Yüzük ve Serçe parmak uçlarını kontrol et
        for tip_id in [8, 12, 16, 20]:
            dist_to_wrist = math.hypot(lmList[tip_id][1] - lmList[0][1], lmList[tip_id][2] - lmList[0][2])
            if dist_to_wrist < threshold: 
                fingers_closed += 1
        return fingers_closed >= 4 # 4 parmak kapalıysa yumruktur

# ==========================================
#           4. ANA DÖNGÜ (MAIN)
# ==========================================
def main():
    try:
        # Modülleri Başlat
        cam = CameraStream().start()
        mouse = MouseController()
        gesture_engine = GestureEngine()
        
        # MediaPipe Kurulumu
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=0
        )
        mp_draw = mp.solutions.drawing_utils

        # Pencere Ayarları
        win_name = "AI Mouse - By Hz.Aybars"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 320, 240)
        cv2.setWindowProperty(win_name, cv2.WND_PROP_TOPMOST, 1) # Pencereyi hep üstte tut

        print("Hz.Aybars AI Mouse Başlatıldı. Çıkış için 'Q' basınız.")

        while True:
            img = cam.read()
            if img is None: continue
            
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(imgRGB)
            
            status_msg = "Mouse Aktif"
            color_ui = (0, 255, 0)
            
            if results.multi_hand_landmarks:
                for hand_lms in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
                    
                    # Landmark koordinatlarını listeye çevir
                    lmList = []
                    h, w, c = img.shape
                    for id, lm in enumerate(hand_lms.landmark):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        lmList.append([id, cx, cy])

                    if not lmList: continue

                    # --- DİNAMİK ÖLÇEK HESAPLAMA (KRİTİK BÖLÜM) ---
                    # Bilek (0) ile Orta Parmak Kökü (9) arası mesafe referans alınır.
                    # El kameraya yaklaşınca bu sayı büyür, uzaklaşınca küçülür.
                    scale_ref = math.hypot(lmList[9][1] - lmList[0][1], lmList[9][2] - lmList[0][2])
                    
                    # Tıklama mesafelerini elin o anki boyutuna göre ayarla
                    dynamic_click_dist = scale_ref * Config.CLICK_RATIO
                    dynamic_freeze_dist = scale_ref * Config.FREEZE_RATIO

                    # SENARYO 1: YUMRUK (Sürükle ve Bırak)
                    if gesture_engine.is_fist(lmList, scale_ref):
                        status_msg = "MOD: SURUKLEME"
                        color_ui = (0, 0, 255) # Kırmızı
                        mouse.drag_start()
                        mouse.move(lmList[5][1], lmList[5][2]) # İşaret parmağı kökü ile hareket
                    
                    else:
                        mouse.drag_end()
                        
                        # SENARYO 2: ÖZEL JESTLER (KAPAT/TAB)
                        detected_gesture, score = gesture_engine.detect(hand_lms.landmark)
                        if detected_gesture:
                            status_msg = f"JEST: {detected_gesture}"
                            color_ui = (255, 0, 0)
                            # Buraya win32api ile klavye kısayolları eklenebilir.
                        
                        # SENARYO 3: İMLEÇ KONTROLÜ
                        else:
                            # 8: İşaret Ucu, 4: Başparmak Ucu, 12: Orta Parmak Ucu
                            x1, y1 = lmList[8][1], lmList[8][2]
                            x2, y2 = lmList[4][1], lmList[4][2]
                            x3, y3 = lmList[12][1], lmList[12][2]
                            
                            dist_index = math.hypot(x2 - x1, y2 - y1)     # Sol tık mesafesi
                            dist_middle = math.hypot(x2 - x3, y2 - y3)    # Sağ tık mesafesi
                            
                            # Mouse KİLİTLEME (Tıklarken imleç titremesin)
                            is_clicking = (dist_index < dynamic_freeze_dist) or (dist_middle < dynamic_freeze_dist)
                            
                            if not is_clicking:
                                mouse.move(x1, y1)
                            else:
                                status_msg = "KILIT (Tiklama Hazir)"
                                color_ui = (255, 255, 0) # Sarı

                            # TIKLAMA EYLEMLERİ
                            if dist_index < dynamic_click_dist:
                                if mouse.click('left'): cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                            elif dist_middle < dynamic_click_dist:
                                if mouse.click('right'): cv2.circle(img, (x3, y3), 15, (0, 0, 255), cv2.FILLED)

                    # KLAVYE GİRİŞLERİ (JEST KAYDI İÇİN)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('k'): gesture_engine.save("KAPAT", hand_lms.landmark)
                    elif key == ord('t'): gesture_engine.save("TAB", hand_lms.landmark)

            else:
                mouse.drag_end()
                status_msg = "El Bekleniyor..."
                color_ui = (100, 100, 100)

            # Ekrana Çizimler
            cv2.rectangle(img, 
                        (Config.FRAME_REDUCTION_X, Config.FRAME_REDUCTION_Y), 
                        (Config.CAM_WIDTH - Config.FRAME_REDUCTION_X, Config.CAM_HEIGHT - Config.FRAME_REDUCTION_Y), 
                        (255, 0, 255), 2)
            
            cv2.putText(img, status_msg, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_ui, 2)
            cv2.imshow(win_name, img)

            if cv2.waitKey(1) & 0xFF == ord('q'): break

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        if 'cam' in locals(): cam.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()