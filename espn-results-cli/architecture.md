# ESPN Results CLI — AWS Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  User                                                                       │
│                                                                             │
│  ┌──────────────────────┐        ┌──────────────────────┐                  │
│  │  CLI                 │        │  Streamlit UI         │                  │
│  │  espn_results.py     │        │  app.py               │                  │
│  └──────────┬───────────┘        └──────────┬───────────┘                  │
└─────────────┼──────────────────────────────┼────────────────────────────────┘
              │ direct calls                  │ HTTP GET
              │                               ▼
              │                  ┌────────────────────────┐
              │                  │  API Gateway           │
              │                  │  v114kxt4i7            │
              │                  │  (us-east-1)           │
              │                  └──────────┬─────────────┘
              │                             │ invoke
              │                             ▼
              │                  ┌────────────────────────────────────────┐
              │                  │  Lambda                                │
              │                  │                                        │
              │                  │  clt-espn-results-production           │
              │                  │  clt-espn-results-staging              │
              │                  │                                        │
              │                  │  lambda_handler.py                     │
              │                  │  espn_results.py                       │
              │                  │                                        │
              │                  │  actions: results | lineup |           │
              │                  │           standings | player | team    │
              │                  └──────────┬─────────────────────────────┘
              │                             │
              ├─────────────────────────────┤
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌────────────────────────────┐
│  DynamoDB               │   │  External APIs (no auth)   │
│  espn_cache             │   │                            │
│  (us-east-1)            │   │  espn.com.uy  (HTML)       │
│                         │   │  site.api.espn.com         │
│  PK: cache_key (S)      │   │  site.web.api.espn.com     │
│  TTL: expires_at (1h)   │   │  en.wikipedia.org          │
│  Billing: on-demand     │   │  nominatim.openstreetmap   │
└─────────────────────────┘   └────────────────────────────┘
```

## AWS Services

| Service | Resource | Role |
|---|---|---|
| API Gateway | `v114kxt4i7` | HTTP entry point for Streamlit UI |
| Lambda | `clt-espn-results-production` | Handles all 5 actions in production |
| Lambda | `clt-espn-results-staging` | Staging environment |
| DynamoDB | `espn_cache` | Response cache with 1h TTL |

## Data Flow

1. **Streamlit UI** → GET `https://v114kxt4i7.execute-api.us-east-1.amazonaws.com/?action=<action>&...`
2. **API Gateway** → invokes Lambda (`lambda_handler.py`)
3. **Lambda** → checks DynamoDB cache (`cache_key = URL`)
   - Cache hit → returns cached response
   - Cache miss → calls external ESPN/Wikipedia/OSM APIs → stores in DynamoDB → returns result
4. **CLI** (`espn_results.py`) → hits DynamoDB + external APIs directly (no API Gateway)

## Deploy

```bash
./deploy.sh   # zips lambda_handler.py + espn_results.py → updates both Lambda functions
```
