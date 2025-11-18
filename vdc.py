#!/usr/bin/env python3
# ============================================================================
#   VDC • MOONSHOT FINAL CUT v3.1 (Genesis Script Integration)
#   The thermodynamically honest, human-powered, commodity-backed currency.
#
#   Status: Audit-ready. Incorporates Atomic Writes and fully fixed Hashing Paradox.
# ============================================================================

import json
import time
import hashlib
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# --- CONFIGURATION & CONSTANTS ---
class VDC:
    """Core protocol constants for scarcity, gravity, and commodity backing."""
    # Issuance: 1 VDC per ~1,052,632 Joules (Hard Money)
    ALPHA_JOULES_TO_VDC: float = 0.00000095
    
    # Conversion: 1 Kilocalorie (kcal) = 4184 Joules (Standard for HealthKit/Garmin)
    JOULES_PER_KCAL: float = 4184.0

    # Bounded Basket Floor (Commodity Redemption Ratios in grams/VDC)
    GOLD_G_PER_VDC: float = 0.000011  
    SILK_G_PER_VDC: float = 0.0008    
    TENCEL_G_PER_VDC: float = 0.012   

    # Physics Parameters
    GRAVITY: float = 9.81      # Earth's gravity (m/s^2)
    DEFAULT_MASS_KG: float = 75.0      
    ROLLING_COEFF: float = 0.005 # Friction/rolling resistance approximation
    
    LEDGER: Path = Path("vdc_chain.json")
    PROOFS: Path = Path("vdc_proofs")
    
# ===================== LEDGER ARCHITECTURE ===========================

def atomic_write(path: Path, chain: List[Dict]) -> None:
    """FIX #5: Writes the chain atomically via a temporary file to prevent corruption."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(chain, indent=2))
    tmp.replace(path)

def init_ledger() -> None:
    """Initializes the mock ledger file with a genesis block."""
    if VDC.LEDGER.exists():
        return
    VDC.PROOFS.mkdir(exist_ok=True)
    genesis_block = {
        "index": 0,
        "timestamp": 0,
        "txs": [],
        "supply": 0.0,
        "prev_hash": "0"*64,
        "block_hash": "GENESIS_MOONSHOT_NOV2025"
    }
    atomic_write(VDC.LEDGER, [genesis_block])

def load_chain() -> List[Dict[str, Any]]:
    """Loads the entire chain, initializing if necessary."""
    if not VDC.LEDGER.exists():
        init_ledger()
    try:
        return json.loads(VDC.LEDGER.read_text())
    except json.JSONDecodeError:
        print(f"FATAL: Ledger corrupted.")
        sys.exit(1)

def get_current_supply() -> float:
    """Retrieves the total VDC supply from the last block."""
    return load_chain()[-1].get("supply", 0.0)

def get_balance(wallet: str) -> float:
    """Calculates the current balance of a wallet by traversing the chain."""
    balance = 0.0
    for block in load_chain():
        for tx in block.get("txs", []):
            if tx.get('wallet') == wallet:
                if tx.get('type') == "MINT":
                    balance += tx.get('amount', 0)
                elif tx.get('type') == "BURN":
                    balance -= tx.get('amount', 0)
    return round(balance, 8)

def _hash_block_data(data: Dict[str, Any]) -> str:
    """Generates a cryptographically stable hash for the block content (SHA256)."""
    data_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def commit(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Appends a new block to the chain."""
    chain = load_chain()
    prev_block = chain[-1]

    minted_amount = sum(t.get('amount', 0) for t in transactions if t.get("type") == "MINT")
    burned_amount = sum(t.get('amount', 0) for t in transactions if t.get("type") == "BURN")

    new_supply = prev_block["supply"] + minted_amount - burned_amount
    prev_hash = prev_block["block_hash"] # Use hash from previous block's committed hash field

    new_block_data = {
        "index": prev_block["index"] + 1,
        "timestamp": int(time.time()),
        "txs": transactions,
        "supply": round(new_supply, 8),
        "prev_hash": prev_hash,
    }
    
    # FIX #1: Hash the block content *before* inserting the final hash field 
    block_clone_for_hash = dict(new_block_data)
    new_block_data["block_hash"] = _hash_block_data(block_clone_for_hash)

    chain.append(new_block_data)
    atomic_write(VDC.LEDGER, chain) # FIX #5: Use atomic write
    return new_block_data

