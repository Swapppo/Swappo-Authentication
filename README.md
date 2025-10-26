# Swappo Backend - FastAPI Hello World

A simple FastAPI application with a Hello World endpoint.

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- On Windows:
```bash
venv\Scripts\activate
```
- On macOS/Linux:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
python main.py
```

## API Endpoints

- `GET /` - Returns a Hello World message
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Testing

Once the server is running, you can:
1. Visit http://localhost:8000 to see the Hello World message
2. Visit http://localhost:8000/docs to see the interactive API documentation
3. Visit http://localhost:8000/health for the health check