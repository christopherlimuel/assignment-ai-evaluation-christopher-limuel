"""
Modul Tools — fungsi-fungsi "aksi" yang dipanggil router ketika intent
BUKAN pertanyaan informasi/kebijakan, melainkan permintaan spesifik
yang butuh pengecekan data langsung (bukan retrieval semantik).

Pola ini mengikuti konsep Tool Integration di Sesi 12.3.
"""

import pandas as pd
import re

MOCK_TICKETS_PATH = "data/mock_tickets.csv"

def extract_ticket_id(query: str) -> str:
    """
    # Format ticket_id pada mock_tickets.csv adalah 'TICKET-XXXX'.

    # Contoh format yang diterima oleh regex:
        1. TICKET-1234              (Huruf kapital dengan pemisah tanda hubung) 
        2. ticket_5678              (Huruf kecil atau dengan pemisah garis bawah)
        3. TICKET 9999              (Huruf kapital atau dengan pemisah spasi)
    # Contoh format yang ditolak oleh regex:
        1. ticket-abcd              (Gagal karena XXXX berisi huruf, bukan angka)
        2. TICKET-123               (Gagal karena angka kurang dari 4 digit)
        3. TIKET-1234               (TIKET bukan TICKET dan typo lainnya)
        4. TICKET dengan kode 1234  (TICKET dengan kode digit terpisah oleh)
    """
    ticket_ids = re.findall(r"\bTICKET[-_ ](\d{4})\b", query, re.IGNORECASE)
    if not ticket_ids:
        return "NOT FOUND"
    return f"TICKET-{ticket_ids[-1]}"

def get_ticket_status(ticket_id: str) -> list:
    """
    Mencari status tiket berdasarkan ticket_id pada data mock_tickets.csv.
    """
    ticket_df = pd.read_csv(MOCK_TICKETS_PATH)
    found_ticket_df = ticket_df.loc[ticket_df['ticket_id'] == ticket_id]
    result = []

    for _, found_ticket in found_ticket_df.iterrows():
        result.append(found_ticket.to_dict())   # (ticket_id, employee_name, category, subject, status, last_update)
    return result