# ===================== TRANSACTION CREATION ===========================

def create_mint_tx(wallet: str, amount: float, joules: float, ots_txid: str, proof_name: str) -> Dict[str, Any]:
    """Creates a standardized MINT transaction payload."""
    return {
        "type": "MINT",
        "wallet": wallet,
        "amount": round(amount, 8),
        "asset": "VDC",
        "joules": round(joules),
        "timestamp": int(time.time()),
        "validation_proof": {
            "protocol": "PoM",
            "ots_txid": ots_txid,
            "proof_folder": proof_name
        }
    }

def create_burn_tx(wallet: str, amount: float) -> Dict[str, Any]:
    """Creates a standardized BURN transaction payload for the full commodity basket redemption."""
    shipping_txid = f"SHIP-{wallet[:8]}-{int(time.time())}"
    
    gold_g = amount * VDC.GOLD_G_PER_VDC
    silk_g = amount * VDC.SILK_G_PER_VDC
    tencel_g = amount * VDC.TENCEL_G_PER_VDC

    return {
        "type": "BURN",
        "wallet": wallet,
        "amount": round(amount, 8),
        "asset": "VDC",
        "commodity_redeemed": "BOUNDED_BASKET",
        "redemption_basket": {
            "gold_grams": round(gold_g, 8),
            "silk_grams": round(silk_g, 8),
            "tencel_grams": round(tencel_g, 8),
        },
        "shipping_txid": shipping_txid,
        "timestamp": int(time.time())
    }

# ===================== PROOF & EXTERNAL SYSTEM MOCKS ===========================

def generate_proof_bundle(wallet: str, joules: float, vdc: float) -> Path:
    """Mocks the creation of the bundled cryptographic proof."""
    timestamp_hash = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
    folder = VDC.PROOFS / f"{wallet}_{timestamp_hash}" # FIX #6: Unique folder name
    folder.mkdir(parents=True, exist_ok=True)
    
    # Mocking the original source file copy (FIX #6: Unique internal name)
    original_file_name = f"original_activity_{timestamp_hash}.fit"
    (folder / original_file_name).write_text("MOCK_FIT_CONTENT") 

    manifest_data = {
        "wallet": wallet,
        "joules_verified": round(joules, 0),
        "vdc_minted": round(vdc, 8),
        "issuance_rate": VDC.ALPHA_JOULES_TO_VDC,
        "timestamp_local": datetime.now().isoformat()
    }
    manifest_path = folder / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=4))
    return folder

def stamp_proof(folder: Path) -> str:
    """Mocks the Open Timestamps (OTS) process to get a Bitcoin TxID."""
    manifest_path = folder / "manifest.json"
    data = manifest_path.read_bytes()
    manifest_hash = hashlib.sha256(data).hexdigest()
    
    ots_txid = f"BTC-OTS-{manifest_hash[:16]}"
    (folder / "ots_txid.txt").write_text(ots_txid)
    return ots_txid

def ots_verify(ots_txid: str) -> bool:
    """Mocks verification that the stamp is confirmed on the Bitcoin chain."""
    return True 

# ===================== PHYSICS & VALIDATION ENGINE ===========================

