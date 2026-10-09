### LocalDoc test (held-out) (1000 texts)
| System | Protected (all PII) | Leak rate | Precision |
|---|---|---|---|
| Pərdə | 94.9% | 5.1% | 93.0% |
  MISS BUILDINGNUM: '8' :: Təchizatçı materialları Callan's Lane, 8, AZ 1801 ünvanına çatdıracaq. Xahiş edirik, çatdırılan materialı qəbul etmək üç
  MISS BUILDINGNUM: '8' :: Təchizatçı materialları Callan's Lane, 8, AZ 1801 ünvanına çatdıracaq. Xahiş edirik, çatdırılan materialı qəbul etmək üç
  MISS BUILDINGNUM: '3' :: 21:42:10 Veysəl: Mənim ünvanım: V.PLOTNİKOV pr. 3, Yevlax, AZ 5327.
  MISS GIVENNAME: 'Ələsgər' :: 22:48:43 Ələsgər: Mənim nömrəm 012 479 00 59.
  MISS DATE: '1987/01/01' :: Yubileyimiz: 1987/01/01
  MISS GIVENNAME: 'Xəyyam' :: Kimdən: Çiçək Şıxlı
Kimə: Xəyyam Musazadə
Tarix: 10-12-1978
Mövzu: Ağac Evinin Dizaynı üzrə 2014-02-13 tarixində görü
  MISS GIVENNAME: 'Əflatun' :: Yavər: 'Problem deyil, bölüşməkdən məmnunam! Yeri gəlmişkən, Əflatunun yeni yemək kitabını görmüsən? navrhar seamless in
  MISS BUILDINGNUM: '3' :: 03:58:22 Xudu: Bəli, S.S. AXUNDOV prospekti 3-də əla bir yer var. Çox tövsiyə edirəm.
  MISS BUILDINGNUM: '1' :: Niyaz Abdullazadə, məzun olmağınız münasibətilə sizi təbrik edirik! Diplomunuzu 1 S.S. AXUNDOV pr.-dən götürə bilərsiniz
  MISS STREET: 'S.S. AXUNDOV pr.' :: Niyaz Abdullazadə, məzun olmağınız münasibətilə sizi təbrik edirik! Diplomunuzu 1 S.S. AXUNDOV pr.-dən götürə bilərsiniz
  MISS BUILDINGNUM: '8' :: Hər kəsə salam, mən qrup çatdan Turxan. Xahiş edirəm, xatirə və ehtiram kitab layihəsi üçün NEMƏT QULİYEV prospekti və 8
  MISS STREET: 'AKAD.H.ƏLİYEV küç.' :: Kimdən: hemid_69@yahoo.com
Kimə: simuzer28@bk.ru
Mövzu: Unikal İmza Analizi Məktubu - Zəhmət olmasa, təhlil üçün yazılı 
  MISS SURNAME: 'İsmayılqızı' :: Mənim adım Ceyla İsmayılqızıdır və mənim 57 yaşım var. Bu təlim qrupunun bir hissəsi olmaqdan çox həyəcanlıyam.
  MISS BUILDINGNUM: '5' :: Resept formasında, zəhmət olmasa, sahələri 0U51BU4, Nisə və 5 ilə doldurun.
  MISS STREET: 'BAKI-BATUMİ küç.' :: Nəzərinizə çatdırırıq ki, Lətifə Məhərrəmzadə yüngül dəmir yolu stansiyası, BAKI-BATUMİ küç. 0 qazıntı sahəsinə ən yaxın
| Pərdə without name detector | 41.1% | 58.9% | 96.0% |
| Generic regex baseline | 23.9% | 76.1% | 96.4% |
Per entity (Pərdə):
| Entity | Gold | Recall (right type) | Protected | Precision |
|---|---|---|---|---|
| PERSON | 1144 | 97.2% | 97.4% | 90.6% |
| PHONE | 184 | 100.0% | 100.0% | 100.0% |
| EMAIL | 132 | 100.0% | 100.0% | 99.2% |
| ID_NUMBER | 165 | 100.0% | 100.0% | 100.0% |
| CARD | 25 | 100.0% | 100.0% | 100.0% |
| DATE | 117 | 80.3% | 80.3% | 78.5% |
| ADDRESS | 298 | 74.8% | 82.2% | 97.1% |
### Hand-written AZ/RU/EN cases (20 texts)
| System | Protected (all PII) | Leak rate | Precision |
|---|---|---|---|
| Pərdə | 98.7% | 1.3% | 96.6% |
  MISS GIVENNAME: 'Ульвия' :: zəng: 0705552211 - Ульвия, deyir ki kuryer gəlməyib, ünvan Azadlıq prospekti 33
| Pərdə without name detector | 56.6% | 43.4% | 100.0% |
| Generic regex baseline | 28.9% | 71.1% | 100.0% |
Per entity (Pərdə):
| Entity | Gold | Recall (right type) | Protected | Precision |
|---|---|---|---|---|
| PERSON | 33 | 97.0% | 97.0% | 90.0% |
| PHONE | 9 | 100.0% | 100.0% | 100.0% |
| EMAIL | 4 | 100.0% | 100.0% | 100.0% |
| ID_NUMBER | 14 | 100.0% | 100.0% | 100.0% |
| CARD | 3 | 100.0% | 100.0% | 100.0% |
| DATE | 3 | 100.0% | 100.0% | 100.0% |
| ADDRESS | 10 | 100.0% | 100.0% | 100.0% |
