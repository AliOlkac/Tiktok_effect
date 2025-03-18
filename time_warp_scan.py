import cv2
import numpy as np
import time
import os

def time_warp_scan():
    # Kullanıcıdan tarama yönünü seçmesini iste
    direction = input("Tarama yönünü seçin (1: Yukarıdan Aşağıya, 2: Soldan Sağa): ")
    
    # Kamerayı başlat
    cap = cv2.VideoCapture(0)
    
    # Kamera açılamazsa hata mesajı ver
    if not cap.isOpened():
        print("Kamera açılamadı!")
        return
    
    # İlk kareyi al ve boyutlarını öğren
    ret, frame = cap.read()
    if not ret:
        print("Kare yakalanamadı!")
        return
    
    # Sonuç görüntüsünü oluştur (başlangıçta boş)
    height, width, _ = frame.shape
    result = np.zeros_like(frame)
    
    # Tarama çizgisinin başlangıç pozisyonu
    scan_line_pos = 0
    
    # Tarama hızı (piksel/kare)
    scan_speed = 2
    
    # Video kayıt değişkenleri
    video_frames = []  # Tüm kareleri saklayacak liste
    is_recording = True  # Başlangıçtan itibaren kaydet
    
    # Tarama duraklatma değişkeni
    is_paused = False
    
    # Videolar için klasör oluştur
    if not os.path.exists('time_warp_videos'):
        os.makedirs('time_warp_videos')
    
    # Tarama tamamlandı mı?
    scan_completed = False
    
    while True:
        # Kameradan kare al
        ret, frame = cap.read()
        if not ret:
            break
        
        # Ayna görüntüsü (selfie modu gibi)
        frame = cv2.flip(frame, 1)
        
        # Tarama yönüne göre işlemleri yap
        current_result = result.copy()
        
        if direction == '1':  # Yukarıdan Aşağıya
            if scan_line_pos < height and not is_paused:
                current_result[scan_line_pos:, :] = frame[scan_line_pos:, :]
                result[scan_line_pos:scan_line_pos+scan_speed, :] = frame[scan_line_pos:scan_line_pos+scan_speed, :]
                scan_line_pos += scan_speed
            elif scan_line_pos >= height and not scan_completed:
                scan_completed = True
                print("Tarama tamamlandı! Videoyu kaydetmek için 's' tuşuna basın.")
            else:
                # Duraklatıldığında canlı kamera görüntüsünü tarama çizgisinin altında göster
                current_result[scan_line_pos:, :] = frame[scan_line_pos:, :]
        
        elif direction == '2':  # Soldan Sağa
            if scan_line_pos < width and not is_paused:
                current_result[:, scan_line_pos:] = frame[:, scan_line_pos:]
                result[:, scan_line_pos:scan_line_pos+scan_speed] = frame[:, scan_line_pos:scan_line_pos+scan_speed]
                scan_line_pos += scan_speed
            elif scan_line_pos >= width and not scan_completed:
                scan_completed = True
                print("Tarama tamamlandı! Videoyu kaydetmek için 's' tuşuna basın.")
            else:
                # Duraklatıldığında canlı kamera görüntüsünü tarama çizgisinin sağında göster
                current_result[:, scan_line_pos:] = frame[:, scan_line_pos:]
        
        # Tarama çizgisini çiz (mavi renkte)
        if direction == '1' and scan_line_pos < height:
            cv2.line(current_result, (0, scan_line_pos), (width, scan_line_pos), (255, 0, 0), 2)
        elif direction == '2' and scan_line_pos < width:
            cv2.line(current_result, (scan_line_pos, 0), (scan_line_pos, height), (255, 0, 0), 2)
        
        # Kayıt için kareyi listeye ekle
        if is_recording:
            video_frames.append(current_result.copy())
            
            # Kayıt bilgisini göster
            cv2.putText(current_result, "REC", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Sonuç görüntüsünü göster
        cv2.imshow('Time Warp Scan', current_result)
        
        # Tuş kontrolü
        key = cv2.waitKey(1)
        
        # ESC tuşuna basılırsa çık
        if key == 27:  # ESC tuşunun ASCII kodu
            break
            
        # 'r' tuşuna basılırsa efekti sıfırla ve kaydı durdur
        elif key == ord('r'):
            # Kaydı sıfırla
            video_frames = []
            is_recording = True
            is_paused = False
            
            # Efekti sıfırla
            result = np.zeros_like(frame)
            scan_line_pos = 0
            scan_completed = False
            
        # 's' tuşuna basılırsa ve tarama tamamlandıysa videoyu kaydet
        elif key == ord('s') and scan_completed:
            save_video(video_frames, width, height)
            video_frames = []  # Belleği temizle
            
        # Space tuşuna basılırsa taramayı durdur/devam ettir
        elif key == 32:  # Space tuşunun ASCII kodu
            is_paused = not is_paused
            if is_paused:
                print("Tarama duraklatıldı. Devam etmek için tekrar SPACE tuşuna basın.")
            else:
                print("Tarama devam ediyor.")
            
    # Temizlik işlemleri
    cap.release()
    cv2.destroyAllWindows()

def save_video(frames, width, height):
    if not frames:
        print("Kaydedilecek kare bulunamadı!")
        return
        
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    video_path = f"time_warp_videos/time_warp_{timestamp}.avi"
    
    # Video yazıcıyı oluştur
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))
    
    print(f"Video kaydediliyor: {video_path}")
    
    # Tüm kareleri videoya yaz
    for frame in frames:
        out.write(frame)
    
    # Video yazıcıyı kapat
    out.release()
    print(f"Video başarıyla kaydedildi: {video_path}")

if __name__ == "__main__":
    time_warp_scan()