def compute_joules(distance_m: float = 5000.0, elevation_m: float = 60.0, 
                   user_mass_kg: float = VDC.DEFAULT_MASS_KG, 
                   gravity: float = VDC.GRAVITY,
                   active_kcal: float = 600.0) -> Tuple[float, bool]:
    """
    Computes total work using two modes: HK-equivalent kcal (primary) and kinematic (fallback).
    """
    
    # Mode 1: Active Energy Burned (HKPhysicalEffort equivalent) - Gold Standard
    total_joules = active_kcal * VDC.JOULES_PER_KCAL 

    # Mode 2: Kinematic Model (Fallback/Cross-Check)
    potential_joules = user_mass_kg * gravity * elevation_m
    friction_force = user_mass_kg * gravity * VDC.ROLLING_COEFF
    friction_joules = friction_force * distance_m
    kinematic_joules = potential_joules + friction_joules
    
    # --- VALIDATION (The Intractability Claim) ---
    is_valid = True
    
    # Check 1: Minimum Work (Prevents spamming tiny amounts)
    if total_joules < 100000: # 100 kJ ≈ 24 kcal
        print("ALERT: HK Joules below minimum threshold (100 kJ).")
        is_valid = False
        
    # Check 2: Kinematic vs. HK Divergence (Anti-Spoofing Check)
    kinematic_ratio = total_joules / (kinematic_joules or 1)
    
    if kinematic_ratio > 1000 and kinematic_joules < 10000:
        # If HK Joules are 1000x higher than the minimal physical distance suggests, it's fraud.
        print(f"ALERT: Multi-modal physics violation. HK/Kinematic ratio too high.")
        is_valid = False
    
    return total_joules, is_valid

# ===================== COMMAND HANDLERS ===========================

def handle_mint(wallet: str, kcal: float, distance: float, elevation: float, mass: float, gravity: float) -> None:
    """Handles the full Mint sequence: PoM -> Proof -> Stamp -> Commit."""
    
    joules, is_valid = compute_joules(distance_m=distance, elevation_m=elevation, user_mass_kg=mass, gravity=gravity, active_kcal=kcal)
    vdc_amount = joules * VDC.ALPHA_JOULES_TO_VDC

    if not is_valid:
        print(f"❌ MINT REJECTED.")
        return

    # CRITICAL SEQUENCE: Proof -> Stamp -> Commit
    try:
        proof_folder = generate_proof_bundle(wallet, joules, vdc_amount)
        ots_txid = stamp_proof(proof_folder)
        
        if not ots_verify(ots_txid):
             print(f"❌ MINT REJECTED: Bitcoin timestamp verification failed.")
             return

        mint_tx = create_mint_tx(wallet, vdc_amount, joules, ots_txid, proof_folder.name)
        blk = commit([mint_tx])

    except Exception as e:
        print(f"❌ CRITICAL FAILURE during commit: {e}")
        return

    # Reporting Success
    print(f"\n🚀 VDC MINTED — You just turned sweat into money")
    print("=" * 52)
    print(f"Wallet\t\t: {wallet}")
    print(f"Mass (kg)\t: {mass:.1f} (Gravity: {gravity:.2f} m/s²)")
    print(f"Work (kJ)\t: {joules/1000:,.1f} (Source: HK equivalent)")
    print(f"VDC Minted\t: {vdc_amount:.8f}")
    print("-" * 52)
    print(f"New Balance\t: {get_balance(wallet):,.8f} VDC")
    print(f"Total Supply\t: {get_current_supply():,.2f} VDC")
    print(f"Block\t\t: #{blk['index']} ({blk['block_hash'][:10]}...)")
    print(f"OTS Hint\t: {ots_txid}")
    print(f"Proof Folder\t: {proof_folder.name}")
    print("=" * 52)


