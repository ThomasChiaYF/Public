




import os
import subprocess
import platform
import ipaddress

def numeric_to_dotted_decimal(numeric_mask):
    """Convert a numeric subnet mask to dotted-decimal format."""
    mask = (numeric_mask >> 24 & 0xFF, 
            numeric_mask >> 16 & 0xFF, 
            numeric_mask >> 8 & 0xFF, 
            numeric_mask & 0xFF)
    return '.'.join(map(str, mask))

def get_subnet_mask_linux(iface):
    try:
        # Get subnet mask using ip command
        subnet_info = subprocess.check_output(f"ip addr show {iface}", shell=True).decode()
        for line in subnet_info.splitlines():
            if "inet " in line:
                mask_cidr = line.split()[1].split('/')[1]  # Get the CIDR part
                mask = str(ipaddress.IPv4Network(f'0.0.0.0/{mask_cidr}', strict=False).netmask)  # Convert to subnet mask
                return mask
    except subprocess.CalledProcessError:
        pass
    return None

def get_subnet_mask_mac(iface):
    try:
        # Get subnet mask using ifconfig command
        iface_info = subprocess.check_output(f"ifconfig {iface}", shell=True).decode()
        for line in iface_info.splitlines():
            if "netmask " in line:
                # Convert the hexadecimal netmask to decimal format
                hex_mask = line.split()[3]
                decimal_mask = int(hex_mask, 16)
                dotted_decimal_mask = numeric_to_dotted_decimal(decimal_mask)
                return dotted_decimal_mask
    except subprocess.CalledProcessError:
        pass
    return None

def check_physical_layer():
    print("\nChecking Physical Layer (Layer 1)...")
    active_interfaces = []

    # Determine the operating system
    if platform.system() == 'Linux':
        command = "ip -brief addr"
    elif platform.system() == 'Darwin':  # macOS
        command = "ifconfig"
    else:
        print("Physical layer check is not supported on this OS.")
        return []

    try:
        # Use the appropriate command based on the OS
        result = subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode()
        
        print("Detected Network Interfaces:")
        if platform.system() == 'Linux':
            # Parse the output of the ip command
            for line in result.splitlines():
                parts = line.split()
                iface = parts[0]
                status = parts[1]
                ip_address = parts[2] if len(parts) > 2 else None

                if status == "UP" and ip_address:  # Only consider interfaces that are UP and have an IP address
                    mask = get_subnet_mask_linux(iface)
                    if mask:
                        active_interfaces.append((iface, ip_address, mask))
                        print(f"Interface {iface} is active with IP address: {ip_address}, Subnet Mask: {mask}")

        elif platform.system() == 'Darwin':  # macOS
            interfaces = [line.split(':')[0] for line in result.split('\n') if "flags=" in line]
            for iface in interfaces:
                try:
                    iface_status = subprocess.check_output(f"ifconfig {iface}", shell=True, stderr=subprocess.DEVNULL).decode()
                    if "status: active" in iface_status or "RUNNING" in iface_status:
                        # Extract the IP address and subnet mask from the ifconfig output
                        ip_address = None
                        mask = get_subnet_mask_mac(iface)

                        for line in iface_status.splitlines():
                            if "inet " in line and "inet6" not in line:
                                ip_address = line.split()[1]

                        # Only add to the list if an IP address and subnet mask are found
                        if ip_address and mask:
                            active_interfaces.append((iface, ip_address, mask))
                            print(f"Interface {iface} is active with IP address: {ip_address}, Subnet Mask: {mask}")
                
                except subprocess.CalledProcessError:
                    pass  # Skip interfaces that can't be checked

        # Get the default gateway
        gateway_command = "ip route show" if platform.system() == 'Linux' else "netstat -rn"
        gateway_result = subprocess.check_output(gateway_command, shell=True, stderr=subprocess.DEVNULL).decode()

        # Parse gateway info
        print("\nDefault Gateway:")
        if platform.system() == 'Linux':
            for line in gateway_result.splitlines():
                if "default" in line:
                    parts = line.split()
                    print(f"Default Gateway: {parts[2]}")  # The gateway IP address is usually the third part
                    break
        elif platform.system() == 'Darwin':
            for line in gateway_result.splitlines():
                if "default" in line:
                    parts = line.split()
                    print(f"Default Gateway: {parts[1]}")  # The gateway IP address is usually the second part
                    break

    except subprocess.CalledProcessError as e:
        print(f"Error checking interfaces: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    if not active_interfaces:
        print("No active interfaces with an IP address detected.")
    return active_interfaces

def main():
    print("Starting Physical Layer Troubleshooting...\n")
    active_interfaces = check_physical_layer()
    print("\nPhysical Layer Troubleshooting Complete.")

if __name__ == "__main__":
    main()