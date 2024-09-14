import socket
import struct
import threading
import time
import concurrent.futures
import argparse

def send_dns_query(domain_name, server_address=('127.0.0.1', 2053), packet_id=1234):
    query = build_dns_query(domain_name, packet_id)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(2)
    try:
        client_socket.sendto(query, server_address)
        response, _ = client_socket.recvfrom(512)
        # Optionally parse and validate the response
        return True  # Indicate success
    except socket.timeout:
        print(f"Timeout for domain: {domain_name}")
        return False  # Indicate failure
    except Exception as e:
        print(f"Error sending query for {domain_name}: {e}")
        return False
    finally:
        client_socket.close()

def build_dns_query(domain_name, packet_id):
    encoded_name = encode_domain_name(domain_name)
    flags = 0x0100  # Standard query
    qdcount = 1
    ancount = 0
    nscount = 0
    arcount = 0
    header = struct.pack("!HHHHHH", packet_id, flags, qdcount, ancount, nscount, arcount)
    question = encoded_name + struct.pack("!HH", 1, 1)
    return header + question

def encode_domain_name(domain_name):
    parts = domain_name.split('.')
    encoded_name = b''
    for part in parts:
        encoded_name += bytes([len(part)]) + part.encode('ascii')
    encoded_name += b'\x00'
    return encoded_name

def run_load_test(domain_names, total_requests, max_workers=100):
    start_time = time.time()
    successes = 0
    failures = 0

    def task(domain, packet_id):
        success = send_dns_query(domain, packet_id=packet_id)
        return success

    # Use ThreadPoolExecutor to manage threads efficiently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(total_requests):
            domain = domain_names[i % len(domain_names)]
            packet_id = 1000 + i  # Ensure unique packet IDs
            futures.append(executor.submit(task, domain, packet_id))

        # As futures complete, tally the results
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                successes += 1
            else:
                failures += 1

    end_time = time.time()
    duration = end_time - start_time
    print(f"Total requests: {total_requests}")
    print(f"Successful responses: {successes}")
    print(f"Failed responses: {failures}")
    print(f"Total time: {duration:.2f} seconds")
    print(f"Requests per second: {total_requests / duration:.2f}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="DNS Server Load Tester")
    parser.add_argument('--requests', type=int, default=1000, help='Total number of DNS queries to send')
    parser.add_argument('--workers', type=int, default=100, help='Maximum number of worker threads')
    args = parser.parse_args()

    # List of domain names to test
    domain_names = ['example.com', 'codecrafters.io', 'test.com', 'mydomain.net', 'random.org']

    # Run the load test
    run_load_test(domain_names, args.requests, args.workers)
