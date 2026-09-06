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
Currently on **Fase 6** (Mood/Love Meter System — implementation done, testing pending). See roadmap below for full progress tracking across all phases.

## Notes
- No thinking/reasoning mode (hard-disabled — known closing-tag bug in Qwen3.5:4b's thinking variant on this quantization).
- Character personality inspired by Megumi Kato (*Saenai Heroine no Sodatekata*) — for personal, non-commercial use only.
- CLI supports system commands: `/clear`, `/reset`, `/help`, `/quit` (see `core/command_handler.py`).

---

# Project "Megumi Kato" — Roadmap & Progress Tracker

> Personal AI companion. Local-first, zero-budget, built from scratch.
> Last updated: 2026-09-07

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
| 5.1 — Inspection Tools & Context Anchoring Fix | ✅ Selesai (⏳ re-test final pending) |
| 6 — Mood/Love Meter System | 🔶 Implementasi selesai, testing berjalan |
| 7 — Voice Output | 🔲 Belum |
| 8 — Personality Polish | 🔲 Belum |
| 9 — Voice Input | 🔲 Belum |
| 10 — Live2D + Proactive Loop | 🔲 Belum |
| 11 — Native Android App | 🔲 Belum |
| 12 — Ekosistem Lanjutan | 🔲 Belum |

---

**FASE 1 — Core Foundation** ✅ *Selesai*
- Core, config, orchestrator
- Thinking mode hard-disabled total (bug closing-tag qwen3.5:4b)

**FASE 2 — Personality Dasar** ✅ *Selesai*
- Base character Megumi (riset kanon: kind, non-confrontational, tsukkomi humor)
- Few-shot turn-based, mix bahasa, anti-fabrikasi data

**FASE 2B — Standar Kualitas Kode & Logging** ✅ *Selesai*

**FASE 3 — Memory System** ✅ *Selesai*
- SQLite WAL (`memories`, `activity_log`, `chat_history`) + sliding window
- Keyword extraction, category enum, `reset_all()`

**FASE 4 — Tools Tier 1** ✅ *Selesai*
- `time_tools.py`, `web_search_tools.py`, tool-calling loop native, `ChatResponse`
- **Bug #1 RESOLVED**: `get_current_time` → `TimeCache` ambient + `verify_exact_system_clock` on-demand
- **Bug #2 RESOLVED**: anti-fabrikasi bertahan di bawah tekanan multi-turn
- `save_memory`/`recall_memory` tervalidasi aktif dari obrolan natural
- **Batasan diketahui**: `recall_memory` gagal lintas bahasa (`"belajar"` ≠ `"learning"`) — ditunda ke embedding search (Parking Lot)

**FASE 5 — Tools Tier 2 (Desktop Agent)** ✅ *Selesai*
- `get_weather` (wttr.in), `read_web_page` (BeautifulSoup, fallback otomatis ke `web_search` saat 403 Cloudflare — **emergent behavior**, bukan hard-coded)
- `manage_local_file` (CRUD sandboxed di `D:\Megumi Kato`, whitelist `.txt/.md/.pdf`), `manage_application` (buka/tutup app + blocklist proses kritis), `get_system_status`
- 29/29 unit test passed
- Bug ditemukan & fix: penolakan buat PDF, halusinasi update file tanpa tool call, halusinasi tutup aplikasi, multi-file delete gagal parse

**FASE 5.1 — Inspection Tools & Context Anchoring Fix** ✅ *Selesai*
- `scan_workspace`, `list_running_applications` (support multi-filter koma) — 34/34 unit test passed
- **Bug ditemukan**: Context Anchoring Bias — model menolak verifikasi ulang status file/app kalau jawaban serupa sudah ada di `chat_history`, bahkan di sesi baru sekalipun
- **Root cause**: instruksi deklaratif kalah kuat lawan pattern-matching "saya sudah pernah jawab ini" yang terlihat langsung di history — bukan soal kurang tegas instruksinya
- **Fix final**: konsolidasi 8 `hard_rules` redundan (soal file/app) jadi 2 baris padat + tambahan eksplisit *"even if already answered earlier, always re-verify with a fresh tool call"*
- **Temuan sampingan**: karakter sempat "keluar personality" pakai kata ganti "gue" — sudah di-fix di `speaking_style`
- **Optimasi**: `base_character.yaml` dirampingkan dari 15 → 8 `hard_rules` unik
- ⏳ **Belum dikonfirmasi**: re-test skenario Log 1/Log 2 dengan `base_character.yaml` versi final, tanpa `/clear` manual

**FASE 6 — Mood/Love Meter System** 🔶 *Implementasi selesai, testing berjalan*
- `mood_log` table (append-only), `MoodManager` (score calc + time decay menuju netral, bukan menuju 0)
- Tool `adjust_mood` (5 event type: praised, nice_conversation, shared_something_personal, wrong_name_used, dismissed_or_ignored)
- 5 state label: very_warm/warm/neutral/distant/cold, ambient-injected ke context tiap turn (skip inject kalau netral, hemat token)
- State-tracking murni (bukan RL) — keputusan final dari diskusi sebelumnya
- **Bug ditemukan & fix**: karakter `:` di dalam string tanpa quote yang benar di `base_character.yaml` menyebabkan seluruh file gagal parse — **silent failure**, aplikasi tidak crash tapi diam-diam fallback ke `FALLBACK_SYSTEM_PROMPT` generik. Terdeteksi lewat unit test (`test_personality_builder.py`), bukan dari behavior runtime.
- **Peringatan aktif**: `wrong_name_used` berisiko ter-trigger berlebihan selama testing (riwayat testing project banyak menguji skenario nama salah) — perlu `/reset` sebelum pemakaian harian sungguhan
- ⏳ **Belum dikonfirmasi**: hasil testing live (Grup 1-8: baseline, trigger positif/negatif, tone shift, non-trigger check, decay, edge case ambigu)

**Tambahan infrastruktur (di luar fase resmi):**
- `core/command_handler.py` — CLI system commands terpisah dari orchestrator (SRP): `/clear` (wipe short-term + chat_history), `/reset` (full database wipe termasuk `mood_log`), `/help`, `/quit`

**FASE 7 — Voice Output** (text-in → voice-out)
- GPT-SoVITS, voice mode = selalu full English (keputusan desain — mismatch budaya komunikasi personality Megumi kalau berbahasa Indonesia)
- Strategi ekstraksi data kanon: sampling S1 (baseline speaking pattern) + target spesifik S2/Movie (momen emotional_depth) + LN versi Inggris untuk Fase 8 — bukan konsumsi penuh 25 episode/13 volume

**FASE 8 — Deep Personality Polish**
- Perbaiki kesalahan fakta umum (contoh: atribusi lagu salah)
- Tuning konsistensi follow-up response
- Kurasi manual 15-30 momen dari LN (via triase ringkasan volume dulu, bukan baca linear) untuk perkaya few-shot & emotional_depth

**FASE 9 — Voice Input** (STT + VAD)

**FASE 10 — Visual Character Live2D + Proactive Loop Dasar**
- `see-through` + `Anime2.5DRig`, scheduler sederhana → `trigger_reason`
- Interruption budget + quiet hours, journal proaktif, `OLLAMA_KEEP_ALIVE=-1`

**FASE 11 — Native Android App**
- Chibi/sprite → Live2D Android SDK, integrasi OPPO Band

**FASE 12 — Ekosistem Lanjutan**
- Server API, IoT, home server, LINE bot

---

## PARKING LOT

**Kelompok A — Prasyarat Fase 10/11**
- Vision, curfew system, confirmation-gate-enforced-in-code (referensi OpenWatari)
- Knowledge Base RAG + upgrade `memories` ke embedding search (prioritas naik)
- IoT sensor integration

**Kelompok B — Opsional**: LINE bot, email AI, engineering/career mode

**Kelompok C — Eksperimen Terpisah**: RL untuk mood (ditolak, final: state-tracking), server API multi-device

**Kelompok D — Multi-Agent Era** (~32B+): Agent Analis asynchronous, reversible-only git, upgrade model utama

**Kelompok E — Catatan Desain**: L2/L4 memory (OpenWatari), eksplainability advantage, TTFT metrik krusial voice

**Kelompok F — Psychological Layer (visi jangka panjang)**: axis tambahan di luar mood (misal `relationship` — tren jangka panjang, beda dari mood harian) sebagai modul independen terpisah, pola komputasi sama (state-tracking, bukan LLM "merasakan"). Bukan sistem emosi multi-dimensi kompleks dari awal — ekspansi hanya kalau terbukti perlu dari pemakaian nyata mood 1-axis yang sudah ada.

---

## Keputusan Arsitektur Kunci (jangan diubah tanpa alasan kuat)

- **100% lokal, zero budget** — no cloud API, no VPS
- **Modular, config-driven, dependency injection** di semua layer
- **Native tool-calling, tanpa LangChain/LangGraph** — kontrol penuh, transparansi debugging
- **Hal yang bisa dihitung statistik/SQL, jangan dibebankan ke LLM** — prinsip konsisten dipakai di: mood system, curfew verification, deteksi pola aktivitas
- **Thinking mode permanen off** — bug model-level, bukan sesuatu yang bisa diperbaiki dari prompt
- **Perilaku baru butuh contoh konkret (few-shot), bukan cuma instruksi deklaratif** — pola berulang terbukti sejak Fase 2 (bug nama) sampai Fase 5.1 (context anchoring): model 4B lebih patuh ke demonstrasi nyata daripada penumpukan `hard_rules` teks
