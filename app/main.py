import socket
import struct
import logging

from domain_mappings import domain_ip_mapping

# Setting up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_domain_name(query):
    # Your existing code
    domain_parts = []
    i = 12
    while True:
        if i >= len(query):
            logging.error("Reached end of query while parasing domain name.")
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

def forward_query(query):
    upstream_server = ('8.8.8.8', 53) # Google DNS server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.timeout(5) # Timeout incase of Upstream server not responding

    try:
        sock.sendto(upstream_server, query)
        response, _ = sock.recvfrom(512)
        return response
    except socket.timeout:
        logging.error("Timeout when contacting Upstream DNS Server.")
        return None
    finally:
        sock.close

def build_dns_response(query):    
    domain_name = extract_domain_name(query)
    domain_name = domain_name.lower() # Ensure domain names are handled in a case-sensitive manner
    logging.debug(f"Received query for the domain name: {domain_name}")

    encoded_name = encode_domain_name(domain_name)

    # Building DNS header structure
    packet_id = struct.unpack("!H", query[:2])[0]  # Extract packet ID from query
    query_flags = struct.unpack("!H", query[2:4])[0]
    rd = (query_flags >> 8) & 1  # Recursion Desired flag from query
    logging.debug(f"Packet ID: {packet_id}, Recursion Desired: {rd}")

    # Header Flags
    qr = 1 # Response
    opcode = 0
    aa = 1 # Authoritative Answer
    tc = 0
    ra = 0 # Recursion not available
    z = 0
    rcode = 0 # No error by default 

    flags = (qr << 15) | (opcode << 11) | (aa << 10) | (tc << 9) | (rd << 8) | (ra << 7) | (z << 4) | rcode

    # Questions and records section
    qdcount = 1
    ancount = 1 
    nscount = 0
    arcount = 0

    # Constructing question section
    # Type = 1 (A record), Class = 1 (IN class)
    question = encoded_name + struct.pack("!HH", 1, 1)

    # Lookup for IP address
    ip_address = domain_ip_mapping.get(domain_name)
    if ip_address is None:
        logging.warning(f"Domain {domain_name} not found in mapping.")
        ancount = 0
        rcode = 3 # Name error
        flags = (flags & 0xFFF0) | rcode # Update rcode in flags
        header = struct.pack("!HHHHHH", packet_id, flags, qdcount, ancount, nscount, arcount)
        response = header + question
        logging.debug(f"Response header with RCODE = 3 for the domain {domain_name}.")
        return response
    else:
        ancount = 1
        header = struct.pack("!HHHHHH", packet_id, flags, qdcount, ancount, nscount, arcount)
        logging.debug(f"Domain {domain_name} found. IP Address: {ip_address}")

    # Constructing answer section
    try:
        answer_name = b'\xc0\x0c' # Pointer to offset 12 in the message 
        # Answer section body
        answer_type = struct.pack("!H", 1) # Type A
        answer_class = struct.pack("!H", 1) # Class IN
        answer_ttl = struct.pack("!I", 300) # TTL
        answer_rdlength = struct.pack("!H", 4) # Length of RDATA
        answer_rdata = socket.inet_aton(ip_address)

        # Building answer section
        answer_section = (answer_name + answer_type + answer_class + answer_ttl + answer_rdlength + answer_rdata)

        response = header + question + answer_section
        logging.debug(f"Response with Answer section sent for the domain {domain_name}")
        return response
    except OSError as e:
        logging.error(f"Invalid IP address: {ip_address} for domain {domain_name} : {e}") 
        # Error case
        ancount = 0
        rcode = 3 # Name error
        flags = (flags & 0xFFF0) | rcode # Update rcode in flags
        header = struct.pack("!HHHHHH", packet_id, flags, qdcount, ancount, nscount, arcount)
        response = header + question
        logging.debug(f"Respoinse with RCODE = 3 sent due to Invalid IP for domain {domain_name}.")
        return response 

def run_dns_server():
    logging.info("DNS server is starting...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.bind(("127.0.0.1", 2053))
        logging.info("DNS server is running on 127.0.0.1:2053")
    except OSError as e:
        logging.error(f"Failed to bind socket : {e}")

    while True:
        try:
            query, source = udp_socket.recvfrom(512)
            logging.debug(f"Received packet from {source}")

            response = build_dns_response(query)
            udp_socket.sendto(response, source)
            logging.debug(f"Sent response to {source}")
        except Exception as e:
            logging.error(f"Error processing request from {source} : {e}")
            continue

if __name__ == "__main__":
    run_dns_server()
