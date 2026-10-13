## BusTicketNotifier
A personal project to monitor Interbus ticket releases using HTTP requests and Discord webhook.

## Goals
- Practice making HTTP requests using the Python *requests* library.
- Learn how to encrypt and decrypt data using AES given a key and IV, using the *pycryptodome* library.
- Practice parsing JSON data.
- Set up a Discord webhook to receive notifications while the script runs in the background.

## API Analysis
`/ApiVentaIngenia/Api/DeparturesTaq?InitialVector=RmNxMjdSczN5MXAwQnY1dw==` allows POST Request with `"Content-Type": "application/json"` and a encrypted body using AES (key and IV were extracted from public JS) and wrapped in double quotes

It responds with another JSON object encrypted with the same algorithm, which can be easily decrypted and analyzed.

## Setup
1. Install dependencies
```bash
pip install -r requirements.txt
```
2. Copy `config.example.json` to `config.json` and fill in your webhook and trips
3. Run it
```bash
python main.py
```

## Disclaimer
This project is for **educational and personal use only**. It is not affiliated with or connected to Interbus, Ingenia, or any related company.
- Responsible use: Keep the polling interval reasonable to avoid overloading the service. Do not use this tool for abusive or automated mass requests.
