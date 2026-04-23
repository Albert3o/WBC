import socket

# Listen on all network interfaces
UDP_IP = "0.0.0.0" 
# Must match the port defined in the Unity C# script
UDP_PORT = 5005    

# Initialize the UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for Quest 3 UDP packets on port {UDP_PORT}...")

try:
    while True:
        # Buffer size is 1024 bytes
        data, addr = sock.recvfrom(1024) 
        # Decode and print the incoming joystick data
        print(f"Received from {addr}: {data.decode('utf-8')}")
except KeyboardInterrupt:
    print("\nTest stopped by user.")
    sock.close()