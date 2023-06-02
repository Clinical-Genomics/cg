def q30_ratio(q30_yield: int, total_yield: int) -> float:
    """
    Calculate the proportion of bases that have a Phred quality score of 30 or more.
    Args:
        q30_yield (int): The sum of all Q30 yields.
        total_yield (int): The total yield.
    Returns:
        float: Proportion of bases with Q30.
    """
    return round(q30_yield / total_yield, 2)


def average_quality_score(total_quality_score: int, total_yield: int) -> float:
    """
    Calculate the average quality score of all bases.
    Args:
        total_quality_score (int): The sum of quality scores.
        total_yield (int): The total yield.
    Returns:
        float: Average quality score of all bases.
    """
    return round(total_quality_score / total_yield, 2)
