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
| 5.1 — Inspection Tools & Context Anchoring Fix | ✅ Selesai |
| 6 — Mood/Love Meter System | ✅ Selesai |
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
- **Batasan diketahui**: gap semantik 1-bahasa (`"pemrograman"` ≠ `"python"`)

**FASE 4 — Tools Tier 1** ✅ *Selesai*
- `time_tools.py`, `web_search_tools.py`, tool-calling loop native, `ChatResponse`
- **Bug #1 RESOLVED**: `get_current_time` → `TimeCache` ambient + `verify_exact_system_clock`
- **Bug #2 RESOLVED**: anti-fabrikasi bertahan di bawah tekanan multi-turn
- **Batasan diketahui**: `recall_memory` gagal lintas bahasa (`"belajar"` ≠ `"learning"`) — ditunda ke embedding search

**FASE 5 — Tools Tier 2 (Desktop Agent)** ✅ *Selesai*
- `get_weather`, `read_web_page` (fallback otomatis ke `web_search` saat 403 — emergent behavior)
- `manage_local_file` (sandboxed CRUD), `manage_application`, `get_system_status`
- 29/29 unit test passed

**FASE 5.1 — Inspection Tools & Context Anchoring Fix** ✅ *Selesai*
- `scan_workspace`, `list_running_applications` — 34/34 unit test passed
- Context Anchoring Bias ditemukan & fix final diterapkan (konsolidasi hard_rules + "always re-verify")

**FASE 6 — Mood/Love Meter System** ✅ *Selesai*
- `mood_log`, `MoodManager` (score + decay ke netral), tool `adjust_mood`, 5 state label
- **Bug ditemukan #1**: karakter `:` tanpa quote di YAML → silent fail ke fallback prompt
- **Bug ditemukan #2 (MAJOR)**: `hard_rules: >` (block scalar) di YAML membuat Python mem-parsing `hard_rules` sebagai **string tunggal**, bukan list. Fungsi `fmt_list()` lalu meng-iterasi string itu **per karakter**, menghasilkan ratusan baris sampah (`- N`, `- e`, `- v`, dst) yang membanjiri system prompt dengan noise, menyebabkan **Identity Collapse total** (model mengaku sebagai "Qwen3.5 by Tongyi Lab", bukan Megumi)
- **Root cause resmi bukan** "context overflow" atau "attention dilution dari 12 tools" — sempat dicurigai lewat laporan awal, tapi **terbukti keliru** setelah cek raw payload langsung
- **Fix**: `hard_rules` diubah ke native YAML list, `fmt_list()` diberi guard clause defensif (auto-detect kalau menerima string, warning + auto-recover)
- **History pollution**: respons robotic akibat bug ini sempat tersimpan ke `chat_history`, memperparah masalah lewat in-context learning di turn berikutnya — diselesaikan via `/reset`
- ⏳ **WAJIB**: ulangi seluruh Grup 1-8 testing mood dari awal — testing sebelumnya tercemar bug ini, hasilnya tidak representatif

**Tambahan infrastruktur**: `core/command_handler.py` — `/clear`, `/reset` (termasuk `mood_log`), `/help`, `/quit`

**FASE 7 — Voice Output** (text-in → voice-out)
- GPT-SoVITS, voice mode = selalu full English
- Ekstraksi data kanon: sampling S1 + target S2/Movie + LN (Inggris)

**FASE 8 — Deep Personality Polish**
- Kurasi manual 15-30 momen LN via triase ringkasan volume dulu

**FASE 9 — Voice Input** (STT + VAD)

**FASE 10 — Visual Character Live2D + Proactive Loop Dasar**
- `see-through` + `Anime2.5DRig`, scheduler → `trigger_reason`
- Interruption budget + quiet hours, `OLLAMA_KEEP_ALIVE=-1`

**FASE 10.1 — Vision & Screen Awareness** *(BARU)*
- Webcam presence/motion detection (YOLO nano, CPU-only)
- Screenshot-based screen reading (on-demand/interval, bukan continuous)
- Prasyarat untuk: curfew verification, Fase 13

**FASE 11 — Native Android App**
- Chibi/sprite → Live2D Android SDK, integrasi OPPO Band

**FASE 12 — Ekosistem Lanjutan**
- Server API, IoT, home server, LINE bot

**FASE 13 — Autonomous Browser Exploration** *(BARU)*
- Playwright automation + vision-based decision making (bergantung Fase 10.1)
- **WAJIB** confirmation-gate-enforced-in-code sebelum fase ini mulai — fitur paling invasif yang pernah direncanakan
- Browser profile terpisah/sandboxed, bukan browser harian
- Koreksi konsep awal: Windows tidak mendukung 2 cursor independen — kalau butuh visual "cursor AI", itu simulasi overlay, bukan cursor fungsional kedua

