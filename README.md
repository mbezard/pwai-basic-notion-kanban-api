## Configure the app
1. Create a `.env` file by copying the `.env.example` file and filling in the values
```bash
cp .env.example .env
```

2. In the `main.py`, change the `kanban_database_id` to the id of the database you want to use


## Start the app
```bash
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8082 --reload
```

## Open it to the world
```bash
ngrok http 8082
```

## Get the openapi.json
Open `http://localhost:8082/openapi.json` in your browser


## Test the app
Open `http://localhost:8082/docs` in your browser
