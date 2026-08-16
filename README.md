# Smart Data Analyst Agent

**Non-Invasive Cognitive Layer for Legacy POS.**
Sistem enterprise-grade yang menambahkan kapabilitas agentic AI LLM ke PostgreSQL _legacy system_ tanpa menyentuh source code utama Anda.

## 🚀 Fitur Utama Topologi Sistem

- **LangGraph State Machine**: Orchestrator flow berbasis Node interaktif.
- **Dynamic Introspection (W2 & W10)**: _Cacheable Postgres schema lookup_.
- **Self-Healing SQL (W5)**: Memperbaiki kueri yang gagal dieksekusi secara otomatis dan rekursif (max 3 retry trial).
- **Asynchronous Webhook (W6)**: Mencegah pemblokiran HTTP API. Memiliki _exponential backoff_ jika server pelapor lumpuh.
- **Rate-Limiting & Sanitization (W8)**: Melindungi Endpoints dengan perlindungan middleware `slowapi` dan Regex anti SQL-Injection.
- **Postgres Checkpointer (W7)**: _Stateful chat thread memory_ untuk _multi-turn conversational context_.

## ⚙️ Persyaratan Target

- Python 3.11+
- PostgreSQL 15+
- Docker Engine & Docker Compose
- Lingkungan API Key (OpenAI API Model, dll)

## 🛠 Instalasi dan Konfigurasi Lokal

1. Buat _Virtual Environment_ & Install Dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # (Windows: .\venv\Scripts\activate.ps1)
    pip install -r requirements.txt
    ```
2. Setup konfigurasi spesifik environment. Rename `.env.example` ke `.env` lalu edit konfigurasi token Anda.
3. Jalankan _dummy database_ & Server via Docker Compose CI.
    ```bash
    docker-compose up -d
    ```
4. Navigasi portal dokumentasi Swagger OpenAPI `http://localhost:8000/docs`

## 🚦 Unit Testing UAT (Fase 4 - W11)

Sistem memiliki test pipeline **Integration Testing** yang dijalankan manual secara sinkron dari root:

```bash
pytest tests/ -v
```

## 📦 Deployment Prod (Fase 4 - W12)

Auto-deployment _staging server_ didukung script bash.

```bash
chmod +x deploy.sh
./deploy.sh
```

Didukung dengan Github Actions CI terintegrasi (`.github/workflows/ci.yml`).

---

_Architected automatically during the Google Antigravity Session_
