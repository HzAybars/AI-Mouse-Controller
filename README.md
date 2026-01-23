# AI Mouse Controller - Depth Adaptive

Bu proje, bilgisayar kamerasını kullanarak imleci el hareketleriyle kontrol etmeyi sağlayan, Python tabanlı bir görüntü işleme uygulamasıdır. Standart el takibi projelerinden farklı olarak, elin kameraya olan uzaklığını hesaplayan dinamik bir derinlik algoritmansı kullanır.

## Proje Hakkında

Geleneksel el takibi yazılımları, el kameraya yaklaştığında veya uzaklaştığında piksel bazlı eşik değerleri nedeniyle hatalı tıklamalar yapabilir. Bu proje, "Scale Reference" (Ölçek Referansı) mantığı ile çalışır. Elin o anki boyutunu analiz eder ve tıklama/sürükleme hassasiyetini dinamik olarak günceller. Bu sayede kullanıcı kameraya hangi mesafede olursa olsun stabil bir deneyim sunar.

## Temel Özellikler

* **Derinlik Uyarlı Hassasiyet:** El boyutuna göre otomatik kalibre olan tetikleme mekanizması.
* **Jitter (Titreme) Önleme:** İmleç hareketlerini pürüzsüzleştiren enterpolasyon ve yumuşatma algoritmaları.
* **Çoklu Mod Desteği:** İmleç kontrolü, tıklama ve sürükle-bırak işlemleri için ayrı modlar.
* **Optimize Edilmiş Performans:** Görüntü işleme işlemleri ayrı bir thread üzerinde çalıştırılarak FPS kaybı önlenmiştir.

## Gereksinimler

Projenin çalışması için aşağıdaki Python kütüphanelerine ihtiyaç vardır:

* Python 3.x
* opencv-python
* mediapipe
* numpy
* pywin32

## Kurulum

Projeyi yerel makinenize klonlamak ve çalıştırmak için aşağıdaki adımları izleyin:

1.  **Depoyu Klonlayın:**
    ```bash
    git clone [https://github.com/HzAybars/AI-Mouse-Controller.git](https://github.com/HzAybars/AI-Mouse-Controller.git)
    cd AI-Mouse-Controller
    ```

2.  **Bağımlılıkları Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Uygulamayı Başlatın:**
    ```bash
    python main.py
    ```

## Kullanım Kılavuzu

Uygulama başlatıldığında kamera açılacak ve el hareketlerini takip etmeye başlayacaktır.

### Hareket Kontrolleri

| Eylem | Hareket Tanımı |
| :--- | :--- |
| **İmleç Hareketi** | İşaret parmağınızı kamera görüş açısı içinde hareket ettirin. |
| **Sol Tık** | Başparmak ve işaret parmağınızı birbirine değdirin (Pinch). |
| **Sağ Tık** | Başparmak ve orta parmağınızı birbirine değdirin. |
| **Sürükle & Bırak** | Elinizi yumruk yapın. Bu modda iken imleç kilitlenir ve nesneleri taşıyabilirsiniz. |
| **İmleç Kilitleme** | Tıklama yaparken imlecin kaymaması için sistem, parmaklar birbirine çok yaklaştığında hareketi geçici olarak dondurur.

### Algoritma Detayları

Sistem, MediaPipe kütüphanesi üzerinden elin 21 noktasını (landmark) takip eder.
* **Referans Uzunluk:** Bilek (0) ve Orta Parmak Kökü (9) arasındaki Öklid mesafesi hesaplanır.
* **Dinamik Eşik:** Tıklama hassasiyeti sabit bir piksel değeri yerine, hesaplanan referans uzunluğun belirli bir yüzdesi (%25) olarak belirlenir.

## Lisans ve Yazar

MIT License

Copyright (c) 2026 HzAybars

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
