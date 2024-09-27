# DNS Server Project

This project is an implementation of a DNS server in Python. The DNS server listens for DNS queries, processes them, and sends back responses. The project is being developed incrementally, with a focus on understanding the DNS protocol and building out the various features of a functioning DNS server.

## Features Implemented So Far

### 1. **UDP Socket Setup**

- The server listens on `127.0.0.1` at port `2053` and can receive DNS query packets over UDP.

### 2. **DNS Header and Question Section Handling**

- The server constructs a DNS header according to DNS protocol specifications.
  - **Packet ID**: Extracted from the incoming query.
  - **Flags**: Properly set to indicate a standard query response, including handling the `QR`, `OPCODE`, `AA`, `TC`, `RD`, `RA`, `Z`, and `RCODE` fields.
  - **Counts**: `QDCOUNT`, `ANCOUNT`, `NSCOUNT`, and `ARCOUNT` are appropriately set based on the response.

- The question section from the query is extracted and included in the response.
  - **Name**: Parsed from the query, currently handling uncompressed label sequences.
  - **Type**: Always set to `1` (A record) for this stage.
  - **Class**: Always set to `1` (IN class).

### 3. **Answer Section Implementation**

- The server constructs the Answer section in DNS responses.
  - Returns IP addresses for known domains based on a static domain-to-IP mapping.
  - Uses pointer compression in the DNS response for efficient encoding.
  - **A Record Handling**:
    - **Name**: Encoded as a pointer to the domain name in the question section.
    - **Type**: Set to `1` (A record).
    - **Class**: Set to `1` (IN class).
    - **TTL**: Set to `300` seconds.
    - **RDLENGTH**: Set to `4` bytes (length of IPv4 address).
    - **RDATA**: Encoded IPv4 address (e.g., `8.8.8.8`).

### 4. **Handling Unknown Domains**

- If a domain is not found in the local mapping:
  - The server forwards the query to an upstream DNS server (e.g., Google DNS at `8.8.8.8`).
  - Handles the response from the upstream server and sends it back to the client.
  - Sets appropriate `RCODE` values based on the outcome:
    - `0` (No Error) if the upstream server resolves the domain.
    - `2` (Server Failure) if the upstream server does not respond.
    - `3` (Name Error) if the domain does not exist.

### 5. **Separate Domain-to-IP Mapping**

- Created a `domain_mappings.py` file to store domain-to-IP mappings separately from the main server code.
  - Enhances code organization and maintainability.
  - Example:
    ```python
    domain_ip_mapping = {
        'example.com': '8.8.8.8',
        'test.com': '8.8.4.4',
        'helloworld.com': '1.1.1.1',
        'random.org': '1.0.0.1'
    }
    ```

### 6. **Comprehensive Logging**

- Implemented detailed logging in `main.py` using Python's `logging` module.
  - Logs incoming queries, responses sent, forwarding actions, and any errors encountered.
  - Helps in debugging and monitoring server operations.
  - Example log entries:
    ```
    2024-09-18 13:58:35,000 - INFO - DNS server is starting...
    2024-09-18 13:58:35,001 - INFO - DNS server is running on 127.0.0.1:2053
    2024-09-18 13:58:36,002 - DEBUG - Received packet from ('127.0.0.1', 59070)
    2024-09-18 13:58:36,003 - DEBUG - Received query for domain: google.com
    2024-09-18 13:58:36,004 - INFO - Domain 'google.com' not found locally. Forwarding query.
    2024-09-18 13:58:36,025 - DEBUG - Received response from upstream server for domain 'google.com'.
    2024-09-18 13:58:36,026 - DEBUG - Sent response to ('127.0.0.1', 59070)
    ```

### 7. **Tester Script for Rigorous Testing**

- Developed `tester.py` to rigorously test the DNS server's functionality.
  - **Tests Included**:
    - **Known Domains**: Ensures that domains present in `domain_mappings.py` are resolved correctly.
    - **Recursive Query Handling**: Verifies that unknown domains are forwarded to the upstream DNS server and responses are correctly returned.
    - **Response Header Validation**: Checks that the `ID`, `QR`, `OPCODE`, `AA`, `RD`, `RA`, and `RCODE` fields are correctly set.
    - **Answer Section Validation**: Ensures that answer sections contain valid "A" records with correct IP addresses.
    - **Recursion Flags**: Verifies that the server respects the `RD` (Recursion Desired) flag when performing recursive queries.
  - **Usage**:
    ```bash
    python tester.py
    ```
  - **Example Output**:
    ```
    Ran 6 tests in 2.018s

    OK
    ```

## In Progress

### **Parsing Compressed Labels**

