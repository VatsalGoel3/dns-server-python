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

    def send_dns_query(self, domain_name, record_type=1, packet_id=1234, rd_flag=1):
        query = self.build_dns_query(domain_name, record_type, packet_id, rd_flag)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(5)
        try:
            client_socket.sendto(query, ('127.0.0.1', 2053))
            response, _ = client_socket.recvfrom(512)
            return response
        except socket.timeout:
            self.fail(f"Timeout waiting for response from DNS server for domain {domain_name}")
        finally:
            client_socket.close()

    def build_dns_query(self, domain_name, record_type, packet_id, rd_flag):
        encoded_name = self.encode_domain_name(domain_name)
        flags = 0x0000  # Standard query
        if rd_flag:
            flags |= 0x0100  # Set RD flag if recursion is desired
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
            if offset >= len(data):
                raise ValueError("Offset exceeds data length while decoding domain name.")
            length = data[offset]
            if length == 0:
                offset += 1
                break
            elif (length & 0xC0) == 0xC0:
                # Pointer encountered
                if offset + 1 >= len(data):
                    raise ValueError("Incomplete pointer in domain name.")
                pointer = struct.unpack("!H", data[offset:offset+2])[0]
                pointer &= 0x3FFF  # Mask the first two bits
                labels.extend(self.decode_compressed_domain_name(data, pointer))
                offset += 2
                break
            else:
                offset += 1
                label = data[offset:offset+length].decode('ascii')
                labels.append(label)
                offset += length
        domain_name = '.'.join(labels)
        return domain_name, offset

    def decode_compressed_domain_name(self, data, pointer):
        labels = []
        while True:
            if pointer >= len(data):
                raise ValueError("Pointer exceeds data length while decoding domain name.")
            length = data[pointer]
            if length == 0:
                break
            elif (length & 0xC0) == 0xC0:
                # Nested pointer
                if pointer + 1 >= len(data):
                    raise ValueError("Incomplete nested pointer in domain name.")
                new_pointer = struct.unpack("!H", data[pointer:pointer+2])[0] & 0x3FFF
                labels.extend(self.decode_compressed_domain_name(data, new_pointer))
                break
            else:
                pointer += 1
                label = data[pointer:pointer+length].decode('ascii')
                labels.append(label)
                pointer += length
        return labels

    def parse_response(self, response):
        header = struct.unpack("!HHHHHH", response[:12])
        packet_id, flags, qdcount, ancount, nscount, arcount = header

        offset = 12

        # Parse Question Section
        questions = []
        for _ in range(qdcount):
            domain_name, offset = self.decode_domain_name(response, offset)
            qtype, qclass = struct.unpack("!HH", response[offset:offset+4])
            offset += 4
            questions.append({
                'name': domain_name,
                'type': qtype,
                'class': qclass
            })

        # Parse Answer Section
        answers = []
        for _ in range(ancount):
            name, offset = self.decode_domain_name(response, offset)
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
            'questions': questions,
            'answers': answers
        }

    def test_known_domains(self):
        # Domains that should be resolved locally
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

    def test_recursive_resolution(self):
        # Domains not in local mapping, should be resolved via recursion
        domain = 'google.com'
        response = self.send_dns_query(domain)
        parsed_response = self.parse_response(response)

        # Check packet ID
        self.assertEqual(parsed_response['packet_id'], 1234)

        # Check that it's a response
        qr = (parsed_response['flags'] >> 15) & 1
        self.assertEqual(qr, 1)

        # Check that RA flag is set
        ra = (parsed_response['flags'] >> 7) & 1
        self.assertEqual(ra, 1)

        # Check that RCODE is 0 (No error)
        rcode = parsed_response['flags'] & 0xF
        self.assertEqual(rcode, 0)

        # Check that we have at least one answer
        self.assertGreaterEqual(parsed_response['ancount'], 1)

        # Optionally, validate that the answer is a valid IP address
        for answer in parsed_response['answers']:
            self.assertEqual(answer['type'], 1)    # Type A
            self.assertEqual(answer['class'], 1)   # Class IN
            try:
                socket.inet_ntoa(answer['rdata'])
            except socket.error:
                self.fail("Invalid IP address format in answer RDATA.")

    def test_no_recursion(self):
        # Test that when RD flag is not set, server does not perform recursion
        domain = 'google.com'
        response = self.send_dns_query(domain, rd_flag=0)
        parsed_response = self.parse_response(response)

        # Check that RA flag is set (server supports recursion)
        ra = (parsed_response['flags'] >> 7) & 1
        self.assertEqual(ra, 1)

        # Check that RD flag is not set in the response
        rd = (parsed_response['flags'] >> 8) & 1
        self.assertEqual(rd, 0)

        # Currently, the server forwards queries regardless of RD flag,
        # so ANCOUNT should be >=1
        self.assertGreaterEqual(parsed_response['ancount'], 1)

    def test_unknown_domain(self):
        # Domain that likely doesn't exist
        domain = 'nonexistentdomain.example'
        response = self.send_dns_query(domain)
        parsed_response = self.parse_response(response)

        # Check that RCODE is 0 (No error) or 3 (Name Error)
        rcode = parsed_response['flags'] & 0xF
        self.assertIn(rcode, [0, 3])

        # If RCODE is 3, ensure ANCOUNT is 0
        if rcode == 3:
            self.assertEqual(parsed_response['ancount'], 0)
        elif rcode == 0:
            # If RCODE is 0, ensure ANCOUNT >=1
            self.assertGreaterEqual(parsed_response['ancount'], 1)

    def test_invalid_domain(self):
        # Test with an invalid domain name
        domain = 'invalid_domain_name'
        response = self.send_dns_query(domain)
        parsed_response = self.parse_response(response)

        # The behavior may vary; DNS queries are tolerant of invalid domain names
        # Check the RCODE and ancount accordingly
        rcode = parsed_response['flags'] & 0xF
        self.assertIn(rcode, [0, 3])

        # If RCODE is 3, ensure ANCOUNT is 0
        if rcode == 3:
            self.assertEqual(parsed_response['ancount'], 0)
        elif rcode == 0:
            # If RCODE is 0, ensure ANCOUNT >=1
            self.assertGreaterEqual(parsed_response['ancount'], 1)

    def test_multiple_queries(self):
        # Currently, the server handles only single-question queries
        # This test ensures that the server can handle multiple queries gracefully
        # Since handling multiple questions is planned for future work, this test is expected to fail or handle only the first question
        domains = ['example.com', 'google.com']
        responses = []
        for idx, domain in enumerate(domains):
            with self.subTest(domain=domain):
                response = self.send_dns_query(domain, packet_id=1000 + idx)
                parsed_response = self.parse_response(response)
                responses.append(parsed_response)

                # Check packet ID
                self.assertEqual(parsed_response['packet_id'], 1000 + idx)

                # Check that it's a response
                qr = (parsed_response['flags'] >> 15) & 1
                self.assertEqual(qr, 1)

                # Check RCODE
                rcode = parsed_response['flags'] & 0xF
                self.assertIn(rcode, [0, 3])

                # Check ANCOUNT based on RCODE
                if rcode == 0:
                    self.assertGreaterEqual(parsed_response['ancount'], 1)
                elif rcode == 3:
                    self.assertEqual(parsed_response['ancount'], 0)

    @classmethod
    def tearDownClass(cls):
        # Optionally, implement server shutdown if necessary
        pass

if __name__ == '__main__':
    unittest.main()
