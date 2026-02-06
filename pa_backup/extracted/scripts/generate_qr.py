import qrcode
import sys

url = sys.argv[1] if len(sys.argv) > 1 else "https://three-jokes-jump.loca.lt"
print(f"Generating QR for: {url}")

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("mobile_qr.png")
