-- ==============================================================================
-- SMART POS AGENT - SUPABASE QUICK SETUP SCRIPT
-- Jalankan skrip DDL SQL ini langsung di "SQL Editor" pada Dashboard Supabase!
-- ==============================================================================

-- 1. Bikin Role Khusus (Read Only) biar AI kita bisa nge-baca data warisan lo dengan Aman.
-- Ganti bagian sandi rahasia di bawah pake sandi yg kuat banget.
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ai_agent_readonly') THEN
      CREATE ROLE ai_agent_readonly LOGIN PASSWORD 'SandiSuperAman123!';
   END IF;
END
$do$;

-- 2. Kasih Izin Si Agent Buat Bebas BACA (SELECT-Only) Seluruh Table di Skema Public
GRANT USAGE ON SCHEMA public TO ai_agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ai_agent_readonly;

-- 3. (CATATAN CHEKPOINTER)
-- Nggak perlu nulis script bikin tabel Checkpointer (LangGraph Memory).
-- Karena kalau lo colokin String Supabase lo via `.env` port 5432, 
-- Mesin python kita otomatis nge-eksekusi `await checkpointer.setup()`
-- dan dia otomatis ngelahirin/bikin tabel memorinya sendiri (checkpoints, blob, dll)!
