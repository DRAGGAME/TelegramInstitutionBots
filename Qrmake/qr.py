import qrcode

# Ссылка для QR-кода
url = "https://t.me/Draggame_test_bot?start=Nikolskaya10"

# Создание QR-кода
qr_image = qrcode.make(url)
# 806328887

# Сохранение QR-кода в файл
qr_image.save('Nikolskaya10.png')


