def auto_mode(private_key: str, amount: float, delay: int = 10):
    """
    Jalankan wrap -> unwrap terus menerus.
    amount: jumlah FOGO/SPL FOGO per transaksi
    delay: jeda antar transaksi (detik)
    """
    while True:
        try:
            print_header("AUTO MODE: WRAP")
            wrap_fogo(private_key, amount)

            time.sleep(delay)

            print_header("AUTO MODE: UNWRAP")
            unwrap_fogo(private_key, amount)

            time.sleep(delay)

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
elif choice == "5":
    amount = float(input("\nEnter Amount per Transaction -> "))
    delay = int(input("Enter Delay between Transactions (seconds) -> "))
    if amount <= 0 or delay <= 0:
        print_error("Amount and delay must be greater than 0")
        continue
    auto_mode(private_key, amount, delay)
============================================================
  FOGO TOOL - Hasbi
============================================================

Select an Option:
  1. Wrap FOGO to SPL FOGO
  2. Unwrap SPL FOGO to FOGO
  3. Check Balances
  4. Exit
  5. Auto Mode (Loop Wrap/Unwrap)
------------------------------------------------------------
