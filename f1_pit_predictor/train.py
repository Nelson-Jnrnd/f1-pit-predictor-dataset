from pathlib import Path
import dvc.api
import typer
from loguru import logger
from tqdm import tqdm
import pandas as pd

from f1_pit_predictor.modeling.random_forest_trainer import RandomForestTrainer
from f1_pit_predictor.config import MODELS_DIR, PROCESSED_DATA_DIR

app = typer.Typer()

def get_x_y(df, target_col="target"):
    """
    Split the DataFrame into features and target.
    """
    return df.drop(target_col, axis=1), df[target_col]

@app.command()
def main(
    training_data_path: Path = PROCESSED_DATA_DIR / "train_processed.csv",
    test_data_path: Path = PROCESSED_DATA_DIR / "test_processed.csv",
    model_path: Path = MODELS_DIR,
):
    logger.info("Training model...")
    params = dvc.api.params_show()
    logger.info(f"Parameters: {params}")
    model = RandomForestTrainer(params, "RandomForest")
    train_df = pd.read_csv(training_data_path)
    x_train, y_train = get_x_y(train_df, target_col=params["target"])
    model.train(x_train, y_train)
    logger.info("Model trained.")
    
    logger.info("Predicting on test set...")
    test_df = pd.read_csv(test_data_path)
    x_test, y_test = get_x_y(test_df, target_col=params["target"])
    y_pred = model.predict(x_test)
    logger.info("Predictions made.")

    logger.info("Saving model...")
    model.save(model_path / "random_forest.pkl")
    logger.info("Model saved.")

if __name__ == "__main__":
    app()