---

## PARKING LOT

- **Kelompok A**: curfew system, confirmation-gate-enforced-in-code, Knowledge Base RAG + upgrade `memories` ke embedding search, IoT sensor
- **Kelompok B**: LINE bot, email AI, engineering/career mode
- **Kelompok C**: RL untuk mood (ditolak), server API multi-device
- **Kelompok D**: Agent Analis asynchronous (~32B+), reversible-only git
- **Kelompok E**: L2/L4 memory (OpenWatari), eksplainability advantage, TTFT metrik
- **Kelompok F**: Psychological layer tambahan (axis `relationship`, dll) — modul independen, bukan sistem emosi kompleks dari awal

---

## LOG PROBLEM & RESOLUSI (Referensi Debugging)

| # | Fase | Problem | Root Cause Sebenarnya | Status |
|---|---|---|---|---|
| 1 | 2 | Bug salah nama, AI klaim namanya salah padahal benar | Few-shot tanpa contoh kontras (nama benar vs salah) | ✅ Fixed |
| 2 | 2 | Personality "Bluntly Honest" terlalu kritis, tidak sesuai kanon | Draft awal tidak diriset dari sumber kanon | ✅ Fixed |
| 3 | 3 | `recall_memory` nyaris tidak pernah match | Search pakai kalimat mentah utuh, bukan keyword terekstrak | ✅ Fixed (keyword extraction) |
| 4 | 4 | `get_current_time` dipanggil tapi respons `"Jam segini."` tanpa angka | Tool-call round-trip celah + hard_rules kurang eksplisit | ✅ Fixed (TimeCache + instruksi) |
| 5 | 4 | Fabrikasi detail berita palsu tanpa tool call | Anti-fabrikasi runtuh di bawah tekanan sosial multi-turn | ✅ Fixed (hard_rules diperkuat + few-shot) |
| 6 | 4 | Heuristik thinking-mode tidak konsisten | Thinking mode punya bug closing-tag di model — **thinking dihapus total**, bukan diperbaiki | ✅ Resolved (permanent off) |
| 7 | 5 | Model tolak buat PDF, halusinasi update/delete file & close app | Deskripsi skema kurang eksplisit/tegas | ✅ Fixed |
| 8 | 5.1 | Context Anchoring Bias — model percaya klaim palsu dari history sendiri | Instruksi deklaratif kalah kuat vs pattern-matching history nyata | ✅ Fixed (konsolidasi rules + "always re-verify") |
| 9 | 6 | Silent fail ke fallback prompt | Karakter `:` tanpa quote di YAML | ✅ Fixed |
| 10 | 6 | **Identity Collapse total** — AI mengaku Qwen3.5, bukan Megumi | `hard_rules: >` (block scalar) di-parse jadi string, `fmt_list()` iterasi per-karakter, system prompt penuh noise sampah | ✅ Fixed (native list + guard clause) |
| 11 | 6 | (Sempat dicurigai) "context overflow dari 12 tools" | **Diagnosis awal SALAH** — root cause asli adalah #10, bukan jumlah tools. Diketahui lewat cek raw payload, bukan asumsi | ✅ Diklarifikasi |

**Pelajaran pola berulang (masuk ke Keputusan Arsitektur Kunci):**
- Kesalahan sintaks YAML kecil (poin #9, #10) berulang kali menyebabkan gejala yang *terlihat* seperti masalah AI kompleks — **selalu cek raw payload/log mentah dulu** sebelum menyimpulkan "keterbatasan model" atau redesain arsitektur besar
- Perilaku baru butuh **contoh konkret (few-shot)**, bukan cuma instruksi deklaratif — terbukti sejak poin #1 sampai #8
- **Ablation test** (matikan 1 variabel, tes ulang) adalah cara tercepat mengisolasi root cause vs korelasi kebetulan (terbukti krusial di poin #11)

---

## Keputusan Arsitektur Kunci (jangan diubah tanpa alasan kuat)

- **100% lokal, zero budget** — no cloud API, no VPS
- **Modular, config-driven, dependency injection** di semua layer
- **Native tool-calling, tanpa LangChain/LangGraph** — kontrol penuh, transparansi debugging
- **Hal yang bisa dihitung statistik/SQL, jangan dibebankan ke LLM** — prinsip konsisten dipakai di: mood system, curfew verification, deteksi pola aktivitas
- **Thinking mode permanen off** — bug model-level, bukan sesuatu yang bisa diperbaiki dari prompt
- **Perilaku baru butuh contoh konkret (few-shot), bukan cuma instruksi deklaratif** — pola berulang terbukti sejak Fase 2 (bug nama) sampai Fase 5.1 (context anchoring): model 4B lebih patuh ke demonstrasi nyata daripada penumpukan `hard_rules` teks
