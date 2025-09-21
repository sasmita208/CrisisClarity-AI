# CrisisClarity AI

CrisisClarity AI is an AI-powered platform for detecting misinformation related to **crises and disasters**. It helps individuals, organizations, and authorities quickly verify the authenticity of claims, alerts, and posts during emergency situations. The system analyzes both text and URLs and provides confidence scores with source references to support rapid decision-making.

🌐: https://crisis-clarity-ai.vercel.app/
---
## Features

- **Disaster & Crisis Verification**: Detect fake or misleading claims during emergencies.  
- **Text Verification**: Analyze textual claims and messages.   
- **Fact Cards**: Summarized AI-powered analysis with evidence sources.  
- **Confidence Scores**: Provide numerical confidence for each prediction.  
- **Multi-source Evidence**: Cross-reference data with credible fact-checking sources and government releases.  

---

## Prerequisites

- Python 3.11+  
- Node.js 18+ / npm 9+  
- pip / yarn  

1. Navigate to backend folder:
```bash
cd CrisisClarity-AI
```

2.Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```
Backend runs on: http://127.0.0.1:8000

3. Frontend Setup
```bash
cd frontend
npm i
npm run dev
```
Frontend runs on: http://localhost:8080


