import requests, base64, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

URL = "https://interbus.ingeniacom.com/ApiVentaIngenia/Api/DeparturesTaq?InitialVector=RmNxMjdSczN5MXAwQnY1dw%3D%3D"
HEADERS = {
    "Content-Type": "application/json"
}

AES_KEY = b"Fcq27Rs3y1p0Bv5w"
AES_IV = b"Fcq27Rs3y1p0Bv5w"

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
    ciphertext_b64 = ciphertext_b64.strip().strip('"') # remove outer double quotes

    ciphertext = base64.b64decode(ciphertext_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    return unpad(decrypted_padded, AES.block_size)  # devuelve bytes

def web_request(body):
    body = json.dumps(body)  # adds wrapping double quotes

    r = requests.post(URL, data=body, headers=HEADERS, timeout=30)
    return r.text

def get_available_seats(response_text, target_datetime="2026-11-08T20:00:00"):
    data = json.loads(response_text)

    for dep in data.get("DepartureDepartures"):
        if dep["Departure_time"] == target_datetime:
            return dep["Available_seats"]

    print(f"No existe salida a las {target_datetime}")
    return None


date=input("Enter the date in the following format '2026-11-25': ")
time=input("Enter the time in the following format '20:00': ")

datetime = date + "T" + time + ":00"

body = build_body(date) # Build Body depending on trip date, as Python Dict
processed_body = encrypt_aes(json.dumps(body)) # Converts Dict to JSON and then Encrypt using AES

encrypted_response = web_request(processed_body)
response_text = decrypt_aes(encrypted_response).decode()

print(response_text)
print(get_available_seats(response_text, datetime))