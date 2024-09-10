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
            print(f"Received packet from {source}")
    
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

            #Printing the header for debugging
            #print(f"Flags: {flags} ({type(flags)})")
            #print(f"QDCOUNT: {qdcount} ({type(qdcount)})")
            #print(f"ANCOUNT: {ancount} ({type(ancount)})")
            #print(f"NSCOUNT: {nscount} ({type(nscount)})")
            #print(f"ARCOUNT: {arcount} ({type(arcount)})")

            try:
                response = struct.pack("!HHHHHH", packet_id, flags, qdcount, ancount, nscount, arcount)
            except struct.error as e:
                print(f"Struct packing error: {e}")
                continue  # Move on to the next iteration without crashing

    
            udp_socket.sendto(response, source)

        except Exception as e:
            print(f"Error receiving data: {e}")
            break


if __name__ == "__main__":
    main()
