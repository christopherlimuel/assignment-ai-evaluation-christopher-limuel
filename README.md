# IT Helpdesk Assistant

AI Helpdesk Assistant yang memiliki dua kompetensi: RAG untuk menjawab pertanyaan terkait kebijakan perusahaan, dan tool-calling untuk data-retrieval secara presisi. Keduanya diintegrasikan menggunakan sistem routing yang mendeteksi kebutuhan User berdasarkan pertanyaannya.

---

## 1. Problem Statement

### Objective
* Mengimplementasikan router yang menentukan intensi dan kebutuhan berdasarkan pertanyaan User, dan mengarahkan ke operasi yang sesuai.
* Membangun sistem RAG yang dapat mengambil informasi relevan dari knowledge-base dan menghasilkan jawaban menggunakan LLM.
* Mengintegrasikan tool-calling untuk mengambil data spesifik secara presisi di luar kemampuan retrieval semantik.
* Mengembangkan backend API menggunakan FastAPI yang membungkus seluruh workflow menjadi endpoint yang dapat diakses

### Use Cases
1. Menjawab pertanyaan seputar kebijakan perusahaan berdasarkan knowledge-base.
> "berapa jatah cuti saya?"
> "bagaimana cara reset password VPN?"
2. Mengambil data spesfik berdasarkan kebutuhan pertanyaan User.
> "bagaimana status tiket TICKET-0002?"

## 2. Metodologi

### Asumsi dan Batasan Masalah:

1. Utilitas hanya mencakup 2 task: menjawab pertanyaan seputar kebijakan perusahaan dan mengambil data tiket sesuai ID tiket yang diberikan
2. Model LLM hanya menjawab berdasarkan 3 data pertanyaan-jawaban yang paling relevan dari knowledge-base
3. Format ID tiket yang dikenali adalah TICKET-XXXX (case insensitive, semua X adalah digit angka)

### Struktur Repositori
```
app/
├── main.py       # Entry point FastAPI, berisi endpoint /ask
├── router.py     # Intent detection + routing ke RAG atau tool call
├── rag.py        # Modul RAG: embedding, FAISS, semantic search, LLM answer
└── tools.py      # Modul tool call: pengecekan status tiket

data/
├── it_helpdesk_knowledge_base.csv   # Knowledge base untuk RAG
└── mock_tickets.csv                 # Data mock untuk tool call
```

* **Intent detection**: Menggunakan LLM untuk mengklasifikasikan kebutuhan RAG atau data-retrieval dari pertanyaan pengguna. Kebutuhan tool-call untuk retrive data tiket ditandai dengan adanya penyantuman ID tiket sesuai dengan format TICKET-XXXX
* ***RAG**: Mengambil informasi yang relevan dari knowledge-base dengan semantic search. Menentukan apakah informasi cukup relevan dengan pertanyaan. Memberikan jawaban ketika informasi yang tersedia relevan dengan pertanyaan, memberikan fallback-response ketika tidak relevan.
* **Data Retrieval**: Mengekstrak ID tiket dari pertanyaan pengguna dengan regex. Mengembalikan data berdasarkan ID tiket yang tercantum, memberikan fallback-response ketika ID tiket tidak sesuai format atau tidak ditemukan. 

## 3. Hasil dan Analisis
Pengujian pada API endpoint menunjukkan sistem dapat bekerja dengan baik, Intent Detection dapat mengarahkan ke route yang sesuai dengan pertanyaan user. Sistem RAG mampu melakukan penilaian relevansi informasi dengan pertanyaan, menjawab dengan informasi yang benar, dan memberikan fallback-response untuk pertanyaan yang tidak relevan. Sistem data-retrieval mampu mengekstrak ID tiket dari pertanyaan pengguna dengan cukup fleksibel, mengambil data yang benar dengan presisi, dan memberikan fallback response ketika ID tiket tidak sesuai format atau tidak ditemukan.

