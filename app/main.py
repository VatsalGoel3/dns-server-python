import socket
import struct


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("127.0.0.1", 2053))
    
    while True:
        try:
            buf, source = udp_socket.recvfrom(512)
    
            # Building dns header structure
            # ID assigned to query packets
            packet_id = 1234

            # Header Flags            
            qr = 1
            opcode = 0
            aa = 0
            tc = 0
            rd = 0
            ra = 0
            z = 0
            rcode = 0

            flags = (qr << 15) | (opcode << 11) | (aa < 10) | (tc << 9) | (rd << 8) | (ra << 7) | (z << 4) | rcode

            # Questions and records section
            qdcount = 0
            ancount = 0
            nscount = 0
            arcount = 0

            response = struct.pack("HHHHHH!", packet_id, flags, qdcount, ancount, nscount, arcount)
    
            udp_socket.sendto(response, source)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break


if __name__ == "__main__":
    main()
