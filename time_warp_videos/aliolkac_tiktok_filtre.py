import cv2
import numpy as np
import time
import os

def apply_filter(frame, filter_type):
    """Görüntüye farklı efektler uygular
    
    Parametreler:
    frame -- İşlenecek görüntü
    filter_type -- Uygulanacak filtre tipi (0-5 arası değer)
    
    Dönüş:
    Filtre uygulanmış görüntü
    """
    # Boş veya çok küçük frame kontrolü - hataları önlemek için
    if frame is None or frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
        return frame
        
    if filter_type == 0:  # Normal - filtre yok, görüntüyü olduğu gibi döndür
        return frame
    elif filter_type == 1:  # Siyah-beyaz filtresi
        # Görüntüyü önce gri tonlamaya çevir, sonra tekrar BGR formatına dönüştür
        return cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    elif filter_type == 2:  # Negatif filtresi - renkleri ters çevir
        return 255 - frame  # Her piksel değerinden 255 çıkararak negatif elde edilir
    elif filter_type == 3:  # Sepya filtresi - eski fotoğraf görünümü
        # Renk dönüşüm matrisi - sepya tonu için renk değerlerini ayarlar
        sepya = np.array([[0.272, 0.534, 0.131],
                          [0.349, 0.686, 0.168],
                          [0.393, 0.769, 0.189]])
        # Matris çarpımı ile sepya efekti uygulama
        return cv2.transform(frame, sepya)
    elif filter_type == 4:  # Kenar algılama filtresi
        # Canny kenar algılama algoritması
        edges = cv2.Canny(frame, 100, 200)  # Eşik değerleri 100 ve 200
        # Gri tonlamalı kenar görüntüsünü BGR'ye dönüştür
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    elif filter_type == 5:  # Mozaik filtresi - pikselleştirme efekti
        h, w = frame.shape[:2]  # Görüntünün yüksekliği ve genişliği
        # Çok küçük görüntüleri kontrol et - sıfır bölme hatalarını önlemek için
        new_w = max(1, w//10)  # En az 1 piksel genişliğinde olmalı
        new_h = max(1, h//10)  # En az 1 piksel yüksekliğinde olmalı
        
        if new_w < w and new_h < h:  # Boyutlar küçülmelidir
            # Görüntüyü küçültüp sonra tekrar büyüterek pikselleştirme efekti oluşturma
            temp = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            # INTER_NEAREST ile büyültme - piksel tekrarı ile mozaik efekti oluşur
            return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
        else:
            return frame  # Boyut küçültemiyorsak olduğu gibi bırak
    # Diğer tüm durumlar için orijinal görüntüyü döndür
    return frame

def time_warp_scan():
    """Ana Time Warp Scan fonksiyonu - kamera görüntüsünü tarayarak efekt oluşturur"""
    # Kullanıcıdan tarama yönünü seçmesini iste
    print("Tarama yönünü seçin:")
    print("1: Yukarıdan Aşağıya")
    print("2: Soldan Sağa")
    print("3: Çift Yönlü (Yukarıdan Aşağıya ve Soldan Sağa)")
    direction = input("Seçiminiz (1, 2 veya 3): ")  # Kullanıcıdan giriş al
    
    # Mevcut filtreleri göster ve kullanıcıdan seçim iste
    print("\nKullanılabilir filtreler:")
    print("0: Normal (filtre yok)")
    print("1: Siyah-Beyaz")
    print("2: Negatif")
    print("3: Sepya")
    print("4: Kenar Algılama")
    print("5: Mozaik")
    filter_type = int(input("Filtre seçin (0-5): "))  # Filtre seçimini tam sayıya dönüştür
    
    # Kamerayı başlat - 0 parametresi varsayılan kamerayı seçer
    cap = cv2.VideoCapture(0)
    
    # Kamera açılamazsa hata mesajı ver ve fonksiyondan çık
    if not cap.isOpened():
        print("Kamera açılamadı!")
        return
    
    # İlk kareyi al ve boyutlarını öğren
    ret, frame = cap.read()  # ret: okuma başarılı mı, frame: kamera görüntüsü
    if not ret:
        print("Kare yakalanamadı!")
        return
    
    # Sonuç görüntüsünü oluştur (başlangıçta tamamen siyah)
    height, width, _ = frame.shape  # Görüntünün boyutlarını al
    result = np.zeros_like(frame)  # frame ile aynı boyutta sıfırlardan oluşan dizi
    
    # Tarama çizgisinin başlangıç pozisyonları
    scan_line_pos_v = 0  # Dikey tarama için (yukarıdan aşağıya)
    scan_line_pos_h = 0  # Yatay tarama için (soldan sağa)
    
    # Tarama hızı (piksel/kare) - her karede tarama çizgisi kaç piksel ilerleyecek
    scan_speed = 2
    
    # Video kayıt değişkenleri
    video_frames = []  # Kaydedilecek kareleri tutacak liste
    is_recording = True  # Kayıt durumu - başlangıçta kayıt yapılıyor
    
    # Tarama duraklatma değişkeni
    is_paused = False  # Başlangıçta duraklama yok
    
    # Videolar için klasör oluştur (eğer yoksa)
    if not os.path.exists('time_warp_videos'):
        os.makedirs('time_warp_videos')  # Klasör oluştur
    
    # Tarama tamamlandı mı? Başlangıçta hayır.
    scan_completed_v = False  # Dikey tarama tamamlandı mı?
    scan_completed_h = False  # Yatay tarama tamamlandı mı?
    
    # Aktif filtre - başlangıçta kullanıcının seçtiği filtre
    current_filter = filter_type
    
    # Kılavuz metni - ekranın altında gösterilecek tuş bilgileri
    help_text = "ESC: Çıkış | SPACE: Duraklat/Devam | R: Sıfırla | S: Kaydet | F: Filtre Değiştir"
    
    # Ana döngü - her iterasyon bir kare işler
    while True:
        # Kameradan yeni bir kare al
        ret, frame = cap.read()
        if not ret:  # Kare alınamadıysa döngüden çık
            break
        
        # Ayna görüntüsü (selfie modu gibi) - yatay eksende çevirme
        frame = cv2.flip(frame, 1)  # 1: yatay eksende çevirme
        
        # Mevcut sonuç görüntüsünün bir kopyasını oluştur (üzerinde değişiklik yapılacak)
        current_result = result.copy()
        
        # Tarama yönüne göre işlemleri yap
        # Çift yönlü tarama - hem yatay hem dikey
        if direction == '3':
            try:
                # Önce yatay (soldan sağa) taramayı işle
                if scan_line_pos_h < width and not is_paused:
                    # Yatay tarama - geçtiği kısım filtrelenir
                    if not scan_completed_h:
                        # Tarama çizgisinin geçtiği kısımın boş olmadığından emin ol
                        if scan_line_pos_h < width - scan_speed:
                            # Mevcut sütunlara filtre uygula
                            filtered_slice = apply_filter(frame[:, scan_line_pos_h:scan_line_pos_h+scan_speed], current_filter)
                            # Filtrelenmiş sonucu sonuç görüntüsüne ekle
                            result[:, scan_line_pos_h:scan_line_pos_h+scan_speed] = filtered_slice
                        # Tarama çizgisinin pozisyonunu güncelle
                        scan_line_pos_h += scan_speed
                        # Eğer yatay tarama tamamlandıysa bunu işaretle
                        if scan_line_pos_h >= width:
                            scan_completed_h = True
                            print("Yatay tarama tamamlandı!")
                
                # Sonra dikey (yukarıdan aşağıya) taramayı işle
                if scan_line_pos_v < height and not is_paused:
                    # Dikey tarama - geçtiği kısım filtrelenir
                    if not scan_completed_v:
                        # Tarama çizgisinin geçtiği kısımın boş olmadığından emin ol
                        if scan_line_pos_v < height - scan_speed:
                            # Mevcut satırlara filtre uygula
                            filtered_slice = apply_filter(frame[scan_line_pos_v:scan_line_pos_v+scan_speed, :], current_filter)
                            # Filtrelenmiş sonucu sonuç görüntüsüne ekle
                            result[scan_line_pos_v:scan_line_pos_v+scan_speed, :] = filtered_slice
                        # Tarama çizgisinin pozisyonunu güncelle
                        scan_line_pos_v += scan_speed
                        # Eğer dikey tarama tamamlandıysa bunu işaretle
                        if scan_line_pos_v >= height:
                            scan_completed_v = True
                            print("Dikey tarama tamamlandı!")
                
                # Henüz taranmamış kısımları canlı kameradan al
                if scan_line_pos_h < width:
                    # Yatay çizginin sağındaki kısmı canlı kameradan al
                    current_result[:, scan_line_pos_h:] = frame[:, scan_line_pos_h:]
                if scan_line_pos_v < height:
                    # Dikey çizginin altındaki ve yatay çizginin solundaki kısmı güncelle
                    current_result[scan_line_pos_v:, :scan_line_pos_h] = frame[scan_line_pos_v:, :scan_line_pos_h]
                
                # Tarama çizgilerini çiz
                if scan_line_pos_h < width:
                    # Yatay tarama için mavi dikey çizgi çiz
                    cv2.line(current_result, (scan_line_pos_h, 0), (scan_line_pos_h, height), (255, 0, 0), 2)
                if scan_line_pos_v < height:
                    # Dikey tarama için yeşil yatay çizgi çiz
                    cv2.line(current_result, (0, scan_line_pos_v), (width, scan_line_pos_v), (0, 255, 0), 2)
            except Exception as e:
                # Hata yakalama - hata durumunda çökmeyi önle
                print(f"Çift yönlü tarama hatası: {e}")
                
        elif direction == '1':  # Yukarıdan Aşağıya tarama
            try:
                if scan_line_pos_v < height and not is_paused:
                    # Tarama çizgisinden sonraki kısmı canlı kameradan al
                    current_result[scan_line_pos_v:, :] = frame[scan_line_pos_v:, :]
                    
                    # Tarama çizgisinin geçtiği kısmı filtreleyerek sonuç görüntüsüne kaydet
                    # Taşma olmamasını sağla
                    if scan_line_pos_v < height - scan_speed:
                        # Mevcut satırlara filtre uygula
                        filtered_slice = apply_filter(frame[scan_line_pos_v:scan_line_pos_v+scan_speed, :], current_filter)
                        # Filtrelenmiş sonucu sonuç görüntüsüne ekle
                        result[scan_line_pos_v:scan_line_pos_v+scan_speed, :] = filtered_slice
                    
                    # Tarama çizgisinin pozisyonunu güncelle
                    scan_line_pos_v += scan_speed
                    
                    # Tarama tamamlandı mı kontrol et
                    if scan_line_pos_v >= height and not scan_completed_v:
                        scan_completed_v = True
                        print("Tarama tamamlandı! Videoyu kaydetmek için 's' tuşuna basın.")
                else:
                    # Duraklatıldığında canlı kamera görüntüsünü tarama çizgisinin altında göster
                    current_result[scan_line_pos_v:, :] = frame[scan_line_pos_v:, :]
                
                # Tarama çizgisini çiz (mavi renkte)
                if scan_line_pos_v < height:
                    # Yatay mavi çizgi çiz
                    cv2.line(current_result, (0, scan_line_pos_v), (width, scan_line_pos_v), (255, 0, 0), 2)
            except Exception as e:
                # Hata yakalama
                print(f"Dikey tarama hatası: {e}")
                
        elif direction == '2':  # Soldan Sağa tarama
            try:
                if scan_line_pos_h < width and not is_paused:
                    # Tarama çizgisinden sonraki kısmı canlı kameradan al
                    current_result[:, scan_line_pos_h:] = frame[:, scan_line_pos_h:]
                    
                    # Tarama çizgisinin geçtiği kısmı filtreleyerek sonuç görüntüsüne kaydet
                    # Taşma olmamasını sağla
                    if scan_line_pos_h < width - scan_speed:
                        # Mevcut sütunlara filtre uygula
                        filtered_slice = apply_filter(frame[:, scan_line_pos_h:scan_line_pos_h+scan_speed], current_filter)
                        # Filtrelenmiş sonucu sonuç görüntüsüne ekle
                        result[:, scan_line_pos_h:scan_line_pos_h+scan_speed] = filtered_slice
                    
                    # Tarama çizgisinin pozisyonunu güncelle
                    scan_line_pos_h += scan_speed
                    
                    # Tarama tamamlandı mı kontrol et
                    if scan_line_pos_h >= width and not scan_completed_h:
                        scan_completed_h = True
                        print("Tarama tamamlandı! Videoyu kaydetmek için 's' tuşuna basın.")
                else:
                    # Duraklatıldığında canlı kamera görüntüsünü tarama çizgisinin sağında göster
                    current_result[:, scan_line_pos_h:] = frame[:, scan_line_pos_h:]
                
                # Tarama çizgisini çiz (mavi renkte)
                if scan_line_pos_h < width:
                    # Dikey mavi çizgi çiz
                    cv2.line(current_result, (scan_line_pos_h, 0), (scan_line_pos_h, height), (255, 0, 0), 2)
            except Exception as e:
                # Hata yakalama
                print(f"Yatay tarama hatası: {e}")
        
        # Kayıt için kareyi listeye ekle
        if is_recording:
            # Her kareyi video için sakla
            video_frames.append(current_result.copy())
            
            # Kayıt bilgisini göster (kırmızı REC yazısı)
            cv2.putText(current_result, "REC", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Aktif filtre bilgisini göster
        filter_names = ["Normal", "Siyah-Beyaz", "Negatif", "Sepya", "Kenar Algılama", "Mozaik"]
        # Ekranın sağ üst köşesine filtre adını yaz
        cv2.putText(current_result, f"Filtre: {filter_names[current_filter]}", (width-250, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Duraklatma durumunda küçük bir gösterge
        if is_paused:
            # Ekranın ortasında duraklatma simgesi göster
            cv2.putText(current_result, "||", (width//2-10, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
                       
        # Kılavuz metnini göster (ekranın altında)
        cv2.putText(current_result, help_text, (20, height-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Sonuç görüntüsünü göster
        cv2.imshow('Time Warp Scan', current_result)
        
        # Tuş kontrolü - 1ms bekle ve basılan tuşun ASCII kodunu al
        key = cv2.waitKey(1)
        
        # ESC tuşuna basılırsa çık
        if key == 27:  # ESC tuşunun ASCII kodu
            break
            
        # 'r' tuşuna basılırsa efekti sıfırla
        elif key == ord('r'):
            # Kaydı sıfırla
            video_frames = []  # Video kare listesini temizle
            is_recording = True  # Kayıt durumunu aktif et
            is_paused = False  # Duraklatma durumunu kapat
            
            # Efekti sıfırla - her şeyi başlangıç durumuna getir
            result = np.zeros_like(frame)  # Sonuç görüntüsünü siyahla doldur
            scan_line_pos_v = 0  # Dikey tarama çizgisini başa al
            scan_line_pos_h = 0  # Yatay tarama çizgisini başa al
            scan_completed_v = False  # Dikey tarama tamamlanma durumunu sıfırla
            scan_completed_h = False  # Yatay tarama tamamlanma durumunu sıfırla
            
        # 's' tuşuna basılırsa videoyu kaydet
        elif key == ord('s') and (scan_completed_v or scan_completed_h):
            # Kaydetme fonksiyonunu çağır
            save_video(video_frames, width, height)
            video_frames = []  # Belleği temizle
            
        # Space tuşuna basılırsa taramayı durdur/devam ettir
        elif key == 32:  # Space tuşunun ASCII kodu
            is_paused = not is_paused  # Duraklatma durumunu tersine çevir
            if is_paused:
                print("Tarama duraklatıldı. Devam etmek için tekrar SPACE tuşuna basın.")
            else:
                print("Tarama devam ediyor.")
                
        # 'f' tuşuna basılırsa filtre değiştir
        elif key == ord('f'):
            current_filter = (current_filter + 1) % 6  # 6 farklı filtre (0-5)
            print(f"Filtre değiştirildi: {filter_names[current_filter]}")
            
    # Temizlik işlemleri
    cap.release()  # Kamera kaynağını serbest bırak
    cv2.destroyAllWindows()  # Tüm açık pencereleri kapat

def save_video(frames, width, height):
    """Video karelerini bir dosyaya kaydeder
    
    Parametreler:
    frames -- Kaydedilecek video kareleri listesi
    width -- Görüntü genişliği
    height -- Görüntü yüksekliği
    """
    # Kaydedilecek kare yoksa uyarı ver ve fonksiyondan çık
    if not frames:
        print("Kaydedilecek kare bulunamadı!")
        return
        
    # Dosya adı için zaman damgası oluştur
    timestamp = time.strftime("%Y%m%d-%H%M%S")  # Yıl-ay-gün-saat-dakika-saniye formatında
    video_path = f"time_warp_videos/time_warp_{timestamp}.avi"  # Dosya yolu
    
    # Video yazıcıyı oluştur
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Video codec - XVID
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))  # 20 FPS, belirtilen boyutta
    
    print(f"Video kaydediliyor: {video_path}")
    
    # Tüm kareleri videoya yaz
    for frame in frames:
        out.write(frame)  # Her kareyi dosyaya yaz
    
    # Video yazıcıyı kapat
    out.release()  # Dosyayı kapat
    print(f"Video başarıyla kaydedildi: {video_path}")

# Ana program başlangıcı
if __name__ == "__main__":
    time_warp_scan()  # Time Warp Scan fonksiyonunu çağır
