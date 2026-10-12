import requests
import base64, json, time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

URL = "https://interbus.ingeniacom.com/ApiVentaIngenia/Api/DeparturesTaq?InitialVector=RmNxMjdSczN5MXAwQnY1dw%3D%3D"
HEADERS = {"Content-Type": "application/json"}

AES_KEY = b"Fcq27Rs3y1p0Bv5w"
AES_IV = b"Fcq27Rs3y1p0Bv5w"

def load_config():
    with open("config.json") as file:
        return json.load(file)

def discord_notify(message):
    try:
        payload = json.dumps({"content": message})
        r = requests.post(WEBHOOK, headers=HEADERS, data=payload)
        status = r.status_code
        text = r.text
        r.close()

        if status // 100 == 4:
            print("Client Side error connecting to Discord", status, text)
        elif status // 100 == 5:
            print("Server Side error connecting to Discord:", status, text)
    
    except Exception as e:
        print("Error connecting to Discord:", e)

def build_body(date, trip="Toledo_CiudadReal"):
    if trip=="Toledo_CiudadReal":
        origin="127"
        destination="053"
    elif trip=="CiudadReal_Toledo":
        origin="053"
        destination="127"

    return {
        "Lang": "ES",
        "User": "INGENIA",
        "Password": "ONLINE21",
        "Origin_id": origin,
        "Destination_id": destination,
        "Departure_time": date,
        "Return_time": date,
        "NumberPassengers": "1",
        "PassengersFare": ["01"],
        "ReturnType": 0,
        "AddAdditionalServices": 0,
        "IdSession": 0
    }

def encrypt_aes(plaintext, key=AES_KEY, iv=AES_IV):
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    return base64.b64encode(ciphertext).decode("utf-8")

def decrypt_aes(ciphertext_b64, key=AES_KEY, iv=AES_IV):
    ciphertext = base64.b64decode(ciphertext_b64)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    return unpad(decrypted_padded, AES.block_size).decode()

def web_request(body):
    body = json.dumps(body)  # adds wrapping double quotes

    r = requests.post(URL, data=body, headers=HEADERS, timeout=30)
    return r.text

def get_available_seats(response_text, target_datetime="2026-11-08T20:00:00"):
    data = json.loads(response_text)

    for dep in data.get("DepartureDepartures"):
        if dep["Departure_time"] == target_datetime:
            return dep["Available_seats"]

    print(f"No bus at {target_datetime}")
    return None



# ===================== MAIN ==========================

# ===== Load Config from config.json =====
config = load_config()
WEBHOOK = config["WEBHOOK"]

# by the moment static at config.json
DAYS = config["DAYS"]
HOURS = config["HOURS"]

datetimes = []
for day in DAYS:
    for hour in HOURS:
        datetimes.append(day + "T" + hour + ":00")

# ===== Main Loop =====
while True:
    for date_time in datetimes:
        # PREPARE REQUEST'S BODY
        body = build_body(date_time[:10]) # Build Body depending on trip date, as Python Dict
        processed_body = encrypt_aes(json.dumps(body)) # Converts Dict to JSON and then Encrypt using AES

        # THROW REQUEST
        encrypted_response = web_request(processed_body)
        response_text = decrypt_aes(encrypted_response)

        # EXTRACT AVAIABLE SEATS AND NOTIFY ON DISCORD
        seats = get_available_seats(response_text, date_time)
        if seats and (seats > 0): # if non null and bigger than 0: notify
            discord_notify(f"Seats for {date_time[:10]} at {date_time[-8:]} -> {seats}")
    
    time.sleep(30) # repeat each 30 min