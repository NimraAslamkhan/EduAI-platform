import sys
import os
# Ensure workspace root is on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database.db_manager import DatabaseManager
from src.ml.ml_pipeline import StudentMLPipeline

if __name__ == '__main__':
    db = DatabaseManager()
    data = db.get_performance_data_for_ml(school_id=1)
    print(f"Loaded {len(data)} records for ML")
    pipeline = StudentMLPipeline()
    # Use a dry run (do not persist)
    res = pipeline.generate_ai_alerts(data, db=None, school_id=1, persist=False)
    print("AI alerts dry-run summary:")
    print(res)
