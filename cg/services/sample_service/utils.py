from datetime import datetime


def get_cancel_comment(user_name: str) -> str:
    date: str = datetime.now().strftime("%Y-%m-%d")
    return f"Cancelled {date} by {user_name}"


def get_confirmation_message(sample_ids: list[str], remaining_cases: list[str]):
    samples: str = "sample" if len(sample_ids) == 1 else "samples"
    cases: str = "case" if len(remaining_cases) == 1 else "cases"

    message: str = f"Cancelled {len(sample_ids)} {samples}. "
    case_message: str = ""

    for case_id in remaining_cases:
        case_message = f"{case_message} {case_id},"

    case_message = case_message.strip(",")

    if remaining_cases:
        case_count = len(remaining_cases)
        message += f"Found {case_count} {cases} with additional samples: {case_message}."
    else:
        message += "No case contained additional samples."
