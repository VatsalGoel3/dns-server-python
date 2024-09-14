import socket
import struct

def extract_domain_name(query):
    # Your existing code
    domain_parts = []
    i = 12
    while True:
        if i >= len(query):
            print("Error: Reached end of query while parsing domain name.")
            return ''
        length = query[i]
        if length == 0:
            break
        i += 1
        domain_parts.append(query[i:i + length].decode('ascii'))
        i += length
    return '.'.join(domain_parts)

def encode_domain_name(domain_name):
    # Your existing code
    parts = domain_name.split('.')
    encoded_name = b''
    for part in parts:
        encoded_name += bytes([len(part)]) + part.encode('ascii')
    encoded_name += b'\x00'
    return encoded_name

def build_dns_response(query):
    # Your existing code
    domain_name = extract_domain_name(query)
    print(f"Received query for the domain: {domain_name}")

    encoded_name = encode_domain_name(domain_name)

    # Building DNS header structure
    packet_id = struct.unpack("!H", query[:2])[0]  # Extract packet ID from query
    query_flags = struct.unpack("!H", query[2:4])[0]
    rd = (query_flags >> 8) & 1  # Recursion Desired flag from query

    # Header Flags
    qr = 1
    opcode = 0
    aa = 0
    tc = 0
    ra = 0
    z = 0
    rcode = 0

    flags = (qr << 15) | (opcode << 11) | (aa << 10) | \
            (tc << 9) | (rd << 8) | (ra << 7) | (z << 4) | rcode

    # Questions and records section
    qdcount = 1
    ancount = 0
    nscount = 0
    arcount = 0

    header = struct.pack("!HHHHHH", packet_id, flags, qdcount, ancount, nscount, arcount)

    # Constructing question section
    # Type = 1 (A record), Class = 1 (IN class)
    question = encoded_name + struct.pack("!HH", 1, 1)

    response = header + question
    return response

def run_dns_server():
    print("DNS server is running...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("127.0.0.1", 2053))

    while True:
        try:
            query, source = udp_socket.recvfrom(512)
            print(f"Received packet from {source}")

            response = build_dns_response(query)
            udp_socket.sendto(response, source)
        except Exception as e:
            print(f"Error receiving data: {e}")
            continue

if __name__ == "__main__":
    run_dns_server()
