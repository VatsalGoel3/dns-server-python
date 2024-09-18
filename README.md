```markdown
# DNS Server Project

This project is an implementation of a DNS server in Python. The DNS server listens for DNS queries, processes them, and sends back responses. The project is being developed incrementally, with a focus on understanding the DNS protocol and building out the various features of a functioning DNS server.

## Features Implemented So Far

### 1. **UDP Socket Setup**

- The server listens on `127.0.0.1` at port `2053` and can receive DNS query packets over UDP.

### 2. **DNS Header and Question Section Handling**

- The server constructs a DNS header according to DNS protocol specifications.
  - **Packet ID**: Extracted from the query.
  - **Flags**: Properly set to indicate a standard query response.
  - **Counts**: `QDCOUNT`, `ANCOUNT`, `NSCOUNT`, and `ARCOUNT` are appropriately set based on the response.

- The question section from the query is extracted and included in the response.

### 3. **Answer Section Implementation**

- The server constructs the Answer section in DNS responses.
  - Returns IP addresses for known domains based on a static domain-to-IP mapping.
  - Uses pointer compression in the DNS response for efficient encoding.

### 4. **Handling Unknown Domains**

- If a domain is not found in the local mapping:
  - The server forwards the query to an upstream DNS server (e.g., Google DNS at `8.8.8.8`).
  - Handles the response from the upstream server and sends it back to the client.
  - Currently, the server forwards all unknown queries regardless of the client's RD (Recursion Desired) flag.

### 5. **Recursive Query Handling**

- Implemented recursive query handling to resolve any domain name, not just those in the local mapping.
  - The server indicates that recursion is available (`RA` flag is set in responses).
  - Queries are forwarded to the upstream DNS server when necessary.

### 6. **Separate Domain-to-IP Mapping**

- Created a `domain_mappings.py` file to store domain-to-IP mappings separately from the main server code.
  - Enhances code organization and maintainability.

### 7. **Comprehensive Logging**

- Implemented detailed logging in `main.py` using Python's `logging` module.
  - Logs incoming queries, responses sent, and any errors encountered.
  - Helps in debugging and monitoring server operations.

### 8. **Tester Script for Rigorous Testing**

- Developed `tester.py` to rigorously test the DNS server's functionality.
  - Tests handling of known and unknown domains.
  - Tests recursive query handling.
  - Checks for correct RCODE settings and response structures.
  - Simulates multiple queries to test server robustness.
  - The tester code was created with assistance from OpenAI GPT.

## How It Works

1. **Server Startup**:
   - The server initializes a UDP socket and binds to `127.0.0.1:2053`.
   - Logging is configured to provide detailed output.

2. **Query Processing**:
   - The server waits for incoming DNS query packets and processes them in a loop.
   - When a query is received:
     - Extracts the domain name from the query.
     - Logs the received domain name.

3. **Response Construction**:
   - Checks if the domain name exists in `domain_mappings.py`.
     - If found:
       - Constructs the DNS response with the Answer section, including the IP address.
       - Sets `ANCOUNT` to `1`.
     - If not found:
       - Forwards the query to the upstream DNS server.
       - Handles the response and sends it back to the client.
   - Logs the action taken (e.g., domain found locally, query forwarded).
   - Sends the response back to the client.

4. **Logging**:
   - Throughout the process, the server logs important events and errors.
   - Logs include timestamps, severity levels, and messages.

## How to Run

### **Prerequisites**

- Python 3.x installed on your system.

### **Running the DNS Server**

```bash
python main.py
```

- The server will start and listen on `127.0.0.1:2053`.
- Logs will be printed to the console.

### **Testing the DNS Server**

#### **Using the Tester Script**

- Ensure the server is not already running separately, as the tester will start it internally.

```bash
python tester.py
```

- The tester script will perform several tests and output the results.
- It tests known domains, unknown domains, recursive query handling, and multiple queries.

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

- Currently, the server does not respect the RD flag from the client and will perform recursion regardless.

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

- The server currently handles only `A` records (IPv4 addresses).
- **Respecting RD Flag**: The server does not currently respect the client's RD (Recursion Desired) flag and will perform recursion even if the client does not request it.

## Future Work

- **Respecting RD Flag from Client**:
  - Modify the server to check the client's RD flag and only perform recursion if it is set.
  - If the RD flag is not set, the server should return an authoritative response with `RCODE` set to `3` (Name Error) for unknown domains.

- **Support for Additional Record Types**:
  - Implement handling of `AAAA` (IPv6), `CNAME`, `MX`, and other DNS record types.

- **Dynamic Domain Loading**:
  - Implement dynamic reloading of `domain_mappings.py` without restarting the server.

- **Improved Error Handling**:
  - Enhance exception handling and logging for robustness.

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

**Note:** In the future, we plan to respect the client's RD flag to fully comply with DNS standards.

---
```