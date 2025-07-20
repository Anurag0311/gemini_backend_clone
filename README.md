# Gemini_backend_clone
A Gemini-style backend system that enables user-specific chatrooms, OTP-based
login, Gemini API-powered AI conversations, and subscription handling via Stripe. 

This project is a backend system for handling AI-powered chatrooms using Google Gemini API, task queuing with Celery and Redis, user management with JWT, and payment integration with Stripe. Built with FastAPI.

---

## 🧩 Features

- ✅ User authentication via JWT
- ✅ Chatroom creation & conversation management
- ✅ Async Gemini API call handling using Celery and Redis
- ✅ Stripe integration for Pro subscriptions
- ✅ Webhook support for payment status updates
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Easily testable via Postman

---

## 📦 Tech Stack

| Layer          | Stack                                 |
|----------------|---------------------------------------|
| Backend        | FastAPI                               |
| Async Queue    | Celery + Redis                        |
| Database       | PostgreSQL + SQLAlchemy (async+sync)  |
| Auth           | JWT                                   |
| Payments       | Stripe                                |
| AI Integration | Google Gemini API                     |


## How to set up and run the project
Ensure that Redis and PostgreSQL are installed, or that you have access to their IP address, port, and password.
## 1. Backend Setup

### 1.1 Python Version Check
Ensure you are using the correct Python version.
```bash
python --version  # Should match project requirement
```

### 1.2 Virtual Environment Setup
Create and activate a virtual environment:
```bash
python -m venv venv  # Create virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows
```

### 1.3 Installing Dependencies
```bash
pip install -r requirements.txt
```
If adding a new package, update `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### 1.4 Creating `.env` File
Always keep environment variables in `.env`. Example:
```
DATABASE_URL= "postgresql+asyncpg://postgres:your_password@your_db_ip:your_db_port/your_db_name"
SYNC_DATABASE_URL= "postgresql+psycopg2://postgres:your_password@your_db_ip:your_db_port/your_db_name"

GEMINI_API_KEY= "YOUR_GEMINI_API_KEY"

REDIS_HOST="YOUR_REDIS_HOST"
REDIS_PORT="YOUR_REDIS_HOST_PORT"

STRIPE_SECRET_KEY = "YOUR_STRIPE_KEY"

STRIPE_WEBHOOK_SECRET = "YOUR_STRIPE_WEBHOOK_KEY"
```

## 2. Database Setup

### 2.1 Creating Database
Run the database creation script:
```bash
python db/create.py
```

## 3.Redis-Celery Setup
Make sure you are in `gemini_backend_clone` directory and run below command:

`python -m celery -A core.celery_worker.celery_app worker --loglevel=info --pool=solo`

this basically instantiate the worker and connects to redis-broker

## 4. Run the application
Run the below command:

`python main.py`

while being inside `gemini_backend_clone` directory


## Architecture overview

sequenceDiagram

    participant User (Frontend/Postman)

    participant FastAPI

    participant Celery (Redis)

    participant Worker

    participant Gemini API

    participant PostgreSQL (ChatroomHistory)



    User->>FastAPI: POST /chatroom/{id}

    FastAPI->>FastAPI: Validate input

    FastAPI->>Celery: get_and_store.delay()

    Celery->>Worker: Pick up task

    Worker->>Gemini API: Send prompt via HTTPX

    Gemini API-->>Worker: Return response

    Worker->>PostgreSQL: Store response in ChatroomHistory

    User->>FastAPI: GET /message-status/{task_id}

    FastAPI-->>User: Return Gemini response



### 1. FastAPI (API Layer)
FastAPI is your main web framework. It handles:

`Routing (@router.get, @router.post, etc.)`

`Request parsing (via Pydantic schemas)`

`Dependency injection (like Depends(get_current_user))`

`Response formatting (JSON)`

✅ Key Roles:

Acts as the RESTful interface that clients (e.g. frontend or Postman) interact with.

Delegates tasks to services or queues where necessary.


### 2. Routers
These are modular route definitions grouped by functionality:

`/chatroom`: Handles chatroom creation and message processing.

`/subscribe`: Initiates Stripe subscriptions.

`/webhook`: Processes events from Stripe (like payment success/failure).

`/user`: Handles user creation and otp-logins

Each router focuses on a single domain and calls appropriate service functions or Celery tasks.

### 3. Services
This folder contains business logic like communicating with the Gemini API, processing messages, etc.

Example: `gemini_task.py`
Contains the task function `get_and_store()` that:

Calls the Gemini API via `get_gemini_response()`

Stores the response in ChatroomHistory

Is triggered asynchronously through Celery

This layer ensures your app logic is decoupled from routing and background infrastructure.


### 4. Celery Worker (Asynchronous Processing)
File: `core/celery_worker.py`

Defines the celery_app instance:

`celery_app = Celery(..., broker=REDIS_URL, backend=REDIS_URL)`

Starts a background worker process that listens for tasks and executes them.

Why Celery?

`Gemini API calls may take several seconds. Instead of blocking the main FastAPI thread (which affects user experience and scalability), the task is delegated to a worker queue.`

### 5. Redis (Broker + Result Backend)
Redis is used in two roles:

`Message Broker`: When FastAPI schedules a task, Redis holds the job until a worker picks it up.

`Result Backend`: Stores the output of tasks (e.g., Gemini API response), which can be retrieved later via task ID.

Why Redis?

`It’s fast, lightweight, and integrates well with Celery.
Enables scalable task queuing in production environments.`


### 6. Gemini API (via httpx)

Gemini is Google's generative AI model. You interact with it by:

Creating structured JSON prompts

Sending HTTP POST requests using httpx (a modern, async-compatible HTTP client)

Parsing the response and storing it in the DB

All Gemini interactions are encapsulated in your `utils/utils.py` or similar helper.


### 7. Stripe Integration
Stripe is used to manage paid subscriptions:

✅ /subscribe/pro: Creates a Stripe Checkout session for the user.

✅ /webhook/stripe: Listens for events like `payment_success`, `payment_failure`, etc.

✅ /subscription/status: Shows the user’s current subscription plan `(Basic/Pro)`

This allows your app to gate access to premium features (e.g., more Gemini requests or advanced chatroom options).


### 8. Assumptions / Design Decisions
It is assumed that the user does not require an immediate Gemini API response in the same request to `POST /chatroom/{id}`.

Calling the Gemini API is a time-consuming operation (due to network latency and model inference). Therefore, embedding it directly in the request-response cycle would make the API synchronous and slow down user experience.

To keep the API responsive and scalable, the request to `/chatroom/{id}` simply queues the task using Celery, and returns a task_id immediately.

The client (frontend or Postman) can then poll `/chatroom/message-status/{task_id}` to check if the Gemini response is ready.

This design ensures a non-blocking UX and allows background processing of long-running tasks.