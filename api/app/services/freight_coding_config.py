"""Freight cost-coding configuration (PIDSA worksheet).

EDITABLE LOOKUP TABLES — extracted from the 'Freight coding NEW PIDSA' workbook.
These drive the generated per-shipment coding sheet. Non-developers can adjust
G/L codes, cost centers, and chemistry rows here without touching the generator.

G/L CODES: the authoritative mapping is NOT yet confirmed, so defaults are blank.
The analyst enters/corrects the G/L code per charge row during review (it persists
on the document). When the correct charge-type -> G/L mapping is provided, fill in
the defaults below and they will pre-populate (analyst can still override).
"""
from __future__ import annotations

# Charge-type -> DEFAULT G/L account code. Intentionally blank until the
# authoritative mapping is confirmed; analyst sets these per shipment for now.
GL_CODE_BY_CHARGE: dict[str, str] = {
    "AIR_FREIGHT_JAPAN": "",
    "AIR_FREIGHT_OTHER": "",
    "OCEAN_FREIGHT_JAPAN": "",
    "OCEAN_FREIGHT_OTHER": "",
    "CUSTOM_BROKER_SERVICES": "",
    "FREIGHT_LOCAL": "",
    "CUSTOMS_DUTY": "",
    "OTHERS": "",
}

# Display label for each charge-type row, in worksheet order.
CHARGE_ROWS: list[tuple[str, str]] = [
    ("AIR_FREIGHT_JAPAN", "AIR FREIGHT JAPAN"),
    ("AIR_FREIGHT_OTHER", "AIR FREIGHT (other than JAPAN)"),
    ("OCEAN_FREIGHT_JAPAN", "OCEAN FREIGHT JAPAN"),
    ("OCEAN_FREIGHT_OTHER", "OCEAN FREIGHT (other than JAPAN)"),
    ("CUSTOM_BROKER_SERVICES", "CUSTOM BROKER SERVICES"),
    ("FREIGHT_LOCAL", "FREIGHT LOCAL"),
    ("CUSTOMS_DUTY", "CUSTOMS DUTY"),
    ("OTHERS", "Others"),
]

# Cost-center columns on the per-vendor sheet (header row). Analyst distributes
# each charge amount across these.
COST_CENTERS: list[str] = [
    "13426", "13483", "13484", "13485", "13486", "13487", "13488", "13489", "13553",
]

# Battery-chemistry rows for the allocation block (label, code).
CHEMISTRY_ROWS: list[tuple[str, str]] = [
    ("MTY-Pack Assbly", "M1394"),
    ("NI-CD OEM", "M3519"),
    ("Li-ION OEM Pris", "M3520"),
    ("LI-ION OEM CYLINDER", "M3521"),
    ("NI-MH OEM", "M3522"),
    ("POLYMER OEM", "M3523"),
    ("LITHIUM OEM", "M3524"),
    ("BIG BATTERY", "M3525 / K3525"),
    ("SE-Shelf & PMI (MS)", "M3559 / K3559"),
]

# Keyword -> charge-type classification for mapping extracted charge descriptions.
# Lowercased substring match, first hit wins (order matters).
CHARGE_KEYWORDS: list[tuple[str, str]] = [
    ("air freight", "AIR_FREIGHT_OTHER"),   # JAPAN refined by origin in classify_charge
    ("air ", "AIR_FREIGHT_OTHER"),
    ("ocean freight", "OCEAN_FREIGHT_OTHER"),
    ("ocean", "OCEAN_FREIGHT_OTHER"),
    ("brokerage", "CUSTOM_BROKER_SERVICES"),
    ("broker", "CUSTOM_BROKER_SERVICES"),
    ("customs clearance", "CUSTOM_BROKER_SERVICES"),
    ("duty", "CUSTOMS_DUTY"),
    ("customs duty", "CUSTOMS_DUTY"),
    ("thc", "FREIGHT_LOCAL"),
    ("terminal handling", "FREIGHT_LOCAL"),
    ("drayage", "FREIGHT_LOCAL"),
    ("chassis", "FREIGHT_LOCAL"),
    ("delivery", "FREIGHT_LOCAL"),
    ("documentation", "FREIGHT_LOCAL"),
    ("doc fee", "FREIGHT_LOCAL"),
    ("baf", "FREIGHT_LOCAL"),
    ("fuel", "FREIGHT_LOCAL"),
    ("security", "FREIGHT_LOCAL"),
    ("isps", "FREIGHT_LOCAL"),
]
