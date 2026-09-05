# Megumi Kato

Personal AI companion project. Local-first, zero-budget, built from scratch.

> Private repository — for personal development tracking only. Not intended for public use or distribution.

## Stack
- **LLM:** Qwen3.5:4b via Ollama (local, no cloud API)
- **Language:** Python 3.11
- **Memory:** SQLite (WAL mode)
- **Personality:** YAML-based character definition + turn-based few-shot examples
- **Architecture:** Modular — `core/`, `personality/`, `memory/`, `tools/`

## Status
Currently on **Fase 5** (Tools Tier 2). See `/docs/ROADMAP.md` for full progress tracking across all phases.

## Notes
- No thinking/reasoning mode (hard-disabled — known closing-tag bug in Qwen3.5:4b's thinking variant on this quantization).
- Character personality inspired by Megumi Kato (*Saenai Heroine no Sodatekata*) — for personal, non-commercial use only.

# Project "Megumi Kato" — Roadmap & Progress Tracker

> Personal AI companion. Local-first, zero-budget, built from scratch.
> Last updated: 2026-09-05

---

## Status Ringkas

| Fase | Status |
|---|---|
| 1 — Core Foundation | ✅ Selesai |
| 2 — Personality Dasar | ✅ Selesai |
| 2B — Kualitas Kode & Logging | ✅ Selesai |
| 3 — Memory System | ✅ Selesai |
| 4 — Tools Tier 1 | ✅ Selesai |
| 5 — Tools Tier 2 | ✅ Selesai |
| 6 — Mood System | 🔶 Berikutnya |
| 7 — Voice Output | 🔲 Belum |
| 8 — Personality Polish | 🔲 Belum |
| 9 — Voice Input | 🔲 Belum |
| 10 — Live2D + Proactive Loop | 🔲 Belum |
| 11 — Native Android App | 🔲 Belum |
| 12 — Ekosistem Lanjutan | 🔲 Belum |

---

## FASE 1 — Core Foundation ✅

- Core, config, orchestrator
- Thinking mode hard-disabled total — bug closing-tag di varian thinking Qwen3.5:4b, model tidak pernah keluar dari blok `<think>`, menghabiskan seluruh token budget tanpa hasil

## FASE 2 — Personality Dasar ✅

- Base character Megumi — riset kanon: kind, non-confrontational, tsukkomi-style dry humor, bukan kritis/blak-blakan (koreksi dari draft awal yang overstated)
- Few-shot disusun sebagai actual conversation turns (bukan text blob di system prompt) — signifikan memperbaiki reliability model kecil
- Mix bahasa Indonesia/Inggris/code-switch, filler proporsional, anti-fabrikasi data

## FASE 2B — Standar Kualitas Kode & Logging ✅

- Audit SRP, modularitas, type hints, error handling
- Automated logging `.txt` per sesi

## FASE 3 — Memory System ✅

- `deque(maxlen=55)` short-term + SQLite WAL: `memories`, `activity_log`, `chat_history`
- Fix kritis: keyword extraction (sebelumnya auto-inject memory nyaris tidak pernah match karena search pakai kalimat mentah utuh)
- Multi-keyword OR search, category enum, `reset_all()`, SQL wildcard sanitization

**Batasan diketahui:** keyword search tidak menangkap hubungan semantik dalam 1 bahasa (`"pemrograman"` ≠ `"python"`).

## FASE 4 — Tools Tier 1 ✅

- `time_tools.py`, `web_search_tools.py`, `registry.py`, `tool_dispatcher.py`, `llm_client.py` (`ChatResponse` dataclass), `orchestrator.py` (native tool-calling loop, `MAX_TOOL_ITERATIONS=3`)
- `save_memory` otomatis dari obrolan natural — tervalidasi konsisten
- **Bug #1 RESOLVED**: `get_current_time` diarsitektur ulang jadi `TimeCache` (ambient context, refresh 30 menit) + tool `verify_exact_system_clock` (dipanggil eksplisit untuk presisi). Menghilangkan celah round-trip yang bikin waktu "hilang" dari respons, sekaligus mempertahankan agency model untuk cek ulang kalau perlu.
- **Bug #2 RESOLVED**: anti-fabrikasi bertahan meski user eksplisit "kasih izin nebak" — tervalidasi ulang di skenario yang sama persis dengan yang gagal sebelumnya
- Response time: non-tool ~2-4 detik, tool-call 4-9 detik, cold start ~14-15 detik di awal sesi (perilaku Ollama normal)

**Temuan baru — keterbatasan bilingual recall:** `recall_memory` cuma reliable kalau query dan `content` tersimpan sama-sama Bahasa Inggris. Query Indonesia gagal match ke memory berbahasa Inggris (`"belajar"` ≠ `"learning"`), dan translate-on-the-fly tidak menyelesaikan akar masalah karena ambiguitas sinonim (`belajar` → `learn` atau `study`?). Diterima sebagai limitasi diketahui — solusi sesungguhnya (embedding-based search) ditunda ke Parking Lot, digabung dengan Knowledge Base RAG.

**Catatan minor (non-blocking, untuk Fase 8):** sesekali respons kurang natural follow-up; 1 kesalahan fakta umum ditemukan (atribusi lagu salah). Belum tervalidasi: pertanyaan waktu versi Inggris murni, siklus refresh `TimeCache` di sesi >30 menit.

---

## FASE 5 — Tools Tier 2 (Desktop Agent) ✅

- [x] `get_weather` — Pengecekan cuaca real-time lokasi spesifik via API publik wttr.in
- [x] `web_page_reader` — Ekstraksi teks bersih dari URL spesifik (pelengkap `web_search`)
- [x] `system_tools` — Desktop Management:
  - [x] `manage_local_file`: CRUD file sandboxed di `D:\Megumi Kato` (.txt, .md, .pdf)
  - [x] `manage_application`: Buka/tutup aplikasi desktop dengan proteksi blocklist
  - [x] `get_system_status`: Read-only metrik hardware (CPU, RAM, Baterai)
- [ ] **Setelah fase ini selesai: clear database** (sebelum Fase 6 mood system aktif, supaya mood_score mulai dari kondisi bersih)

## FASE 6 — Mood/Love Meter System

- State-tracking berbasis rule (bukan RL — sudah dipertimbangkan dan ditolak karena reward signal terlalu jarang/lambat untuk kasus ini)
- Trait independent opinion (bukan yes-man)

## FASE 7 — Voice Output (text-in → voice-out)

- Engine: **GPT-SoVITS** (dipilih atas Chatterbox — cross-lingual English matang, fidelity lebih baik untuk sumber suara anime Jepang)
- Voice sample Megumi diekstrak per kategori emosi (neutral/happy/sad/serious/surprised), dari klip per-kalimat (bukan full-length)
- **Keputusan desain:** voice mode = selalu full English, apapun bahasa input user. Text chat tetap mirror bahasa user seperti biasa. Alasan: karakter Megumi berbahasa Indonesia terasa mismatch budaya komunikasi (gaya deadpan yang natural di Jepang bisa terbaca ketus/"jahat" dalam norma komunikasi Indonesia yang lebih high-context).
- Wajib latency-masking (streaming response / acknowledgment cepat) — response time 4-9 detik akan terasa sangat lama sebagai silence di voice

## FASE 8 — Deep Personality Polish

- [ ] Perbaiki kesalahan fakta umum yang ditemukan (contoh: atribusi lagu/band)
- [ ] Tuning konsistensi follow-up response (natural vs bare fact)
- [ ] Testing ekstensif berbagai skenario (santai, diskusi serius, curhat emosional)

## FASE 9 — Voice Input (full voice)

- faster-whisper (STT) + VAD

## FASE 10 — Visual Character Live2D (Laptop) + Proactive Loop Dasar

- Pipeline `see-through` (layer decomposition dari 1 gambar) + `Anime2.5DRig` (auto-rigging, browser-based)
- Physics interaction (drag, throw, idle movement), tool `switch_presence_mode`
- Scheduler sederhana (SQL query ke `activity_log`/`chat_history`) → `trigger_reason` → AI inisiatif ngobrol duluan
- Interruption budget + quiet hours (referensi: OpenWatari)
- Journal log khusus pesan proaktif (`is_proactive` flag)
- `OLLAMA_KEEP_ALIVE=-1` untuk mode always-on

## FASE 11 — Native Android App

- Chibi/sprite version dulu, Live2D Cubism SDK Android belakangan
- Integrasi OPPO Band (OHealth → Android Health Connect API: sleep, heart rate, steps)

## FASE 12 — Ekosistem Lanjutan

- Server API, IoT sensors, home server migration, LINE bot (Messaging API resmi)

---

## PARKING LOT

### Kelompok A — Prasyarat Fase 10/11
- Vision: webcam presence detection, CCTV 360° RTSP integration
- Ambient awareness penuh, curfew system (progressive lock + screenshot verification)
- Confirmation-gate-enforced-in-code (referensi: OpenWatari) — untuk aksi invasif (force lock, dll), bukan cuma diatur via prompt
- Knowledge Base RAG (`nomic-embed-text` + ChromaDB) — untuk dokumen/catatan personal
- **[Prioritas naik]** Upgrade `memories` ke embedding-based semantic search — satu paket teknologi dengan Knowledge Base RAG, menyelesaikan gap semantik 1-bahasa DAN gap bilingual sekaligus
- IoT sensor integration (home server)

### Kelompok B — Opsional/Pelengkap
- LINE bot (Messaging API resmi, bukan otomasi akun personal), email personal AI
- Engineering mode, career support mode

### Kelompok C — Eksperimen Terpisah
- RL/contextual bandit untuk mood — final decision: state-tracking, bukan RL
- Server API multi-device

### Kelompok D — Multi-Agent Era (butuh hardware ~32B+)
- Agent Analis asynchronous (interval 2-3 jam) → tabel `pattern_reports`
- Companion agent baca laporan sebagai enhancement kualitas inisiatif (bukan syarat)
- Reversible-only git untuk self-improvement (referensi: OpenWatari — no reset/force-push/rebase, revert selalu commit baru)
- Upgrade model companion utama seiring hardware upgrade

### Kelompok E — Catatan Desain (referensi, bukan fase)
- L2 Journal & L4 Hot-cache (referensi: OpenWatari 6-layer memory) — dipetakan ke Fase 10
- Eksplainability advantage Anima (1 model spesifik vs framework generik) — pertahankan
- TTFT (Time To First Token) sebagai metrik krusial voice — pantau ketat di Fase 7-9

---

## Keputusan Arsitektur Kunci (jangan diubah tanpa alasan kuat)

- **100% lokal, zero budget** — no cloud API, no VPS
- **Modular, config-driven, dependency injection** di semua layer
- **Native tool-calling, tanpa LangChain/LangGraph** — kontrol penuh, transparansi debugging
- **Hal yang bisa dihitung statistik/SQL, jangan dibebankan ke LLM** — prinsip konsisten dipakai di: mood system, curfew verification, deteksi pola aktivitas
- **Thinking mode permanen off** — bug model-level, bukan sesuatu yang bisa diperbaiki dari prompt
