from pathlib import Path
import pickle
import typer
from loguru import logger
from tqdm import tqdm
import pandas as pd
from typing_extensions import Annotated

from f1_pit_predictor.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, RANDOM_STATE
from f1_pit_predictor.preprocessing.cleaning import clean_data
from f1_pit_predictor.preprocessing.splitting import get_train_test_split
from f1_pit_predictor.preprocessing.features import preprocess_training_set, preprocess_test_set

app = typer.Typer()

def load_data(input_path: Path, years: list[int]) -> pd.DataFrame:
    """
    Concatenate the raw data from races in the specified years into a single DataFrame.
    """
    df_list = []

    for year in years:
        year_path = input_path / str(year)
        
        if not year_path.exists():
            logger.warning(f"Directory not found at {year_path}. Skipping...")
            continue

        race_files = list(year_path.glob("*.csv"))

        if not race_files:
            logger.warning(f"Files found for {year}. Skipping...")
            continue

        logger.info(f"Loading races from {year}")

        for race_file in race_files:
            try:
                df = pd.read_csv(race_file)
                df_list.append(df)
            except Exception as e:
                logger.error(f"Failed to load {race_file}: {e}")

    if not df_list:
        logger.error("No data loaded. Returning an empty DataFrame.")
        return pd.DataFrame()

    df_all = pd.concat(df_list, ignore_index=True)
    logger.success(f"Loaded {df_all.shape[0]} rows from seasons {df_all['Year'].unique()}")

    return df_all

def save_data(df: pd.DataFrame, output_path: Path):
    """
    Save the DataFrame to a CSV file.
    """
    logger.info(f"Saving data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.success("Data saved successfully.")

@app.command()
def clean(
    input_path: Path = RAW_DATA_DIR,
    output_path: Path = PROCESSED_DATA_DIR / "clean.csv",
    years: Annotated[list[int], typer.Option(help= "years of data to process. If not specified all years will be processed")] = None,
    target: Annotated[str, typer.Option(help="target variable to preprocess (pit or tire)")] = "pit",
): 
    """
    Load the raw data, clean it, and save the resulting DataFrame to a CSV file.
    """
    logger.info(f"Loading data from {input_path}")
    # Find all directories with numeric names (years)
    all_years = sorted(
        [int(dir_.name) for dir_ in input_path.iterdir() if dir_.is_dir() and dir_.name.isdigit()]
    )
    if years:
        all_years = [year for year in all_years if year in years]
    
    df = load_data(input_path, all_years)
    
    if df.empty:
        logger.error("No data loaded. Exiting...")
        return
    
    logger.info(" Cleaning data...")
    df = clean_data(df, target=target, drop=True)

    if df.empty:
        logger.error("No data after preprocessing. Exiting...")
        return
    
    save_data(df, output_path)

@app.command()
def split(
    input_path: Path = PROCESSED_DATA_DIR / "clean.csv",
    output_path: Path = PROCESSED_DATA_DIR,
    test_size: Annotated[float, typer.Option(help="proportion of data to include in the test set")] = 0.2,
): 
    """
    Load the cleaned data, split it into training and test sets, and save the resulting DataFrames to CSV files.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    if df.empty:
        logger.error("No data loaded. Exiting...")
        return
    
    logger.info(" Splitting data...")
    train_df, test_df = get_train_test_split(df, test_size=test_size, random_state=RANDOM_STATE)

    if train_df.empty or test_df.empty:
        logger.error("No data after preprocessing. Exiting...")
        return

    logger.info("Saving data...")    
    save_data(train_df, output_path / "train.csv")
    save_data(test_df, output_path / "test.csv")


@app.command()
def prepare(
    input_path: Path = PROCESSED_DATA_DIR,
    output_path: Path = PROCESSED_DATA_DIR,
): 
    """
    Load the split data, do feature engineering on it, and save the resulting DataFrame to a CSV files.
    """
    logger.info(f"Loading data from {input_path}")
    train_df = pd.read_csv(input_path / "train.csv")
    test_df = pd.read_csv(input_path / "test.csv")

    if train_df.empty or test_df.empty:
        logger.error("No data loaded. Exiting...")
        return

    train_df, encoder = preprocess_training_set(train_df)
    test_df = preprocess_test_set(test_df, encoder)
    
    train_df.dropna(inplace=True)
    test_df.dropna(inplace=True)

    logger.info("Saving data...")    
    save_data(train_df, output_path / "train_processed.csv")
    save_data(test_df, output_path / "test_processed.csv")
    
    logger.info("Saving encoder...")
    with open(output_path / "encoder.pkl", "wb") as f:
        pickle.dump(encoder, f)

if __name__ == "__main__":
    app()
