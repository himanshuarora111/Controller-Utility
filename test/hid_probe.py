import hid


def main():
    print("Connected HID devices:\n")

    devices = hid.enumerate()

    for index, device in enumerate(devices, start=1):
        vendor_id = device.get("vendor_id")
        product_id = device.get("product_id")
        manufacturer = device.get("manufacturer_string")
        product = device.get("product_string")
        serial = device.get("serial_number")
        usage_page = device.get("usage_page")
        usage = device.get("usage")
        interface_number = device.get("interface_number")
        path = device.get("path")

        print("=" * 80)
        print(f"Device #{index}")
        print(f"VID:PID         = {vendor_id:04X}:{product_id:04X}")
        print(f"Manufacturer    = {manufacturer}")
        print(f"Product         = {product}")
        print(f"Serial          = {serial}")
        print(f"Usage Page      = {usage_page}")
        print(f"Usage           = {usage}")
        print(f"Interface       = {interface_number}")
        print(f"Path            = {path}")

        try:
            d = hid.device()
            d.open_path(path)
            d.set_nonblocking(True)
            print("Open test       = OK")
            d.close()
        except Exception as exc:
            print(f"Open test       = FAILED: {exc}")

    print("\nDone.")


if __name__ == "__main__":
    main()
