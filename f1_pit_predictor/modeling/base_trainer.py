from abc import ABC, abstractmethod
from sklearn.metrics import accuracy_score
from dvclive import Live
from loguru import logger
class BaseTrainer(ABC):
    """
    Abstract base class for model training.
    """

    def __init__(self, config, name):
        super().__init__()
        self.config = config
        self.name = name
        self.model = None
    
    @abstractmethod
    def train(self, x, y):
        """
        Train the model.
        """
        pass

    def evaluate(self, x, y):
        """
        Evaluate the model.
        """
        y_pred = self.predict(x)
        acc = accuracy_score(y, y_pred)
        try :
            with Live(resume=True) as live:
                live.log_params(self.config)
                live.log_metric("accuracy", acc)
        except Exception as e:
            logger.error(f"Failed to start dvclive: {e}")

    @abstractmethod
    def predict(self, x):
        """
        Make predictions using the trained model.
        """
        pass

    @abstractmethod
    def save(self, path):
        """
        Save the trained model to a file.
        """
        pass