- **Implemented:**
  - Modified the `extract_domain_name` function in `main.py` to handle compressed labels in the question section.
  - Ensures that domain names with compressed label sequences are correctly parsed and included in the response.

- **Next Steps:**
  - Thoroughly test the parsing of compressed labels using various DNS clients and test cases.
  - Ensure that the response includes the uncompressed question section as required.

## Future Work

- **Respecting RD Flag from Client**:
  - Modify the server to check the client's `RD` (Recursion Desired) flag.
  - Perform recursion only if the `RD` flag is set.
  - If the `RD` flag is not set, respond with an authoritative answer or appropriate error codes without performing recursion.

- **Support for Additional Record Types**:
  - Implement handling of `AAAA` (IPv6), `CNAME`, `MX`, and other DNS record types.
  - Extend the server to support these records in both question and answer sections.

- **Dynamic Domain Loading**:
  - Implement dynamic reloading of `domain_mappings.py` without restarting the server.
  - Allow real-time updates to DNS records for better flexibility and maintenance.

- **Improved Error Handling**:
  - Enhance exception handling to gracefully manage malformed queries, network issues, and unexpected upstream responses.
  - Implement comprehensive `RCODE` responses based on different error scenarios.

- **Caching Mechanism**:
  - Add a caching system to store responses from upstream servers.
  - Utilize TTL values to determine cache expiration, reducing latency and upstream DNS queries.

- **Security Enhancements**:
  - Implement DNSSEC validation to protect against cache poisoning and other DNS-based attacks.
  - Introduce rate limiting and access control lists (ACLs) to prevent abuse and Denial of Service (DoS) attacks.

- **Concurrency and Performance Optimization**:
  - Enhance the server to handle multiple simultaneous queries using threading or asynchronous I/O.
  - Optimize response times and resource utilization for better scalability.

- **Logging and Monitoring Improvements**:
  - Expand logging to include more granular details such as cache hits/misses, query sources, and response times.
  - Integrate monitoring tools to track server performance and detect anomalies.

- **Zone Transfers (for Authoritative Servers)**:
  - Implement AXFR/IXFR support to enable zone transfers between primary and secondary DNS servers.
  - Ensure secure and efficient synchronization of DNS records across multiple servers.

## How It Works

1. **Server Startup**:
   - The server initializes a UDP socket and binds to `127.0.0.1:2053`.
   - Logging is configured to provide detailed output for monitoring and debugging.

2. **Query Processing**:
   - The server waits for incoming DNS query packets.
   - Upon receiving a query:
     - Extracts the domain name from the question section, handling both uncompressed and compressed labels.
     - Logs the received domain name and relevant query flags.

3. **Response Construction**:
   - **Known Domains**:
     - If the domain exists in `domain_mappings.py`, the server constructs a DNS response including the Answer section with the corresponding "A" record.
     - Sets `ANCOUNT` to `1` and populates the Answer section with the IP address.
   - **Unknown Domains**:
     - For domains not found locally, the server forwards the query to an upstream DNS server (e.g., Google DNS at `8.8.8.8`).
     - Handles the upstream response and sends it back to the client.
     - Sets appropriate `RCODE` values based on the outcome.

4. **Logging**:
   - Throughout the process, the server logs important events, including received queries, forwarding actions, responses sent, and any errors encountered.
   - Logs include timestamps, severity levels, and descriptive messages to aid in monitoring and debugging.

## How to Run

### **Prerequisites**

- Python 3.x installed on your system.

### **Running the DNS Server**

1. **Start the Server**:
   ```bash
   python main.py
   ```
   - The server will start and listen on `127.0.0.1:2053`.
   - Logs will be printed to the console, detailing incoming queries and responses.

### **Testing the DNS Server**

#### **Using the Tester Script**

- Ensure the server is not already running separately, as the tester will start it internally.

```bash
python tester.py
```

- The tester script will perform several tests and output the results.
- It tests known domains, recursive query handling, response integrity, and more.

#### **Manual Testing with `dig`**

- You can use the `dig` command to test the server manually.

**For a Known Domain (e.g., `example.com`):**
```bash
dig @127.0.0.1 -p 2053 example.com
```

**Expected Output:**
- The server should return the IP address specified in `domain_mappings.py` for `example.com`.

**For an Unknown Domain (e.g., `google.com`):**
```bash
dig @127.0.0.1 -p 2053 google.com
```

**Expected Output:**
- The server should resolve the domain via the upstream DNS server and return the appropriate IP address.

**Testing Without Recursion:**
```bash
dig @127.0.0.1 -p 2053 google.com +norecurse
```

