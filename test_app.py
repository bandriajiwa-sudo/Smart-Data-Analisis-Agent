import httpx
import time
import json

API_URL = "http://127.0.0.1:8000/api/v1/run-agent"
HEADERS = {
    "Authorization": "Bearer dev_key",  # Sama kayak API_KEY di .env
    "Content-Type": "application/json"
}

# Payload / chat interaksi ke bot kasir kita
PAYLOAD = {
    "user_id": "kasir_test_01",
    "pesan": "Tolong buatin rekap dong, apa aja sih tabel schema yang nempel di pos ini? Kasih overview produk kita aja.",
    # Lo bisa buka webhook.site dan ganti URL ini pakai endpoint fresh punya lo!
    "webhook_url": "https://webhook.site/e5da8669-e339-4444-a957-c8665306e6bf",  
    "webhook_secret": "rahasia_illahi_webhook_key_123"
}

print("="*60)
print(f"🚀 MENGIRIM PROMPT KE AI (User: {PAYLOAD['user_id']})")
print(f"💬 Pertanyaan: '{PAYLOAD['pesan']}'")
print("="*60)

try:
    with httpx.Client() as client:
        resp = client.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=10.0)
        print(f"\n[HTTP {resp.status_code}] Response dari Server:")
        print(json.dumps(resp.json(), indent=2))
        
        if resp.status_code == 202:
            print("\n✅ API SUKSES! Agent AI sekarang lagi mikir di background (Non-Blocking).")
            print(f"Cek hasil rangkuman AI lo 5-10 detik lagi di 👉 {PAYLOAD['webhook_url']}")
        else:
            print("\n❌ Gagal mengirim request. Cek config .env lo!")
except Exception as e:
    print(f"\n🚨 ERROR SERVER MATI: {e}")
    print("Hint: Pastikan lo udah nge-run 'uvicorn app.main:app' di terminal terpisah sebelum nge-run file script test ini!")
