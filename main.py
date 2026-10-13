import requests
import base64, json, time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime

URL = "https://interbus.ingeniacom.com/ApiVentaIngenia/Api/DeparturesTaq?InitialVector=RmNxMjdSczN5MXAwQnY1dw%3D%3D"
HEADERS = {"Content-Type": "application/json"}

AES_KEY = b"Fcq27Rs3y1p0Bv5w"
AES_IV = b"Fcq27Rs3y1p0Bv5w"


# ===== Config =====
def load_config():
    with open("config.json") as file:
        return json.load(file)

def init():
    config = load_config()
    webhook = config["WEBHOOK"]

    trips = []  # list with tuples: (trip, datetime)

    for day in config["DAYS_TOLEDO_CR"]:
        for hour in config["HOURS_TOLEDO_CR"]:
            trips.append(("Toledo_CiudadReal", f"{day}T{hour}:00"))

    for day in config["DAYS_CR_TOLEDO"]:
        for hour in config["HOURS_CR_TOLEDO"]:
            trips.append(("CiudadReal_Toledo", f"{day}T{hour}:00"))

    return webhook, trips

# ===== Discord =====
def discord_notify(webhook, message):
    try:
        payload = json.dumps({"content": message})
        r = requests.post(webhook, headers=HEADERS, data=payload, timeout=30)
        print(message) # we send to discord but also print in terminal
        status = r.status_code
        text = r.text
        r.close()

        if status // 100 == 4:
            print("Client Side error connecting to Discord", status, text)
        elif status // 100 == 5:
            print("Server Side error connecting to Discord:", status, text)

    except Exception as e:
        print("Error connecting to Discord:", e)

# ===== Interbus API =====
def build_body(date, trip="Toledo_CiudadReal"):
    if trip == "Toledo_CiudadReal":
        origin, destination = "127", "053"
    elif trip == "CiudadReal_Toledo":
        origin, destination = "053", "127"

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

# ====== AES stuff ======
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

# === Throw POST requests ===
def web_request(body):
    body = json.dumps(body)  # adds wrapping double quotes

    r = requests.post(URL, data=body, headers=HEADERS, timeout=30)
    return r.text

# === Process Response ===
def get_available_seats(response_text, target_datetime):
    data = json.loads(response_text)

    for dep in data.get("DepartureDepartures"):
        if dep["Departure_time"] == target_datetime:
            return dep["Available_seats"]

    print(f"No bus at {target_datetime}")
    return None


# ===== Main Loop =====
def main(webhook, trips):
    for trip, date_time in trips:
        try:
            # PREPARE REQUEST'S BODY
            body = build_body(date_time[:10], trip)
            processed_body = encrypt_aes(json.dumps(body))

            # THROW REQUEST
            encrypted_response = web_request(processed_body)
            response_text = decrypt_aes(encrypted_response)

            # EXTRACT AVAILABLE SEATS AND NOTIFY ON DISCORD
            seats = get_available_seats(response_text, date_time)
            if seats and seats > 0:
                label = trip.replace("_", " → ")
                discord_notify(
                    webhook,
                    f"[{label}] Seats for {date_time[:10]} at {date_time[-8:]} -> {seats}",
                )
        except Exception as e:
            print(f"Error processing {trip} {date_time}:", e)


if __name__ == "__main__":
    webhook, trips = init()
    discord_notify(webhook, f"Started at: [{datetime.now():%Y-%m-%d %H:%M:%S}]")

    while True:
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}]")
        main(webhook, trips)
        time.sleep(600)  # repeat each 10 min