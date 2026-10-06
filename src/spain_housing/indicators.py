"""Scalar indicators with explicit units; apply only to comparable observations."""

from math import isfinite


def _nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def _positive(value: float, name: str) -> float:
    value = _nonnegative(value, name)
    if value == 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def rent_to_income_pct(monthly_rent: float, annual_net_household_income: float) -> float:
    """Annual rent / annual net household income × 100; excludes utilities."""
    return 1200 * _nonnegative(monthly_rent, "rent") / _positive(
        annual_net_household_income, "income"
    )


def price_to_income_years(purchase_price: float, annual_household_income: float) -> float:
    """Total purchase price / annual household income; state net/gross in reports."""
    return _nonnegative(purchase_price, "price") / _positive(annual_household_income, "income")


def per_1000(count: float, population: float) -> float:
    """Count per 1,000 people or households; label the denominator explicitly."""
    return 1000 * _nonnegative(count, "count") / _positive(population, "denominator")


def constant_price(nominal_price: float, cpi: float, base_cpi: float) -> float:
    """Convert to base-period euros using a consistent CPI series."""
    return _nonnegative(nominal_price, "price") * _positive(base_cpi, "base CPI") / _positive(
        cpi, "CPI"
    )


def mortgage_payment(principal: float, annual_rate: float, years: int) -> float:
    """Monthly annuity payment; decimal nominal annual rate; excludes fees/insurance."""
    principal = _nonnegative(principal, "principal")
    annual_rate = _nonnegative(annual_rate, "annual rate")
    if isinstance(years, bool) or not isinstance(years, int) or years <= 0:
        raise ValueError("years must be a positive integer")
    months = years * 12
    rate = annual_rate / 12
    if rate == 0:
        return principal / months
    return principal * rate / (1 - (1 + rate) ** -months)
