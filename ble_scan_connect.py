from bluepy.btle import (
    Scanner,
    Peripheral,
    UUID,
    DefaultDelegate,
    BTLEException
)

SERVICE_UUID = "fff0"
CHAR_UUID = "fff1"
CCCD_UUID = "2902"

SCAN_TIME = 10.0


# --------------------------------------------------
# Receive Notification / Indication
# --------------------------------------------------
class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        print("\n===================================")
        print("Received Notification / Indication!")
        print(f"Handle: {cHandle}")
        print(f"Raw data: {data}")
        print(f"Hex: {data.hex()}")

        try:
            print(f"ASCII: {data.decode()}")
        except UnicodeDecodeError:
            pass

        print("===================================")


# --------------------------------------------------
# Scan BLE devices
# --------------------------------------------------
print(f"Scanning for BLE devices for {SCAN_TIME} seconds...")

scanner = Scanner()
devices = scanner.scan(SCAN_TIME)

targets = []

print("\n=== Scan Result ===")

for i, dev in enumerate(devices):

    targets.append((dev.addr, dev.addrType))

    print(
        f"\n[{i}] "
        f"{dev.addr} "
        f"type={dev.addrType} "
        f"RSSI={dev.rssi}"
    )

    # Show advertising data
    for adtype, desc, value in dev.getScanData():
        print(f"    {desc}: {value}")


# --------------------------------------------------
# Let user choose phone
# --------------------------------------------------
print("\n===================================")

number = int(input("Enter device number: "))

target_addr, target_type = targets[number]

print("\n===================================")
print(f"Connecting to {target_addr}")
print(f"Address type: {target_type}")
print("===================================")


dev = None

try:

    # --------------------------------------------------
    # Connect
    # --------------------------------------------------
    dev = Peripheral(target_addr, target_type)

    dev.setDelegate(MyDelegate())

    print("Connected!")


    # --------------------------------------------------
    # Find Service FFF0
    # --------------------------------------------------
    print("\nSearching for Service FFF0...")

    service = dev.getServiceByUUID(
        UUID(0xfff0)
    )

    print("Found Service FFF0!")
    print(
        f"Handle range: "
        f"{service.hndStart} - {service.hndEnd}"
    )


    # --------------------------------------------------
    # Find Characteristic FFF1
    # --------------------------------------------------
    print("\nSearching for Characteristic FFF1...")

    chars = service.getCharacteristics(
        UUID(0xfff1)
    )

    if len(chars) == 0:
        raise RuntimeError(
            "Characteristic FFF1 not found."
        )

    ch = chars[0]

    print("Found Characteristic FFF1!")
    print(f"UUID: {ch.uuid}")
    print(f"Value handle: {ch.getHandle()}")
    print(
        f"Properties: "
        f"{ch.propertiesToString()}"
    )


    # --------------------------------------------------
    # Find CCCD (UUID 2902)
    # --------------------------------------------------
    print("\nSearching for CCCD (2902)...")

    descriptors = ch.getDescriptors()

    cccd = None

    for desc in descriptors:

        print(
            f"Descriptor: {desc.uuid} "
            f"handle={desc.handle}"
        )

        uuid_string = str(desc.uuid).lower()

        if (
            uuid_string == "2902"
            or uuid_string.startswith("00002902")
        ):
            cccd = desc


    if cccd is None:
        raise RuntimeError(
            "CCCD 0x2902 not found. "
            "Make sure FFF1 supports "
            "Notify or Indicate."
        )


    print("\nCCCD FOUND!")
    print(f"CCCD UUID: {cccd.uuid}")
    print(f"CCCD handle: {cccd.handle}")


    # --------------------------------------------------
    # Write 0x0002 to CCCD
    #
    # CCCD is a 16-bit little-endian value:
    #
    # 0x0000 = disable
    # 0x0001 = notification
    # 0x0002 = indication
    #
    # therefore 0x0002 -> bytes 02 00
    # --------------------------------------------------
    print("\nWriting CCCD = 0x0002...")

    dev.writeCharacteristic(
        cccd.handle,
        b"\x02\x00",
        withResponse=True
    )

    print("Write successful!")
    print("Indication ENABLED.")


    # --------------------------------------------------
    # Read CCCD back
    # --------------------------------------------------
    try:

        value = dev.readCharacteristic(
            cccd.handle
        )

        print("\nRead CCCD back:")

        print(
            "Raw bytes:",
            value
        )

        print(
            "Hex:",
            value.hex()
        )

        if value == b"\x02\x00":
            print(
                "CCCD confirmed = 0x0002"
            )
        else:
            print(
                "CCCD value is not 0x0002"
            )

    except BTLEException as e:

        print(
            "\nCould not read CCCD back."
        )

        print(
            "This does not necessarily "
            "mean the write failed."
        )

        print(e)


    # --------------------------------------------------
    # Wait for Indication
    # --------------------------------------------------
    print("\n===================================")
    print("CCCD setup completed.")
    print("Waiting for indication...")
    print("Change/send the FFF1 value")
    print("from the phone GATT Server.")
    print("Press Ctrl+C to stop.")
    print("===================================")

    while True:

        # bluepy uses the same callback
        # for notifications and indications
        if dev.waitForNotifications(5.0):
            continue

        print("Waiting...")


except KeyboardInterrupt:

    print("\nStopped by user.")


except BTLEException as e:

    print("\nBLE Error:")
    print(e)


except Exception as e:

    print("\nError:")
    print(e)


finally:

    if dev is not None:

        try:
            dev.disconnect()
            print("\nDisconnected.")

        except:
            pass
