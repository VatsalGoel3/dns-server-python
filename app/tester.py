import socket
import struct
import unittest
import threading
import time

class TestDNSServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Import your DNS server code here
        from main import run_dns_server

        # Start the DNS server in a separate thread
        cls.server_thread = threading.Thread(target=run_dns_server, daemon=True)
        cls.server_thread.start()
        time.sleep(1)  # Give the server time to start

    def send_dns_query(self, domain_name, record_type=1, packet_id=1234):
        query = self.build_dns_query(domain_name, record_type, packet_id)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(2)
        try:
            client_socket.sendto(query, ('127.0.0.1', 2053))
            response, _ = client_socket.recvfrom(512)
            return response
        except socket.timeout:
            self.fail(f"Timeout waiting for response from DNS server for domain {domain_name}")
        finally:
            client_socket.close()

    def build_dns_query(self, domain_name, record_type, packet_id):
        encoded_name = self.encode_domain_name(domain_name)
        flags = 0x0100  # Standard query
        qdcount = 1
        ancount = 0
        nscount = 0
        arcount = 0
        header = struct.pack("!HHHHHH", packet_id, flags, qdcount, ancount, nscount, arcount)
        question = encoded_name + struct.pack("!HH", record_type, 1)  # Type, Class
        return header + question

    def encode_domain_name(self, domain_name):
        parts = domain_name.split('.')
        encoded_name = b''
        for part in parts:
            encoded_name += bytes([len(part)]) + part.encode('ascii')
        encoded_name += b'\x00'
        return encoded_name

    def decode_domain_name(self, data, offset):
        labels = []
        while True:
            length = data[offset]
            if length == 0:
                offset += 1
                break
            elif (length & 0xC0) == 0xC0:
                # Pointer encountered
                pointer = struct.unpack("!H", data[offset:offset+2])[0]
                pointer &= 0x3FFF  # Mask the first two bits
                _, name = self.decode_domain_name(data, pointer)
                labels.append(name)
                offset += 2
                break
            else:
                offset += 1
                labels.append(data[offset:offset+length].decode('ascii'))
                offset += length
        domain_name = '.'.join(labels)
        return offset, domain_name

    def parse_response(self, response):
        header = struct.unpack("!HHHHHH", response[:12])
        packet_id, flags, qdcount, ancount, nscount, arcount = header

        offset = 12

        # Parse Question Section
        for _ in range(qdcount):
            offset, domain_name = self.decode_domain_name(response, offset)
            qtype, qclass = struct.unpack("!HH", response[offset:offset+4])
            offset += 4

        # Parse Answer Section
        answers = []
        for _ in range(ancount):
            offset, name = self.decode_domain_name(response, offset)
            atype, aclass, attl, ardlength = struct.unpack("!HHIH", response[offset:offset+10])
            offset += 10
            rdata = response[offset:offset+ardlength]
            offset += ardlength
            answers.append({
                'name': name,
                'type': atype,
                'class': aclass,
                'ttl': attl,
                'rdata': rdata
            })

        return {
            'packet_id': packet_id,
            'flags': flags,
            'qdcount': qdcount,
            'ancount': ancount,
            'nscount': nscount,
            'arcount': arcount,
            'answers': answers
        }

    def test_known_domains(self):
        # Domains that should be resolved
        domain_ip_mapping = {
            'example.com': '28.121.220.44',
            'test.com': '28.121.220.44',
            'helloworld.com': '28.121.220.44',
            'random.org': '28.121.220.44'
        }

        for domain, expected_ip in domain_ip_mapping.items():
            with self.subTest(domain=domain):
                response = self.send_dns_query(domain)
                parsed_response = self.parse_response(response)

                # Check packet ID
                self.assertEqual(parsed_response['packet_id'], 1234)

                # Check that it's a response
                qr = (parsed_response['flags'] >> 15) & 1
                self.assertEqual(qr, 1)

                # Check that RCODE is 0 (No error)
                rcode = parsed_response['flags'] & 0xF
                self.assertEqual(rcode, 0)

                # Check that we have one answer
                self.assertEqual(parsed_response['ancount'], 1)

                # Validate the answer
                answer = parsed_response['answers'][0]
                self.assertEqual(answer['type'], 1)    # Type A
                self.assertEqual(answer['class'], 1)   # Class IN
                ip_address = socket.inet_ntoa(answer['rdata'])
                self.assertEqual(ip_address, expected_ip)

    def test_unknown_domain(self):
        # Domain that should not be resolved
        domain = 'unknown-domain.com'
        response = self.send_dns_query(domain)
        parsed_response = self.parse_response(response)

        # Check that RCODE is 3 (Name Error)
        rcode = parsed_response['flags'] & 0xF
        self.assertEqual(rcode, 3)

        # Check that we have zero answers
        self.assertEqual(parsed_response['ancount'], 0)

    def test_invalid_domain(self):
        # Test with an invalid domain name
        domain = 'invalid_domain_name'
        response = self.send_dns_query(domain)
        parsed_response = self.parse_response(response)

        # Check that RCODE is 3 (Name Error)
        rcode = parsed_response['flags'] & 0xF
        self.assertEqual(rcode, 3)

        # Check that we have zero answers
        self.assertEqual(parsed_response['ancount'], 0)

    def test_multiple_queries(self):
        # Send multiple queries in rapid succession
        domain = 'example.com'
        num_queries = 100
        for i in range(num_queries):
            with self.subTest(i=i):
                response = self.send_dns_query(domain, packet_id=1000 + i)
                parsed_response = self.parse_response(response)
                self.assertEqual(parsed_response['packet_id'], 1000 + i)
                # Additional checks can be added here

if __name__ == '__main__':
    unittest.main()
