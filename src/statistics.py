import numpy as np
from scipy import stats

def calculate_p_value(model_score: float, baseline_scores: list) -> float:
    """
    Calculates the p-value of the model's score against a distribution of baseline scores.
    
    Hypothesis:
    H0: The model score comes from the same distribution as the baseline scores (random chance).
    H1: The model score is significantly better (higher) than the baseline scores.
    
    Args:
        model_score (float): The metric score (e.g., AUC, MRR) of the trained model.
        baseline_scores (list): A list of scores from random/shuffled baselines.
        
    Returns:
        float: The empirical p-value.
    """
    if len(baseline_scores) == 0:
        raise ValueError("Baseline scores list cannot be empty.")
    
    # Empirical p-value
    # Count how many baseline scores are >= model_score
    # Add 1 to both numerator and denominator for unbiased estimate (North et al., 2002)
    count_better_or_equal = sum(1 for s in baseline_scores if s >= model_score)
    n_permutations = len(baseline_scores)
    
    p_value = (count_better_or_equal + 1) / (n_permutations + 1)
    return p_value

def compare_models_ttest(model_a_scores: list, model_b_scores: list) -> float:
    """
    Performs a paired t-test to compare two models if we have per-fold or per-run scores.
    
    Args:
        model_a_scores (list): List of scores for model A.
        model_b_scores (list): List of scores for model B.
        
    Returns:
        float: The p-value from the t-test.
    """
    if len(model_a_scores) != len(model_b_scores):
        raise ValueError("Score lists must have the same length for paired t-test.")
        
    # ttest_rel is for paired samples
    t_stat, p_val = stats.ttest_rel(model_a_scores, model_b_scores)
    
    # We want one-tailed test (is A better than B?), so we divide p by 2 if t_stat is positive
    # If t_stat is negative, it means A is worse, so p-value for "better" is high.
    if t_stat > 0:
        return p_val / 2
    else:
        return 1.0 - (p_val / 2)
