import cv2
import numpy as np

# Dışbükey ayna parametreleri
distortion_strength = 0.5 # Dışbükey etki gücü (0.3-0.5 arası iyi çalışır)

# Kamera aç
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera açılamadı!")
    exit()

# Global değişkenler
mouse_pressed = False
press_x, press_y = 0, 0
concave_radius = 50  # Efekt yarıçapı
magnification = 1.2  # Büyütme faktörü artırıldı

# Mouse callback fonksiyonu
def mouse_callback(event, x, y, flags, param):
    global mouse_pressed, press_x, press_y
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_pressed = True
        press_x, press_y = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        mouse_pressed = False

# Pencere oluştur ve mouse callback'i ekle
window_name = "Disbukey Trafik Aynasi"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, mouse_callback)

# Ekran boyutlarını al
ret, frame = cap.read()
if not ret:
    print("Kamera görüntüsü alınamadı!")
    exit()
    
h, w = frame.shape[:2]

# Koordinat gridlerini önceden hesapla (performans için)
x = np.arange(w, dtype=np.float32)
y = np.arange(h, dtype=np.float32)
xx, yy = np.meshgrid(x, y)

# Maskeleri oluştur
circle_radius = min(w, h) // 2 - 30
center_x, center_y = w // 2, h // 2

# Ayna renkleri
orange = (0, 128, 255)  # BGR formatta turuncu
black = (0, 0, 0)       # BGR formatta siyah

while True:
    ret, frame = cap.read()
    if not ret: 
        print("Kamera görüntüsü alınamadı!")
        break
    
    # Görüntüyü yatay olarak çevir (ayna etkisi)
    frame = cv2.flip(frame, 1)
    
    # Görüntüyü boş bir siyah arka plana kopyala
    result = np.zeros_like(frame)
    
    # Mouse basılıysa büyüteç efekti ekle
    if mouse_pressed:
        # Tıklanan noktaya olan uzaklık
        click_dx = xx - press_x
        click_dy = yy - press_y
        click_distance = np.sqrt(click_dx**2 + click_dy**2)
        
        # Büyüteç efekt maskesi - Gaussian fonksiyonu
        magnify_mask = np.exp(-(click_distance**2) / (2 * concave_radius**2))
        
        # Koordinatları tıklanan noktaya göre ayarla
        dx = (xx - press_x)
        dy = (yy - press_y)
        
        # Büyütme efekti uygula
        dx_magnified = dx * magnify_mask * magnification
        dy_magnified = dy * magnify_mask * magnification
        
        # Yeni koordinatları hesapla
        map_x = (xx - dx_magnified).astype(np.float32)
        map_y = (yy - dy_magnified).astype(np.float32)
    else:
        # Normal dışbükey efekt için koordinatları hesapla
        dx = xx - center_x
        dy = yy - center_y
        
        # Merkeze olan uzaklığı hesapla
        distance = np.sqrt(dx*dx + dy*dy)
        max_dist = np.sqrt((w//2)**2 + (h//2)**2)
        
        # Normalize edilmiş mesafe
        normalized_dist = distance / max_dist
        
        # Dışbükey distorsiyon faktörü
        factor = 1 + (np.arctan(normalized_dist * distortion_strength) / (np.pi/2))
        
        # Yeni koordinatları hesapla
        map_x = (center_x + dx/factor).astype(np.float32)
        map_y = (center_y + dy/factor).astype(np.float32)
    
    # Distorsiyon uygula
    distorted = cv2.remap(frame, map_x, map_y, 
                         interpolation=cv2.INTER_CUBIC,
                         borderMode=cv2.BORDER_REPLICATE)
    
    # Ayna efektini sadece daire içine uygula
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (center_x, center_y), circle_radius, 255, -1)
    
    # Maske kenarlarını yumuşatma
    mask = cv2.GaussianBlur(mask, (9, 9), 0)
    
    # Daire dışı siyah, içi ayna efekti
    mask_3ch = cv2.merge([mask, mask, mask]) / 255.0
    result = distorted * mask_3ch
    
    # Ayna çerçevesi
    # Dış turuncu halka
    cv2.circle(result, (center_x, center_y), circle_radius + 10, orange, 10)
    # Orta siyah halka
    cv2.circle(result, (center_x, center_y), circle_radius + 5, black, 5)
    # İç turuncu halka
    cv2.circle(result, (center_x, center_y), circle_radius, orange, 2)
    
    # Ayna yüzeyinde hafif parlaklık efekti
    shine = np.zeros_like(mask)
    cv2.ellipse(shine, (center_x - circle_radius//4, center_y - circle_radius//4), 
                (circle_radius//3, circle_radius//2), 30, 0, 360, 255, -1)
    shine = cv2.GaussianBlur(shine, (51, 51), 0)
    
    # Parlamayı ekle
    shine_3ch = cv2.merge([shine, shine, shine]) / 255.0
    white = np.ones_like(result) * 255
    result = (1.0 - 0.15 * shine_3ch) * result + 0.15 * shine_3ch * white
    result = result.astype(np.uint8)
    
    # Sonucu göster
    cv2.imshow(window_name, result)
    
    # ESC ile çık
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
