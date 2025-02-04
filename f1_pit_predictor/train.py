from pathlib import Path
import dvc.api
import typer
from loguru import logger
from tqdm import tqdm

from f1_pit_predictor.config import MODELS_DIR, PROCESSED_DATA_DIR

app = typer.Typer()

@app.command()
def main(
    training_data_path: Path = PROCESSED_DATA_DIR / "train_processed.csv",
    test_data_path: Path = PROCESSED_DATA_DIR / "test_processed.csv",
    model_path: Path = MODELS_DIR,
):
    logger.info("Training model...")
    params = dvc.api.params_show()
    logger.info(f"Parameters: {params}")
    


if __name__ == "__main__":
    app()
