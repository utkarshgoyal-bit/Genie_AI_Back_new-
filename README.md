# Garden Genie AI - Backend API

Plant disease detection and product recommendation system powered by AI.

## Features

- 🌱 Plant disease detection using YOLO + OpenAI
- 🔍 Product recommendations based on plant and disease
- 📊 Database of 181 products covering 10 plant species
- 🚀 FastAPI backend with PostgreSQL database

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **AI Models**: YOLO (plant detection) + OpenAI GPT-4 (disease analysis)
- **Deployment**: Docker

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL
- OpenAI API Key

### Installation

1. Clone the repository
```bash
git clone <your-repo-url>
cd Genie_AI_Back_new
## Deployment Notes

### Nginx Configuration Required

For production deployment, ensure Nginx allows large file uploads:
```nginx
client_max_body_size 20M;
```

See `DEPLOYMENT_NOTES.md` for detailed setup instructions.