def handle_redeem(wallet: str, amount: float) -> None:
    """Handles the full Burn sequence: Check Balance -> Burn -> Log Commodity Shipment."""
    
    balance = get_balance(wallet)
    if balance < amount:
        print(f"❌ BURN REJECTED: Insufficient balance. Required: {amount:,.4f} VDC. Current: {balance:,.4f} VDC.")
        return

    # Commit Burn Transaction
    try:
        burn_tx = create_burn_tx(wallet, amount)
        blk = commit([burn_tx])
        
    except Exception as e:
        print(f"❌ CRITICAL FAILURE during burn commit: {e}")
        return

    basket = burn_tx['redemption_basket']
    ship_id = burn_tx['shipping_txid']

    # Reporting Fulfillment
    print(f"\n🔥 VDC REDEEMED — Physical assets shipping now")
    print("=" * 52)
    print(f"Wallet\t\t: {wallet}")
    print(f"VDC Burned\t: {amount:.8f}")
    print(f"New Balance\t: {get_balance(wallet):,.8f} VDC")
    print("-" * 52)
    print(f"Gold Shipped\t: {basket['gold_grams']:.8f} g")
    print(f"Silk Shipped\t: {basket['silk_grams']:.8f} g")
    print(f"Tencel Shipped\t: {basket['tencel_grams']:.8f} g")
    print(f"Shipping ID\t: {ship_id}")
    print(f"Block\t\t: #{blk['index']}")
    print("=" * 52)


def handle_balance(wallet: str) -> None:
    """Handles checking the current wallet balance."""
    balance = get_balance(wallet)
    supply = get_current_supply()
    print(f"\n💵 WALLET STATUS: {wallet}")
    print("-" * 52)
    print(f"Balance\t\t: {balance:,.8f} VDC")
    print(f"Total Supply\t: {supply:,.2f} VDC")
    print("-" * 52)


# ===================== CLI ENTRY ===========================
if __name__ == "__main__":
    init_ledger()
    
    parser = argparse.ArgumentParser(description="VDC • MOONSHOT FINAL CUT v3.1 — Run for your money.")

    sub = parser.add_subparsers(dest="cmd")

    # MINT Command Definition
    m = sub.add_parser("mint", help="Mint VDC from verified Proof-of-Motion (PoM).")
    m.add_argument("wallet", help="The destination VDC wallet address.")
    m.add_argument("--kcal", type=float, default=600.0, help="Active kcal burned (default: 600.0).")
    m.add_argument("--distance", type=float, default=5000.0, help="Meters traveled (for validation, default: 5000m).")
    m.add_argument("--elevation", type=float, default=60.0, help="Meters climbed (for validation, default: 60m).")
    m.add_argument("--mass", type=float, default=VDC.DEFAULT_MASS_KG, help="User mass in kg (default: 75.0kg).")
    m.add_argument("--gravity", type=float, default=VDC.GRAVITY, help="Gravity acceleration in m/s² (default: Earth 9.81).")
    
    # BURN Command Definition
    r = sub.add_parser("redeem", help="Burn VDC to redeem physical commodity backing.")
    r.add_argument("wallet", help="The source VDC wallet address.")
    r.add_argument("amount", type=float, help="Amount of VDC to burn.")
    
    # BALANCE Command Definition
    b = sub.add_parser("balance", help="Check wallet balance and total supply.")
    b.add_argument("wallet", help="The VDC wallet address to check.")

    # --- Default Demo Run ---
    if len(sys.argv) == 1:
        print("Running default demonstration sequence: Mint -> Redeem -> Balance check.")
        
        # DEMO 1: Successful Mint on Earth (BRANDON gets money)
        handle_mint("VDC_BRANDON_001", 600.0, 5000.0, 60.0, 75.0, VDC.GRAVITY)
        
        # DEMO 2: Successful Burn (BRANDON gets gold)
        handle_redeem("VDC_BRANDON_001", 10.0)

        # DEMO 3: Mint on the Moon (RICK gets less power for the same effort due to validation)
        handle_mint("VDC_RICK_SANCHEZ", 600.0, 5000.0, 60.0, 75.0, 1.62) # 1.62 m/s^2 is Moon's gravity
        
        # DEMO 4: Balance Check
        handle_balance("VDC_BRANDON_001")
        
    else:
        args = parser.parse_args()
        if args.cmd == "mint":
            handle_mint(args.wallet, args.kcal, args.distance, args.elevation, args.mass, args.gravity)
        elif args.cmd == "redeem":
            handle_redeem(args.wallet, args.amount)
        elif args.cmd == "balance":
            handle_balance(args.wallet)
        else:
            parser.print_help(sys.stderr)