- **Note**: Currently, the server does not respect the `RD` flag from the client and will perform recursion regardless.

## Project Structure

- `main.py`: The main DNS server implementation.
- `domain_mappings.py`: Contains the domain-to-IP mappings.
- `tester.py`: Script for testing the DNS server.
- `README.md`: Project documentation and usage instructions.

## Example Output

**Server Console Logs:**
```
2024-09-18 13:58:35,000 - INFO - DNS server is starting...
2024-09-18 13:58:35,001 - INFO - DNS server is running on 127.0.0.1:2053
2024-09-18 13:58:36,002 - DEBUG - Received packet from ('127.0.0.1', 59070)
2024-09-18 13:58:36,003 - DEBUG - Received query for domain: google.com
2024-09-18 13:58:36,004 - INFO - Domain 'google.com' not found locally. Forwarding query.
2024-09-18 13:58:36,025 - DEBUG - Received response from upstream server for domain 'google.com'.
2024-09-18 13:58:36,026 - DEBUG - Sent response to ('127.0.0.1', 59070)
```

**Tester Script Output:**
```
Ran 6 tests in 2.018s

OK
```

## Known Issues

- **Handling Compressed Labels**:
  - Currently, the server can parse compressed labels in the question section, but thorough testing is ongoing to ensure robustness.
  
- **Respecting RD Flag**:
  - The server does not currently respect the client's `RD` (Recursion Desired) flag and will perform recursion even if the client does not request it.

- **Record Types Supported**:
  - The server currently handles only `A` records (IPv4 addresses). Support for other record types like `AAAA`, `CNAME`, `MX`, etc., is not yet implemented.

- **Concurrency**:
  - The server handles queries sequentially. Implementing concurrency (e.g., threading or asynchronous I/O) is planned for future stages to improve performance.

- **Security Features**:
  - Basic security measures like rate limiting, access control, and DNSSEC validation are not yet implemented.

## Future Work

- **Respecting RD Flag from Client**:
  - Modify the server to check the client's `RD` (Recursion Desired) flag.
  - Perform recursion only if the `RD` flag is set.
  - If the `RD` flag is not set, respond with an authoritative answer or appropriate error codes without performing recursion.

- **Support for Additional Record Types**:
  - Implement handling of `AAAA` (IPv6), `CNAME`, `MX`, and other DNS record types.
  - Extend the server to support these records in both question and answer sections.

- **Dynamic Domain Loading**:
  - Implement dynamic reloading of `domain_mappings.py` without restarting the server.
  - Allow real-time updates to DNS records for better flexibility and maintenance.

- **Improved Error Handling**:
  - Enhance exception handling to gracefully manage malformed queries, network issues, and unexpected upstream responses.
  - Implement comprehensive `RCODE` responses based on different error scenarios.

- **Caching Mechanism**:
  - Add a caching system to store responses from upstream servers.
  - Utilize TTL values to determine cache expiration, reducing latency and upstream DNS queries.

- **Security Enhancements**:
  - Implement DNSSEC validation to protect against cache poisoning and other DNS-based attacks.
  - Introduce rate limiting and access control lists (ACLs) to prevent abuse and Denial of Service (DoS) attacks.

- **Concurrency and Performance Optimization**:
  - Enhance the server to handle multiple simultaneous queries using threading or asynchronous I/O.
  - Optimize response times and resource utilization for better scalability.

- **Logging and Monitoring Improvements**:
  - Expand logging to include more granular details such as cache hits/misses, query sources, and response times.
  - Integrate monitoring tools to track server performance and detect anomalies.

- **Zone Transfers (for Authoritative Servers)**:
  - Implement AXFR/IXFR support to enable zone transfers between primary and secondary DNS servers.
  - Ensure secure and efficient synchronization of DNS records across multiple servers.

## Contributions

- The tester script (`tester.py`) was developed with assistance from OpenAI GPT to ensure comprehensive testing of the DNS server.

---

Feel free to explore, modify, and extend this project. Contributions and feedback are welcome!

---

### How to Contribute

1. **Fork the Repository**: Create your own fork of the project.

2. **Clone the Fork**:
   ```bash
   git clone https://github.com/your-username/dns-server-python.git
   ```

3. **Create a New Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes**: Implement your feature or bug fix.

5. **Commit Changes**:
   ```bash
   git add .
   git commit -m "Describe your changes"
   ```

6. **Push to Your Fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**: Submit a pull request to the original repository.

---

### License

This project is open-source and available under the MIT License.

---

If you have any questions or need assistance, feel free to reach out!

---

**Note**: In the future, we plan to respect the client's RD flag to fully comply with DNS standards.

---
```