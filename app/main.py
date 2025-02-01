import socket
import struct
import logging

from domain_mappings import domain_ip_mapping
from dns_cache import DNSCache

# Setting up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Add after logging configuration
dns_cache = DNSCache()

def extract_domain_name(query, offset=12, visited_offsets=None):
    if visited_offsets is None:
        visited_offsets = set()
    domain_parts = []
    while True:
        if offset in visited_offsets:
            # Prevent malformed packets to cause loops
            logging.error("Loop detected in domain name compression")
            return [], offset
        visited_offsets.add(offset)

        if offset >= len(query):
            logging.error("Reached end of query while parsing domain name")
            return [], offset
        
        length = query[offset]

        if length == 0:
            offset += 1
            break
        elif(length & 0xC0) == 0xC0:
            # Pointer case
            pointer = struct.unpack("!H", query[offset:offset+2])[0] & 0x3FFF
            offset += 2
            # Recursive call to handle the pointer
            labels,_ = extract_domain_name(query, offset, visited_offsets)
            domain_parts.extend(labels)
            break
        else:
            offset += 1
            label = query[offset:offset+length].decode('ascii')
            domain_parts.append(label)
            offset += length

    return domain_parts, offset

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
    sock.settimeout(5)

    try:
        # Extract domain and query type for caching
        domain_parts, offset = extract_domain_name(query)
        domain_name = '.'.join(domain_parts).lower()
        qtype, _ = struct.unpack("!HH", query[offset:offset+4])

        sock.sendto(query, upstream_server)
        response, _ = sock.recvfrom(512)

        if response:
            # Extract TTL from the answer section
            # Skip header (12 bytes) and question section
            pos = 12 + len(query[12:])
            if len(response) >= pos + 12:  # Minimum answer section size
                # Skip name pointer
                pos += 2
                # Skip type and class
                pos += 4
                ttl = struct.unpack("!I", response[pos:pos+4])[0]
                # Cache the response
                dns_cache.store(domain_name, qtype, response, ttl)

        return response
    except socket.timeout:
        logging.error("Timeout when contacting Upstream DNS Server.")
        return None
    finally:
        sock.close()

def build_dns_response(query):    
    domain_parts, offset = extract_domain_name(query)
    domain_name = '.'.join(domain_parts).lower()
    logging.debug(f"Received query for the domain name: {domain_name}")

    # Extract the query type and class from the question section
    qtype, qclass = struct.unpack("!HH", query[offset:offset+4])
    logging.debug(f"Query Type: {qtype}, Query Class: {qclass}")

    # Get packet ID and flags from query
    packet_id = struct.unpack("!H", query[:2])[0]
    query_flags = struct.unpack("!H", query[2:4])[0]
    rd = (query_flags >> 8) & 1  # Get RD bit from query

    # Check cache first
    cached_response = dns_cache.get(domain_name, qtype)
    if cached_response:
        # Update packet ID and RD bit in cached response
        flags = struct.unpack("!H", cached_response[2:4])[0]
        flags = (flags & 0xFEFF) | (rd << 8)  # Preserve RD bit from query
        return struct.pack("!H", packet_id) + struct.pack("!H", flags) + cached_response[4:]

    encoded_name = encode_domain_name(domain_name)

    # Check local mappings first
    if domain_name in domain_ip_mapping:
        ip_address = domain_ip_mapping[domain_name]
        if ip_address:
            # Fix: Move this block before the error cases
            ancount = 1
            qr = 1
            opcode = (query_flags >> 11) & 0xF
            aa = 1
            tc = 0
            ra = 1
            z = 0
            rcode = 0

            # Use RD from query
            flags = (qr << 15) | (opcode << 11) | (aa << 10) | (tc << 9) | (rd << 8) | (ra << 7) | (z << 4) | rcode
            header = struct.pack("!HHHHHH", packet_id, flags, 1, ancount, 0, 0)

            # Build answer section
            answer_name = b'\xc0\x0c'
            answer_type = struct.pack("!H", qtype)
            answer_class = struct.pack("!H", 1)
            answer_ttl = struct.pack("!I", 300)

            if ':' in ip_address:
                if qtype != 28:  # Not AAAA
                    rcode = 4  # Not Implemented
                else:
                    rdata = socket.inet_pton(socket.AF_INET6, ip_address)
            else:
                if qtype != 1:  # Not A
                    rcode = 4  # Not Implemented
                else:
                    rdata = socket.inet_aton(ip_address)

            if rcode == 4:
                flags = (qr << 15) | (opcode << 11) | (aa << 10) | (tc << 9) | (rd << 8) | (ra << 7) | (z << 4) | rcode
                header = struct.pack("!HHHHHH", packet_id, flags, 1, 0, 0, 0)
                return header + encoded_name + struct.pack("!HH", qtype, qclass)

            answer_rdlength = struct.pack("!H", len(rdata))
            answer = answer_name + answer_type + answer_class + answer_ttl + answer_rdlength + rdata
            response = header + encoded_name + struct.pack("!HH", qtype, qclass) + answer
            return response

    # Forward query if not in local mappings and recursion is desired
    if rd:  # Only forward if recursion is desired
        logging.info(f"Domain {domain_name} not found locally. Forwarding query.")
        forwarded_response = forward_query(query)
        if forwarded_response:
            # Set QR bit to 1 in forwarded response and update packet ID
            flags = struct.unpack("!H", forwarded_response[2:4])[0]
            flags = (flags & 0xFEFF) | (rd << 8) | 0x8000  # Preserve RD bit and set QR bit
            return struct.pack("!H", packet_id) + struct.pack("!H", flags) + forwarded_response[4:]
    else:
        logging.info(f"Domain {domain_name} not found locally and recursion not desired.")

    # If we get here, either recursion was not desired or forwarding failed
    # Return name error response
    flags = (1 << 15) | (0 << 11) | (1 << 10) | (0 << 9) | (rd << 8) | (1 << 7) | (0 << 4) | 3
    header = struct.pack("!HHHHHH", packet_id, flags, 1, 0, 0, 0)
    return header + encoded_name + struct.pack("!HH", qtype, qclass)

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
