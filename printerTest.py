from escpos.printer import Usb
from escpos.constants import QR_ECLEVEL_M, QR_MODEL_2
import dotenv
import os


dotenv.load_dotenv(".env")
# p = Usb(
#     int(os.getenv("VENDOR_ID"), base=16), int(os.getenv("PROD_ID"), base=16)
# )

p = Usb(0x0483, 0x070b)

p.qr("6969", ec=QR_ECLEVEL_M, center=True, size=16, model=QR_MODEL_2)
p.cut()