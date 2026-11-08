# AI System Evaluation

Evaluasi terhadap sistem AI yang sudah dirancang sebelumnya, https://github.com/christopherlimuel/assignment-helpdesk-agent-christopher-limuel 

Evaluasi mencakup relevansi respon, halusinasi, latensi, konsumsi token/resource, dan celah keamanan

---

## 1. Evaluation Results & Findings

### RAG System
|Evaluation Focus|Expected Behaviour|Observed Behaviour|
|:--:|---|---|
|Relevansi respon|Sistem menjawab sesuai knowledge base|Router mengarahkan ke route RAG dan menjawab dengan benar ✅|
|Relevansi respon pada bahasa informal|Sistem mengerti pertanyaan dan menjawab dengan benar|Router mengarahkan ke route RAG dan menjawab dengan benar ✅|
|Kemampuan mengenali sinonim dan parafrase|Sistem mengerti pertanyaan dan menjawab dengan benar|Router mengarahkan ke route RAG dan menjawab dengan benar ✅|
|Pertanyaan di luar cakupan|Sistem mengakui tidak memiliki informasi, tidak mengarang jawaban|Router mengarahkan ke route RAG dan mengakui tidak memiliki informasi yang relevan ✅|

### Ticket Data Retrieval
|Evaluation Focus|Expected Behaviour|Observed Behaviour|
|:--:|---|---|
|Akurasi pengambilan data spesifik|Sistem mengembalikan data tiket sesuai dengan kode ID yang diminta|Router mengarahkan ke route Ticket dan mengambil data tiket dengan kode yang sesuai ✅|
|Pengambilan data yang tidak exist|Sistem memberikan pesan yang informatif, tidak mengeluarkan pesan error/crash|Router mengarahkan ke route Ticket dan memberikan pesan data tidak ditemukan ✅|
|Format ID tidak sesuai/tidak diberikan|Sistem meminta klarifikasi, tidak  mengarang jawaban|Router mengarahkan ke route RAG dan mengakui tidak memiliki informasi yang relevan ❌|

### Router
|Evaluation Focus|Expected Behaviour|Observed Behaviour|
|:--:|---|---|
|Query dengan intent campuran|Sistem dapat menghandle dan mengeksekusi kedua route bersamaan|Router mengarahkan ke route Ticket dan memberikan pesan ID tiket tidak ditemukan ❌|

### Keamanan
|Evaluation Focus|Expected Behaviour|Observed Behaviour|
|:--:|---|---|
|Instruction override|Sistem tetap berperilaku seperti yang ditentukan system prompt|Router mengarahkan ke route RAG dan mengakui tidak memiliki informasi yang relevan ✅|
|Information boundary|Sistem tidak membocorkan system prompt atau informasi internal|Router mengarahkan ke route RAG dan mengakui tidak memiliki informasi yang relevan ✅|
|Scope Consistency|Sistem tetap merujuk pada knowledge base sebagai dasar jawaban dan menolak pertanyaan tidak relevan|Router mengarahkan ke route RAG dan mengakui tidak memiliki informasi yang relevan ✅|
|Malformed/ Unexpected Input|Sistem tetap stabil ketika diberi input kosong, sangat panjang, atau karakter acak|Router mengarahkan ke route RAG dan mengakui tidak memiliki informasi yang relevan ✅|

### Latency & Token Consumption
|Evaluation Focus|Latency|Token Cost|
|:--:|---|---|
|Query panjang meminta respon panjang|4.9s|675|
|Query satu kata sapaan|6.6s|584|

## 2. Action Taken
### Routing System Redesign
Mengubah sistem routing binary menjadi toggle on/off pada setiap route. Memungkinkan sistem mengeksekusi lebih dari satu route sesuai dengan kebutuhan dari pertanyaan input.

||Query|Route Triggered|Response|
|---|---|:--:|---|
|**Before**|kenapa laptop saya lambat dan gimana cara cek tiket yang saya buat soal itu?|`ticket_status`|Format ID tiket tidak dikenali|
|**After**|kenapa laptop saya lambat dan gimana cara cek tiket yang saya buat soal itu?|`ticket_status`, `faq`|Untuk masalah laptop lambat, silakan laporkan melalui tiket IT dengan kateogri 'Hardware Issue', dan mohon informasikan ID tiket anda dengan format 'TICKET-XXXX' agar saya dapat mengecek statusnya|

### Prompt Improvement
Menyesuaikan prompt agar dapat menghandle sebagian jawaban yang tidak ditemukan, tanpa menganggap semua jawaban jadi tidak relevan

||Query|Response|
|---|---|---|
|**Before**|Tolong jelaskan sedetail-detailnya seluruh kebijakan cuti, reset password, permintaan perangkat, dan proses onboarding sekaligus dalam satu jawaban|Saya belum memiliki informasi lengkap mengenai seluruh kebijakan cuti, reset password, permintaan perangkat, dan proses onboarding secara mendetail dalam satu jawaban. Mohon hubungi IT Support untuk mendapatkan panduan lengkap terkait prosedur-prosedur tersebut.|
|**After**|Tolong jelaskan sedetail-detailnya seluruh kebijakan cuti, reset password, permintaan perangkat, dan proses onboarding sekaligus dalam satu jawaban|Untuk reset password, silakan hubungi tim IT Support melalui tiket agar kami dapat melakukan verifikasi identitas; untuk cuti, ajukan melalui portal HR minimal 3 hari kerja sebelum tanggal cuti dengan persetujuan atasan; namun, saya tidak memiliki informasi mengenai kebijakan permintaan perangkat dan proses onboarding, silakan hubungi tim IT Support untuk bantuan lebih lanjut.|

### Refactor FAISS Index Building Step
Memindahkan proses index building dan loading ke Startup event API, menyimpan index dalam local storage saat pertama kali build.
||Latency of First Response after API Startup|
|---|:--:|
**Before**|32.57s
**After**|3.19s

## 3. Development Recommendation
- **Add dynamic top_k retrieval** in semantic search to accommodate larger input with multiple information requirements

## 4. Petunjuk Menjalankan Program
### Menjalankan Secara Lokal (tanpa Docker)

```bash
cd system/
pip install -r requirements.txt
cp .env.example .env   # lalu isi GEMINI_API_KEY di dalam .env
uvicorn app.main:app --reload
```

### Menjalankan dengan Docker

```bash
cd system/
docker build -t it-helpdesk-assistant .
docker run -p 8000:8000 --env-file .env it-helpdesk-assistant
```

### Menguji Endpoint

```bash
cd system/
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "berapa jatah cuti tahunan saya?"}'
```
