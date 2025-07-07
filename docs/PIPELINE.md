1. API Service    → Raw JSON response
2. Extractor      → Creates WorkoutRecord/RecoveryRecord models ← HERE!
3. Transformer    → Cleans/normalizes the models  
4. Aggregator     → Analyzes the models
5. Reporter       → Uses models for visualization

src/
├── api/services/          # Pure API communication
│   ├── whoop_service.py
│   ├── oura_service.py
│   ├── withings_service.py
│   ├── hevy_service.py
│   └── onedrive_service.py
├── processing/extractors/ # Data transformation
│   ├── whoop_extractor.py
│   ├── oura_extractor.py
│   ├── withings_extractor.py
│   └── hevy_extractor.py
└── models/               # Data structures
    └── data_records.py
