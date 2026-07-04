"""
Contract Mapper: TRON Signal → Deriv Contract Parameters
Maps TRON's glassbox output to Deriv's contract API.
"""
from typing import Dict, Any, Literal
from dataclasses import dataclass

@dataclass
class ContractParams:
    contract_type: Literal["rise_fall", "vanilla", "multiplier"]
    symbol: str
    direction: Literal["CALL", "PUT"]
    stake: float
    duration: int  # in minutes or ticks
    duration_unit: Literal["t", "m", "h"]
    # Vanilla-specific
    strike: float = 0.0
    # Multiplier-specific
    leverage: int = 1
    stop_loss_percent: float = 0.0
    take_profit_percent: float = 0.0

class ContractMapper:
    """
    Converts TRON signal JSON into executable contract parameters.
    """

    @staticmethod
    def map_signal(signal: Dict[str, Any], 
                     mode: Literal["vanilla", "rise_fall", "multiplier"],
                     stake: float) -> ContractParams:
        """
        Map TRON signal to Deriv contract.
        """
        setup = signal.get("setup", {})
        symbol = signal.get("symbol", "R_100")
        direction = signal.get("bias", "CALL")

        if mode == "rise_fall":
            # Rise/Fall: direction + duration only. TRON's expiry_min is
            # already in minutes — Deriv's rise/fall duration_unit is "m".
            return ContractParams(
                contract_type="rise_fall",
                symbol=symbol,
                direction=direction,
                stake=stake,
                duration=setup.get("expiry_min", 5),
                duration_unit="m"
            )

        elif mode == "vanilla":
            # Vanilla: strike + expiry + direction
            return ContractParams(
                contract_type="vanilla",
                symbol=symbol,
                direction=direction,
                stake=stake,
                duration=setup.get("expiry_min", 5),
                duration_unit="m",
                strike=setup.get("strike", 0)
            )

        elif mode == "multiplier":
            # Multiplier: direction + leverage + SL/TP
            rr = setup.get("rr", 1.5)
            return ContractParams(
                contract_type="multiplier",
                symbol=symbol,
                direction=direction,
                stake=stake,
                duration=setup.get("expiry_min", 5),
                duration_unit="m",
                leverage=min(int(rr * 50), 500),  # Cap at 500x
                stop_loss_percent=100.0,  # Full stake as SL
                take_profit_percent=min(rr * 100, 500.0)  # RR-based TP
            )

        else:
            raise ValueError(f"Unknown mode: {mode}")

    @staticmethod
    def validate_params(params: ContractParams, balance: float) -> tuple[bool, str]:
        """
        Validate contract parameters before execution.
        Returns: (is_valid, error_message)
        """
        if params.stake <= 0:
            return False, "Stake must be positive"

        if params.stake > balance * 0.1:  # Max 10% of balance per trade
            return False, f"Stake {params.stake} exceeds 10% of balance {balance}"

        if params.contract_type == "vanilla" and params.strike <= 0:
            return False, "Invalid strike price"

        if params.contract_type == "multiplier" and params.leverage > 500:
            return False, "Leverage exceeds maximum 500x"

        return True, "OK"
