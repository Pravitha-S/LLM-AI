"""
RAG Pipeline using pure numpy — no C++ build tools needed!
Run once: python -c "from rag.ingest import ingest_all; ingest_all()"
"""

import os
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

_embedder = None
_chunks = []
_index = None

VECTOR_PATH = "rag/vectors.pkl"

def get_embedder():
    global _embedder
    if _embedder is None:
        print("Loading embedding model (first time only)...")
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder

HOSPITAL_KNOWLEDGE = """
HOSPITAL OVERVIEW
District General Hospital Kasaragod is a government hospital under Kerala Health and Family Welfare Department.
Established in 1962. NABH accredited. Located at Medical College Road, Kasaragod, Kerala 671122.
Phone: 04994-220330. Email: dghkasaragod@kerala.gov.in. Total beds: 500 plus. Specialist doctors: 80 plus.

OPD SERVICES AND TIMINGS
OPD runs Monday to Saturday from 8:00 AM to 1:00 PM.
Patients must collect token from OPD counter between 8AM and 11AM.
Online token booking available. Token collection is free for all patients.
Departments: General Medicine, Cardiology, Orthopaedics, Gynaecology, Paediatrics, ENT, Surgery, Dermatology, Neurology, Ophthalmology.

EMERGENCY SERVICES
Emergency department is open 24 hours 7 days a week including holidays.
Ambulance service: Call 108 free or 102. Trauma care unit available.
ICU has 30 beds. Emergency contact: 04994-220332.

PHARMACY
Hospital pharmacy provides free medicines under government schemes.
Pharmacy timings: 8AM to 8PM daily. Emergency pharmacy available 24 hours.
Free medicines for Karuna Health Scheme, Arogyakeralam, JSSK, and BPL patients.

DIAGNOSTICS AND LAB
Laboratory: blood tests, urine analysis, stool examination available.
Radiology: Digital X-Ray, Ultrasound, CT Scan, MRI available.
Cardiology diagnostics: ECG, Echocardiogram, Stress Test.
Lab timings: 8AM to 5PM. Reports same day for routine tests.
Subsidised rates for government scheme holders.

MOTHER AND CHILD HEALTH
Maternity ward with 50 beds. Free delivery under JSSK scheme.
NICU with 15 beds. Antenatal clinic every Monday and Thursday 9AM to 12PM.
Immunisation clinic every Tuesday 9AM to 12PM. Completely free.

BLOOD BANK
Blood bank operates 24 hours 7 days. All blood groups available.
Blood bank contact: 04994-220331. Free for BPL and scheme beneficiaries.

GOVERNMENT SCHEMES
1. Karuna Health Scheme: Free treatment for BPL families.
2. Arogyakeralam: Cashless treatment up to 3 lakhs per year.
3. Ayushman Bharat PMJAY: Up to 5 lakhs coverage per family per year.
4. JSSK: Free maternity and newborn services.
All scheme holders get free medicines free diagnostics free surgery.

TOKEN AND APPOINTMENT SYSTEM
Token format is KSD followed by 4 digits. Example: KSD2045.
To check token status ask the chatbot with your token number.
Tokens available Monday to Saturday 8AM to 11AM at OPD counter.

DOCTORS SCHEDULE
Dr. Rajesh Kumar M - General Medicine - Monday Wednesday Friday - 9AM to 1PM - Room A3
Dr. Priya Nair - Cardiology - Tuesday Thursday Saturday - 10AM to 1PM - Cardiology Wing Room 1
Dr. Mohammed Aslam K - Orthopaedics - Monday to Saturday - 9AM to 12PM - Room B7
Dr. Sindhu Varma - Gynaecology - Monday Wednesday Friday - 9AM to 1PM - Womens Wing Room 2
Dr. Arun Krishnan - Paediatrics - Monday to Saturday - 9AM to 1PM - Childrens Ward Room 1
Dr. Fathima Beevi - ENT - Tuesday Thursday - 10AM to 12PM - Room A5
Dr. Suresh Babu T - General Surgery - Monday Wednesday Friday - 9AM to 11AM - Surgical Wing Room 4
Dr. Lakshmi Devi - Dermatology - Tuesday Saturday - 10AM to 1PM - Room C2
Dr. Anwar Sadath - Neurology - Wednesday Saturday - 9AM to 12PM - Neurology Wing Room 1
Dr. Meena Kumari - Ophthalmology - Monday to Friday - 9AM to 1PM - Eye Care Centre

FREQUENTLY ASKED QUESTIONS
Is treatment free: Yes consultation is free. Medicines and tests are free for scheme holders.
How to get token: Visit OPD counter between 8AM and 11AM or book online. Token is free.
Documents needed: Aadhaar card and ration card for scheme benefits.
Sunday hours: OPD closed Sundays. Emergency services 24 hours 7 days.
How to reach: Medical College Road Kasaragod near Kasaragod Bus Stand.

CONTACT INFORMATION
Main Reception: 04994-220330
Emergency: 108 or 04994-220332
Blood Bank: 04994-220331
Email: dghkasaragod@kerala.gov.in
Address: Medical College Road Kasaragod Kerala 671122
"""

