from pydantic import BaseModel


class BaselineConfig(BaseModel):
    """
    Configuration for baseline training and scoring.
    """

    use_hour_of_day: bool = True

    mad_threshold: float = 3.5
    min_samples: int = 30

    # Protect against zero-MAD edge cases
    min_mad: float = 1e-6
