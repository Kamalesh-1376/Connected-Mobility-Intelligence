"""
Connected Mobility Intelligence (CMI) - End-to-End Runner
Executes the full data engineering & analytics pipeline, then launches the frontend.
Usage:
    python run_all.py
"""
import os
import sys
import time
import subprocess
import shutil
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

def log(msg: str):
    print(f"\n[CMI PIPELINE] {msg}")

def main():
    t_start = time.time()
    print("=" * 75)
    print("  CONNECTED MOBILITY INTELLIGENCE (CMI) - CUMTA URBAN MOBILITY CHALLENGE")
    print("  End-to-End Automated Pipeline & Frontend Launcher")
    print("=" * 75)

    # 1. Check requirements and config
    log("Step 1/4: Checking configuration and directories...")
    from src.config import load_config
    cfg = load_config()
    print(f"  DATA_DIR: {cfg['DATA_DIR']}")
    print(f"  Salt variable: {cfg['SALT_ENV_VAR']}")

    # 2. Ingestion and normalisation
    log("Step 2/4: Executing Phase 1 Ingestion & Normalisation...")
    from src.ingest_clean import run_ingestion_pipeline
    df_unified, metrics = run_ingestion_pipeline()
    print(f"  Unified events generated: {len(df_unified):,} rows in data/processed/unified_events.parquet")

    # 3. Transfer detection & analytics
    log("Step 3/4: Executing Phase 2 Transfer Detection & DBSCAN Clustering...")
    from src.transfer_analytics import run_transfer_pipeline
    integrated_matrix = run_transfer_pipeline()
    
    # Sync JSON contract to frontend
    pub_json = WORKSPACE_DIR / "frontend" / "public" / "integrated_od_matrix.json"
    src_json = WORKSPACE_DIR / "frontend" / "src" / "data" / "integrated_od_matrix.json"
    od_matrix_path = WORKSPACE_DIR / "data" / "processed" / "integrated_od_matrix.json"
    
    shutil.copyfile(od_matrix_path, pub_json)
    shutil.copyfile(od_matrix_path, src_json)
    print(f"  Synchronized integrated_od_matrix.json to frontend assets.")

    # Sync Suburban GeoJSON if present
    for fname in ["suburban_rail_network.geojson", "suburban_stations.geojson", "suburban_stations.json"]:
        p_src = WORKSPACE_DIR / "data" / "processed" / fname
        p_pub = WORKSPACE_DIR / "frontend" / "public" / fname
        if p_src.exists():
            shutil.copyfile(p_src, p_pub)

    # 4. Launch Frontend
    log(f"Step 4/4: Launching Frontend Dashboard in {time.time() - t_start:.1f}s...")
    frontend_dir = WORKSPACE_DIR / "frontend"
    print("  Starting Vite preview server at http://localhost:5173 ...")
    print("  Press Ctrl+C to terminate the dashboard server.\n")

    try:
        # Use npm run preview or npm run dev
        subprocess.run(["npm", "run", "preview", "--", "--port", "5173", "--host"], cwd=frontend_dir, shell=True)
    except KeyboardInterrupt:
        print("\n[CMI] Dashboard server stopped.")

if __name__ == "__main__":
    main()

