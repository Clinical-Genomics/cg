from datetime import datetime


def get_cancel_comment(user_name: str) -> str:
    date: str = datetime.now().strftime("%Y-%m-%d")
    return f"Cancelled {date} by {user_name}"


def get_confirmation_message(sample_ids: list[str], case_ids: list[str]) -> str:
    message = f"Cancelled {len(sample_ids)} samples. "
    if case_ids:
        cases = ", ".join(case_ids)
        message += f"Found {len(case_ids)} cases with additional samples: {cases}."
    else:
        message += "No case contained additional samples."
    return message
