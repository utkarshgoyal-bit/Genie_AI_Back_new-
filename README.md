🌱 Garden Genie Backend — Full Technical README (v4.2)

(The complete, detailed version)

This README is designed for engineers joining the team, auditors reviewing the system, senior developers planning refactors, and integrators maintaining or extending the backend.

It covers the entire system end-to-end, with full detail on workflows, internal logic, architecture, data flows, components, and constraints.

0. Executive Summary

Garden Genie is an AI-powered backend for diagnosing plant diseases from uploaded images, recommending treatments, and tracking user diagnosis history.

It integrates:

YOLOv8 → Plant detection and bounding boxes

GPT-4o / GPT-4 Vision + Text → Disease reasoning + diagnosis generation

PostgreSQL → Persistent storage of detections, OTPs, and product catalog

AWS S3 → Durable image storage

OTP authentication via E2A SMS

Fuzzy product recommendation using RapidFuzz and Excel-imported catalogs

FastAPI → API server, routing, background tasks

v4.2 introduces a file-reduced ‘domains-first’ architecture, simplifying routing, controllers, and glue code while leaving business logic unchanged.

1. High-Level Architecture
 ┌────────────────────────────────────────────┐
 │                 Mobile App                 │
 └───────────────────────┬────────────────────┘
                         │ HTTPS (JSON + multipart)
                         ▼
 ┌────────────────────────────────────────────┐
 │                 FastAPI API                │
 │  (domains: auth, analyze, products, history)│
 └──────┬───────────────┬──────────────┬──────┘
        │               │              │
        ▼               ▼              ▼
  YOLO Engine     OpenAI GPT-4o    Product Engine
(ultralytics)     (vision+text)     (fuzzy match)
        │               │              │
        └───────────────┴──────┬───────┘
                                ▼
                          PostgreSQL DB
                                │
                                ▼
                             AWS S3
                     (user-uploaded images)


Key Principles:

Domain-oriented (each domain owns routing + controller logic)

Service-oriented for reusable logic (analysis, matching, imports)

Side-effect isolation (S3 uploads & DB writes are backgrounded)

Deterministic output schema (every field always exists)

2. Directory Structure (v4.2 refactor, explained)
app/
  domains/
    analyze.py
    products.py
    auth.py
    history.py

  services/
    analyze_service.py
    image_utils.py
    match_utils.py
    product_import_service.py

  models/
    best.pt

  models.py
  utils.py
  main.py

2.1 domains/ — What these files actually do

Each file contains:

FastAPI router

Request parsing/validation

Controller logic

Error handling

Response schema structuring

This consolidates “routes + controllers” previously spread across 6–8 files.

domains/analyze.py

Contains:

POST /analyze/

POST /analyze/direct

Performs:

Input validation

Image preprocessing

YOLO detection

GPT-4 prompt assembly and decoding

S3 upload

Product recommendation

Background DB write

domains/products.py

Contains:

GET /products/

GET /products/search

GET /products/by-scientific-name/{x}

GET /products/by-disease/{x}

Plus:

In-memory product cache

Matcher scaffolding

domains/auth.py

Contains:

POST /auth/send_otp

POST /auth/verify_otp

GET /auth/profile

DELETE /auth/delete_account

Implements:

OTP generation

OTP DB lifecycle

JWT creation/verification

Cleanup logic

domains/history.py

Contains:

GET /history/
Returns authenticated user's detection history.

3. Data Model (Complete Schema Explanation)
3.1 PlantDetection
id (UUID)
mobile (string, FK-less)
timestamp
common_name
scientific_name
confidence_plant
disease
disease_scientific_name
diagnosis_json  (full GPT structured output)
s3_urls         (array)
recommendation  (product_id or null)
raw_prompt      (optional debug)


The full GPT output is preserved to allow:

doctor audits

model upgrades

fine-tuning datasets

3.2 OTP
id
mobile
otp
created_at
expires_at


Test mobile +919999999999 always returns 0000.

3.3 Product

Imported from Excel:

product_id
product_name
disease_scientific_name
disease_common_name
plant_scientific_name
plant_common_name
description
link

4. Analysis Pipeline (Detailed, Step-by-Step)

Below is the actual sequence for /analyze/.

4.1 Input → Image Preprocessing

For each uploaded image:

Validate content-type (image/jpeg, image/png)

