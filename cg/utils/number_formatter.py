import math

SI_THIN_SPACE = "\u202f"

SI_PREFIXES = [(1e12, "T", 2), (1e9, "G", 2), (1e6, "M", 2), (1e3, "k", 2), (1, "", 0)]


class Si:
    """
    Formats numbers according to SI standards.

    References:
        BIPM (2019). The International System of Units (SI Brochure), 9th edition.
        Section 5.4.4: Formatting numbers. https://www.bipm.org/en/publications/si-brochure/
    """

    @staticmethod
    def prefix(value: int | float, unit: str) -> str:
        """
        Formats numbers according to selected SI prefixes.
        """
        value = Si._integer_convert(value)
        for threshold, prefix, decimals in SI_PREFIXES:
            if value >= threshold:
                scaled_value = value / threshold
                return f"{scaled_value:.{decimals}f}{SI_THIN_SPACE}{prefix}{unit}"
        return f"{value}{SI_THIN_SPACE}{unit}"

    @staticmethod
    def group_digits(value: int | float) -> str:
        """
        Format according to SI group digits, section 5.4.4, BIPM (2019). The International System of Units (SI Brochure), 9th edition.
        """
        value = Si._integer_convert(value)
        return f"{value:,d}".replace(",", SI_THIN_SPACE)

    @staticmethod
    def _integer_convert(value: int | float) -> int:
        """
        Convert a float to an integer using classic rounding: .5 always rounds up.
        """
        if value >= 0:
            return int(math.floor(value + 0.5))
        else:
            return int(math.ceil(value - 0.5))
