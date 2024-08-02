from datetime import datetime


def get_cancel_comment(user_name: str) -> str:
    date: str = datetime.now().strftime("%Y-%m-%d")
    return f"Cancelled {date} by {user_name}"


def get_confirmation_message(sample_ids: list[str], remaining_cases: list[str]) -> str:
    samples: str = "sample" if len(sample_ids) == 1 else "samples"
    message: str = f"Cancelled {len(sample_ids)} {samples}. "
 
    if remaining_cases:
        cases = "case" if len(remaining_cases) == 1 else "cases"
        case_message = ", ".join(remaining_cases)
        message += f"Found {len(remaining_cases)} {cases} with additional samples: {case_message}."
    else:
        message += "No case contained additional samples."

    return message
