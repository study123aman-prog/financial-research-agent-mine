"""
Calculation Engine Tool
Performs financial calculations including ratios, growth rates, DCF
"""

from typing import Dict, Any, List


def calculation_engine(
    calculation_type: str,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform financial calculations.

    Args:
        calculation_type: Type of calculation to perform
        inputs: Dictionary of input values

    Returns:
        Dictionary with calculation results and steps
    """

    calculators = {
        "growth_rate": _growth_rate,
        "cagr": _cagr,
        "pe_ratio": _pe_ratio,
        "roe": _roe,
        "debt_to_equity": _debt_to_equity,
        "profit_margin": _profit_margin,
        "dcf": _dcf,
        "ebitda_margin": _ebitda_margin,
        "current_ratio": _current_ratio,
        "free_cash_flow": _free_cash_flow
    }

    calculator = calculators.get(calculation_type)

    if not calculator:
        return {
            "success": False,
            "error": f"Unknown calculation type: {calculation_type}",
            "available_types": list(calculators.keys())
        }

    try:
        result = calculator(inputs)
        return {
            "success": True,
            "calculation_type": calculation_type,
            "inputs": inputs,
            "result": result,
            "source": "Calculation Engine",
            "reliability_tier": 1
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "calculation_type": calculation_type
        }


def _growth_rate(inputs: Dict) -> Dict:
    current = float(inputs["current_value"])
    previous = float(inputs["previous_value"])
    rate = ((current - previous) / abs(previous)) * 100
    return {
        "growth_rate_percent": round(rate, 2),
        "steps": f"({current} - {previous}) / {previous} * 100 = {rate:.2f}%"
    }


def _cagr(inputs: Dict) -> Dict:
    beginning = float(inputs["beginning_value"])
    ending = float(inputs["ending_value"])
    years = float(inputs["years"])
    cagr = ((ending / beginning) ** (1 / years) - 1) * 100
    return {
        "cagr_percent": round(cagr, 2),
        "steps": f"({ending}/{beginning})^(1/{years}) - 1 = {cagr:.2f}%"
    }


def _pe_ratio(inputs: Dict) -> Dict:
    price = float(inputs["stock_price"])
    eps = float(inputs["earnings_per_share"])
    pe = price / eps
    return {
        "pe_ratio": round(pe, 2),
        "steps": f"{price} / {eps} = {pe:.2f}"
    }


def _roe(inputs: Dict) -> Dict:
    net_income = float(inputs["net_income"])
    equity = float(inputs["shareholders_equity"])
    roe = (net_income / equity) * 100
    return {
        "roe_percent": round(roe, 2),
        "steps": f"{net_income} / {equity} * 100 = {roe:.2f}%"
    }


def _debt_to_equity(inputs: Dict) -> Dict:
    total_debt = float(inputs["total_debt"])
    equity = float(inputs["shareholders_equity"])
    ratio = total_debt / equity
    return {
        "debt_to_equity_ratio": round(ratio, 2),
        "steps": f"{total_debt} / {equity} = {ratio:.2f}"
    }


def _profit_margin(inputs: Dict) -> Dict:
    net_income = float(inputs["net_income"])
    revenue = float(inputs["revenue"])
    margin = (net_income / revenue) * 100
    return {
        "profit_margin_percent": round(margin, 2),
        "steps": f"{net_income} / {revenue} * 100 = {margin:.2f}%"
    }


def _dcf(inputs: Dict) -> Dict:
    cash_flows = inputs["cash_flows"]
    discount_rate = float(inputs["discount_rate"]) / 100
    terminal_growth = float(inputs.get("terminal_growth_rate", 0.025))

    pv_sum = 0
    steps = []

    for i, cf in enumerate(cash_flows, 1):
        pv = float(cf) / ((1 + discount_rate) ** i)
        pv_sum += pv
        steps.append(f"Year {i}: {cf} / (1+{discount_rate})^{i} = {pv:.2f}")

    last_cf = float(cash_flows[-1])
    terminal_value = last_cf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / ((1 + discount_rate) ** len(cash_flows))
    total_value = pv_sum + pv_terminal

    return {
        "intrinsic_value": round(total_value, 2),
        "pv_of_cash_flows": round(pv_sum, 2),
        "terminal_value": round(pv_terminal, 2),
        "steps": steps
    }


def _ebitda_margin(inputs: Dict) -> Dict:
    ebitda = float(inputs["ebitda"])
    revenue = float(inputs["revenue"])
    margin = (ebitda / revenue) * 100
    return {
        "ebitda_margin_percent": round(margin, 2),
        "steps": f"{ebitda} / {revenue} * 100 = {margin:.2f}%"
    }


def _current_ratio(inputs: Dict) -> Dict:
    current_assets = float(inputs["current_assets"])
    current_liabilities = float(inputs["current_liabilities"])
    ratio = current_assets / current_liabilities
    return {
        "current_ratio": round(ratio, 2),
        "steps": f"{current_assets} / {current_liabilities} = {ratio:.2f}"
    }


def _free_cash_flow(inputs: Dict) -> Dict:
    operating_cf = float(inputs["operating_cash_flow"])
    capex = float(inputs["capital_expenditures"])
    fcf = operating_cf - capex
    return {
        "free_cash_flow": round(fcf, 2),
        "steps": f"{operating_cf} - {capex} = {fcf:.2f}"
    }