Read into PIL

Auto-rotate (EXIF)

Resize to max 1536px dimension

Compress to < 1MB target

Detect whether image is:

Close-up (leaf dominance)

Wide view (entire plant)

Close-up images are:

prioritized in GPT reasoning

marked in metadata

4.2 YOLO Detection

YOLO (best.pt) detects plant species.

Output:

[
  { name: "Hibiscus", confidence: 0.93 },
  { name: "Rose", confidence: 0.91 }
]


Rules:

If >1 detection → choose highest confidence

If <0.75 confidence → fallback to GPT-only prompt

4.3 GPT-4 Vision + Text Prompting

Two messages are sent:

1. System prompt (static)

Includes:

Supported plant list

Scientific names

Output JSON schema

Required fields

Safety guards

Avoid hallucination instructions

2. User prompt

Includes:

All user images

YOLO plant suggestion

Close-up/wide detection metadata

“Return strictly valid JSON only” directive

3. Expected JSON output
{
  "plant": { "common_name": "", "scientific_name": "", "confidence": float },
  "diagnosis": {
     "type": "biotic|abiotic|healthy",
     "disease": "",
     "disease_scientific_name": "",
     "symptoms": [],
     "cause": "",
     "treatment": [],
     "prevention": []
  }
}


Parsing:

Strict JSON parsing with fallback to regex-based repair

Any repair attempts logged for QA

4.4 S3 Upload

Each image is uploaded with:

key = f"{mobile}/{uuid4()}.jpg"
ACL = public-read


Retry logic:

3 retries

exponential backoff (300ms → 600ms → 1200ms)

4.5 Product Recommendation

Computed using:

disease_score = fuzz.ratio(disease_scientific_name, product.disease_scientific_name)
plant_score   = fuzz.ratio(plant_scientific_name, product.plant_scientific_name)

final_score = 0.6 * disease_score + 0.4 * plant_score


If:

final_score >= FUZZY_SCORE_CUTOFF (default 85)


→ product selected
Else → null

4.6 Background Write to DB

We store:

plant info

diagnosis info

GPT raw JSON

product recommendation

S3 URLs

Non-blocking for fast responses.

5. Product Import System (Full Explanation)

Startup logic:

Check if Product table empty.

Load Excel:

Product_List.xlsx

Plant_Map.xlsx

Normalize plant names:

lowercase

strip whitespace

map ambiguous names

Insert into PostgreSQL

Load into in-memory cache for 1000x faster lookup

Cache is a list of all products with pre-normalized fields.

6. Authentication System (Deep Explanation)
6.1 OTP Generation

For each mobile request:

If user is test mobile → return 0000

Else:

Generate random 4-digit OTP

Write to DB

Send via E2A API

6.2 Verify OTP

Validate mobile

Validate OTP not expired

Generate JWT with payload:

sub: mobile
iat
exp

6.3 JWT Security

HS256 signing

24h expiry

Blacklisting not required because delete flow wipes history

7. Complete API Documentation

(Condensed listing here; full schemas provided if needed.)

/auth/send_otp
/auth/verify_otp
/auth/profile
/auth/delete_account
/analyze/
/analyze/direct
/products/
/products/search
/products/by-scientific-name/{x}
/products/by-disease/{x}
/history/
/health
/
8. System Startup Behavior

Order:

Load env vars

Initialize DB engine

Create tables

Import products (if needed)

Build in-memory product cache

Validate YOLO weights

Warm GPT model (optional)

Start FastAPI server

9. Performance Characteristics

/health → <50ms

/products/ → 3–10ms (cache hit)

/analyze/direct → 3–10 seconds (GPT-4)

/analyze/ → 5–12 seconds (YOLO + GPT-4 + S3 + DB)

10. Refactor v4.2 — Deep Dive
What changed

Routes + controllers merged

Models consolidated

Config modules eliminated

S3 uploader + DB utilities unified

File count reduced from 19 → 11

What did not change

API endpoints

Response schemas

DB schema

Product logic

Auth logic

Docker config

No frontend changes required.

11. Known Limitations & Future Roadmap
Limitations

No offline mode

GPT-4 cost considerations

Excel import requires structured headings

YOLO limited to trained species

Future

Redis caching

Model versioning

Batch processing

Offline fallback model

WebSocket real-time pipeline

Multi-language support