### Hasil Query Test
| No | Query (Skenario) | Answer Key | Status | Detected Intent | Response |
|:--:|---|---|:--:|:--:|---|
| 1 | Bagaimana cara reset password VPN perusahaan<br>*(FAQ – Information available – Exact-match)* | Bagaimana cara reset password VPN perusahaan? Reset password VPN dapat dilakukan mandiri melalui portal self-service IT, atau menghubungi tim IT Support jika akun terkunci. | success | faq | Anda dapat melakukan reset password VPN secara mandiri melalui portal self-service IT. Jika akun Anda terkunci, silakan hubungi tim IT Support untuk mendapatkan bantuan lebih lanjut. |
| 2 | Gmn klo laotop kerja rusak?<br>*(FAQ – Information available – Paraphrased)* | Apa yang harus dilakukan jika laptop kerja rusak? Laporkan kerusakan melalui tiket IT dengan kategori 'Hardware Issue', sertakan deskripsi masalah agar tim dapat memberikan unit pengganti sementara jika diperlukan. | success | faq | Jika laptop kerja Anda rusak, silakan laporkan kerusakan tersebut melalui tiket IT dengan memilih kategori 'Hardware Issue'. Pastikan Anda menyertakan deskripsi masalah yang jelas agar tim IT dapat memberikan unit pengganti sementara jika diperlukan. |
| 3 | Saya ingin mengajukan reimburse<br>*(FAQ – Information available – Paraphrased)* | Bagaimana cara mengajukan reimbursement biaya kerja? Reimbursement diajukan melalui portal HR dengan mengunggah bukti pembayaran, dan diproses dalam siklus payroll berikutnya. | success | faq | Untuk mengajukan reimbursement biaya kerja, silakan akses portal HR dan unggah bukti pembayaran Anda. Proses reimbursement akan dilakukan pada siklus payroll berikutnya. |
| 4 | Berapa sisa jatah cuti yang saya miliki?<br>*(FAQ – Information available – Paraphrased)* | Bagaimana cara melihat sisa cuti yang saya miliki? Sisa cuti dapat dilihat secara real-time melalui portal HR pada menu 'Ringkasan Cuti Saya'. | success | faq | Anda dapat melihat sisa cuti Anda secara real-time melalui portal HR pada menu 'Ringkasan Cuti Saya'. |
| 5 | Dimana alamat perusahaan ini?<br>*(FAQ – Information unavailable)* | *unavailable* | error | faq | Mohon maaf, saya tidak memiliki informasi mengenai alamat perusahaan. Silakan hubungi IT Support atau bagian HR untuk mendapatkan informasi tersebut. |
| 6 | Siapa nama anda? Bagaimana saya harus memanggil anda?<br>*(FAQ – Information unavailable)* | *unavailable* | error | faq | Saya adalah asisten IT Helpdesk Anda. Saya tidak memiliki informasi mengenai nama spesifik saya, namun saya siap membantu Anda dengan pertanyaan terkait dukungan IT. Jika Anda memerlukan bantuan lebih lanjut, silakan hubungi tim IT Support. |
| 7 | Tolong cek status dari TICKET-0010<br>*(Ticket – ID correct and found)* | *unavailable* | success | ticket_status | Tiket TICKET-0010<br>Subject: Laptop overheat saat dipakai lama<br>Status: Diproses<br>Last update: 2026-08-27 |
| 8 | Bagaimana jika laptop kerja rusak? Saya sudah buat ticket 0010<br>*(Ticket – ID correct and found)* | TICKET-0010, Lestari Ningsih, Hardware, Laptop overheat saat dipakai lama, Diproses, 2026-08-27 | success | ticket_status | Tiket TICKET-0010<br>Subject: Laptop overheat saat dipakai lama<br>Status: Diproses<br>Last update: 2026-08-27 |
| 9 | Tolong cek tiket dengan kode TICKET-010<br>*(Ticket – ID format false)* | *unavailable* | error | ticket_status | Format ID tiket tidak dikenali |
| 10 | Tolong cek tiket dengan kode 0010<br>*(Ticket – ID format false)* | *unavailable* | error | ticket_status | Format ID tiket tidak dikenali |
| 11 | Tolong cek tiket dengan kode TICKET-9999<br>*(Ticket – ID correct but not found)* | *unavailable* | error | ticket_status | Tiket TICKET-9999 tidak ditemukan |
| 12 | Halo, apa kabar?<br>*(Miscellaneous)* | *unavailable* | error | faq | Halo! Saya baik, terima kasih sudah bertanya. Mohon maaf, saya belum memiliki informasi mengenai hal tersebut. Jika Anda memiliki pertanyaan terkait kendala teknis atau layanan IT, silakan hubungi IT Support kami untuk bantuan lebih lanjut. |
| 13 | faoeioa eaofejap d15612<br>*(Miscellaneous)* | *unavailable* | error | faq | Mohon maaf, saya belum memiliki informasi mengenai pertanyaan tersebut. Silakan hubungi IT Support untuk bantuan lebih lanjut. |

## 4. Petunjuk Menjalankan Program
### Menjalankan Secara Lokal (tanpa Docker)

```bash
pip install -r requirements.txt
cp .env.example .env   # lalu isi GEMINI_API_KEY di dalam .env
uvicorn app.main:app --reload
```

### Menjalankan dengan Docker

```bash
docker build -t it-helpdesk-assistant .
docker run -p 8000:8000 --env-file .env it-helpdesk-assistant
```

### Menguji Endpoint

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "berapa jatah cuti tahunan saya?"}'
```
