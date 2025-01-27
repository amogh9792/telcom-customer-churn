from source.utility.utility import generate_global_timestamp
from source.logger import setup_logger
from source.pipeline.pipeline import DataPipeline

global_timestamp = generate_global_timestamp()
setup_logger(global_timestamp)
pipeline = DataPipeline(global_timestamp)

pipeline.run_train_pipeline()
pipeline.run_predict_pipeline()

