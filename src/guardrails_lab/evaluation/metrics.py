from collections.abc import Callable, Sequence


def binary_metrics(
    samples: Sequence[tuple[str, bool]],
    detector: Callable[[str], bool],
) -> dict[str, float | int]:
    """Measure a binary detector against labeled examples."""
    true_positive = false_positive = false_negative = true_negative = 0
    for text, is_attack in samples:
        flagged = detector(text)
        if flagged and is_attack:
            true_positive += 1
        elif flagged:
            false_positive += 1
        elif is_attack:
            false_negative += 1
        else:
            true_negative += 1

    def divide(numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 0.0

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": divide(true_positive, true_positive + false_positive),
        "recall": divide(true_positive, true_positive + false_negative),
        "false_positive_rate": divide(
            false_positive, false_positive + true_negative
        ),
    }