def chunk_text(text, chunk_size=150, overlap=20):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def ingest_all():
    global _chunks, _index
    print("Starting ingestion...")
    embedder = get_embedder()
    all_chunks = chunk_text(HOSPITAL_KNOWLEDGE, chunk_size=80, overlap=15)

    try:
        import csv
        csv_path = os.path.join(os.path.dirname(__file__), '../../documents/doctor_schedule.csv')
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            csv_text = "Doctor Schedule:\n"
            for row in reader:
                csv_text += f"Doctor {row.get('Doctor Name','')} Department {row.get('Department','')} Days {row.get('Days','')} Timings {row.get('Timings','')} Room {row.get('Room','')}\n"
        all_chunks.extend(chunk_text(csv_text, chunk_size=100))
        print("CSV loaded!")
    except Exception as e:
        print(f"CSV skipped: {e}")
    # Load PDFs
    try:
        import PyPDF2
        docs_path = os.path.join(os.path.dirname(__file__), '../../documents')
        for filename in os.listdir(docs_path):
            if filename.endswith('.pdf'):
                with open(os.path.join(docs_path, filename), 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = " ".join(page.extract_text() for page in reader.pages)
                    all_chunks.extend(chunk_text(text, chunk_size=80, overlap=15))
                    print(f"PDF loaded: {filename}")
    except Exception as e:
        print(f"PDF skipped: {e}")

    # Load TXT files
    try:
        docs_path = os.path.join(os.path.dirname(__file__), '../../documents')
        for filename in os.listdir(docs_path):
            if filename.endswith('.txt'):
                with open(os.path.join(docs_path, filename), 'r', encoding='utf-8') as f:
                    text = f.read()
                    all_chunks.extend(chunk_text(text, chunk_size=80, overlap=15))
                    print(f"TXT loaded: {filename}")
    except Exception as e:
        print(f"TXT skipped: {e}")

    print(f"Total chunks: {len(all_chunks)}")
    print("Generating embeddings...")
    embeddings = embedder.encode(all_chunks, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype='float32')
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    os.makedirs(os.path.dirname(VECTOR_PATH) if os.path.dirname(VECTOR_PATH) else '.', exist_ok=True)
    with open(VECTOR_PATH, 'wb') as f:
        pickle.dump({'embeddings': embeddings, 'chunks': all_chunks}, f)

    _chunks = all_chunks
    _index = embeddings
    print(f"Saved {len(all_chunks)} chunks to {VECTOR_PATH}")

def load_index():
    global _chunks, _index
    if _index is None:
        if os.path.exists(VECTOR_PATH):
            with open(VECTOR_PATH, 'rb') as f:
                data = pickle.load(f)
            _chunks = data['chunks']
            _index = data['embeddings']
        else:
            print("Index not found, running ingestion...")
            ingest_all()

def retrieve(query, top_k=3):
    try:
        load_index()
        embedder = get_embedder()
        query_emb = embedder.encode([query])
        query_emb = np.array(query_emb, dtype='float32')
        query_emb = query_emb / np.linalg.norm(query_emb)
        scores = np.dot(_index, query_emb.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [_chunks[i] for i in top_indices]
        return "\n\n---\n\n".join(results)
    except Exception as e:
        print(f"Retrieval error: {e}")
        return HOSPITAL_KNOWLEDGE[:2000]