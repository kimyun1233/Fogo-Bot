import requests, base58, base64, time, datetime
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from spl.token.constants import TOKEN_PROGRAM_ID, WRAPPED_SOL_MINT
from solana.system_program import create_account, CreateAccountParams
from spl.token.instructions import (
    initialize_account,
    InitializeAccountParams,
    transfer_checked,
    TransferCheckedParams,
    close_account,
    CloseAccountParams
)

requests.packages.urllib3.disable_warnings()

RPC_URL = "https://testnet.fogo.io/"
EXPLORER = "https://fogoscan.com/tx/"

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_separator():
    print("-" * 60)

def print_info(label, value):
    print(f"  {label:<25}: {value}")

def print_success(message):
    print(f"\n✅ {message}")

def print_error(message):
    print(f"\n❌ {message}")

def print_warning(message):
    print(f"\n⚠️  {message}")

def rpc_request(method, params=None):
    if params is None:
        params = []
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    res = requests.post(RPC_URL, json=payload, verify=False)
    res.raise_for_status()
    return res.json()

def get_min_rent_exempt_for_token_account():
    size = 165
    resp = rpc_request("getMinimumBalanceForRentExemption", [size])
    return int(resp["result"])

def get_latest_blockhash():
    r = rpc_request("getLatestBlockhash", [{"commitment": "finalized"}])
    return r["result"]["value"]["blockhash"]

def get_fogo_balance(pubkey: str) -> int:
    resp = rpc_request("getBalance", [pubkey, {"commitment": "finalized"}])
    return int(resp["result"]["value"])

def get_spl_fogo_balance(owner: str) -> int:
    resp = rpc_request(
        "getTokenAccountsByOwner",
        [owner, {"mint": str(WRAPPED_SOL_MINT)}, {"encoding": "jsonParsed"}],
    )
    accounts = resp.get("result", {}).get("value", [])
    total = 0
    for ta in accounts:
        amt = int(ta["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
        total += amt
    return total

def send_raw_transaction(tx_bytes_b64):
    return rpc_request(
        "sendTransaction",
        [
            tx_bytes_b64,
            {"skipPreflight": False, "preflightCommitment": "finalized", "encoding": "base64"},
        ],
    )

def check_balance(private_key: str):
    print_header("CURRENT BALANCES")
    secret_bytes = base58.b58decode(private_key)
    wallet = Keypair.from_secret_key(secret_bytes)
    owner = wallet.public_key
    print_info("Wallet Address", str(owner))
    print_separator()
    fogo_balance = get_fogo_balance(str(owner))
    spl_fogo_balance = get_spl_fogo_balance(str(owner))
    print_info("FOGO Balance", f"{fogo_balance/1e9:.9f} FOGO")
    print_info("SPL FOGO Balance", f"{spl_fogo_balance/1e9:.9f} SPL FOGO")
    print_separator()

def auto_mode(private_key: str, amount: float, delay: int = 15, max_loops: int = 0):
    secret_bytes = base58.b58decode(private_key)
    wallet = Keypair.from_secret_key(secret_bytes)
    owner = wallet.public_key
    loop_count = 0

    while True:
        try:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            fogo_balance = get_fogo_balance(str(owner))
            spl_balance = get_spl_fogo_balance(str(owner))
            need_lamports = int(amount * 1e9)

            if fogo_balance >= need_lamports:
                print_header(f"[{now}] AUTO MODE: WRAP")
                wrap_fogo(private_key, amount)
            else:
                print_warning(f"[{now}] Skipping WRAP, not enough FOGO balance.")

            time.sleep(delay)
            now = datetime.datetime.now().strftime("%H:%M:%S")

            if spl_balance >= need_lamports:
                print_header(f"[{now}] AUTO MODE: UNWRAP")
                unwrap_fogo(private_key, amount)
            else:
                print_warning(f"[{now}] Skipping UNWRAP, not enough SPL FOGO balance.")

            time.sleep(delay)
            loop_count += 1

            if max_loops > 0 and loop_count >= max_loops:
                print_success(f"Auto Mode finished after {loop_count} loops.")
                break

        except KeyboardInterrupt:
            print("\n\nExiting Auto Mode...")
            break
        except Exception as e:
            print_error(f"Error in auto mode: {str(e)}")
            time.sleep(delay)

def show_menu():
    print_header("FOGO TOOL - Hasbi")
    print("\nSelect an Option:")
    print("  1. Wrap FOGO to SPL FOGO")
    print("  2. Unwrap SPL FOGO to FOGO")
    print("  3. Check Balances")
    print("  4. Exit")
    print("  5. Auto Mode (Loop Wrap/Unwrap)")
    print_separator()

def main():
    try:
        with open('accounts.txt', 'r') as file:
            private_key = file.read().strip()

        while True:
            show_menu()
            choice = input("Enter Your Choice [1-5] -> ").strip()
            
            if choice == "1":
                amount = float(input("\nEnter Amount of FOGO to Wrap -> "))
                if amount <= 0:
                    print_error("Amount must be greater than 0")
                    continue
                wrap_fogo(private_key, amount)
                
            elif choice == "2":
                amount = float(input("\nEnter Amount of SPL FOGO to Unwrap -> "))
                if amount <= 0:
                    print_error("Amount must be greater than 0")
                    continue
                unwrap_fogo(private_key, amount)
                
            elif choice == "3":
                check_balance(private_key)
                
            elif choice == "4":
                print_header("GOODBYE!")
                break

            elif choice == "5":
                amount = float(input("\nEnter Amount per Transaction -> "))
                delay = int(input("Enter Delay between Transactions (seconds, default 15) -> ") or 15)
                max_loops = int(input("Enter Number of Loops (0 = infinite) -> ") or 0)
                if amount <= 0 or delay <= 0:
                    print_error("Amount and delay must be greater than 0")
                    continue
                auto_mode(private_key, amount, delay, max_loops)
                
            else:
                print_error("Invalid choice! Please select 1-5")
                
            if choice in ["1", "2", "3"]:
                input("\nPress Enter to continue...")
                
    except ValueError:
        print_error("Invalid input! Please enter a valid number.")
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except FileNotFoundError:
        print("\n\nFile 'accounts.txt' Not Found.")
        return
    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
