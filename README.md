# DNS Server Project

This project is an implementation of a DNS server in Python. The DNS server listens for DNS queries, processes them, and sends back a response. It is being developed incrementally, with a focus on understanding the DNS protocol and building out the various features of a functioning DNS server.

## Features Implemented So Far

### 1. **UDP Socket Setup**
- The server listens on `127.0.0.1` at port `2053` and can receive DNS query packets over UDP.

### 2. **DNS Header Construction**
- The server constructs a DNS header according to the DNS protocol specifications:
  - **Packet ID**: A fixed packet identifier (currently set to `1234`).
  - **Flags**: Various DNS flags such as QR (Query/Response), Opcode, and RCODE are packed into a 16-bit field.
  - **Question Count (QDCOUNT)**, **Answer Count (ANCOUNT)**, **Name Server Count (NSCOUNT)**, and **Additional Records Count (ARCOUNT)** are all set to `0` for now.

### 3. **Responding to Queries**
- The server receives a DNS query and responds with a minimal DNS response that includes only the header for now. The query's domain name is extracted, and the response includes the appropriate DNS header and the question section (domain name, type, and class).

### 4. **Logging**
- The server logs incoming packets and provides basic debugging output for the DNS header and domain name fields. For example:
  - **Logs include**: Packet ID, Flags, and extracted domain name from the query.

## How It Works

1. **Socket Binding**: The server opens a UDP socket and binds to `127.0.0.1:2053`.
2. **Query Processing**: It waits for incoming DNS query packets and processes them in a loop.
3. **Response Construction**: When a query is received, the server constructs a basic DNS response, which includes:
   - A **Packet ID** (currently fixed at `1234`).
   - Flags indicating that the response is a standard query response (`QR = 1`, `Opcode = 0`).
   - The server responds with only the header and question sections. No answers or additional records are included in the response for now (`QDCOUNT = 1`, `ANCOUNT = 0`, `NSCOUNT = 0`, `ARCOUNT = 0`).
4. **Logging**: The server logs incoming queries and responses for debugging purposes.

## Future Work

1. **Handling Different DNS Record Types**
   - The next step is to parse and handle different record types, such as:
     - **A (IPv4)**, **AAAA (IPv6)**, **CNAME (Canonical Name)**, etc.

2. **Recursive Queries**
   - Implementing recursive query resolution to forward DNS requests and obtain responses from other DNS servers.

3. **Answer Section**
   - Adding the ability to respond with proper answers (for example, returning IP addresses for domain name queries in the "Answer" section).

4. **Full DNS Packet Parsing**
   - Fully parsing the incoming DNS queries to support various sections, such as **additional sections** and **authority records**.

## How to Run

### 1. **Run the DNS Server**
Make sure you have Python 3 installed. You can start the DNS server with the following command:

```bash
python app/main.py
```

### 2. **Test the DNS Server**
Use `dig` to send a query to your server:

```bash
dig @127.0.0.1 -p 2053 example.com
```

The server will respond with a minimal DNS header and question section for now.

### Project Structure

- `app/main.py`: The main entry point for the DNS server implementation.
- `README.md`: This file, describing the project and its current state.
- `test_dns_server.py`: A test script that sends multiple DNS queries to the server and checks the responses.

## Example Output

When a query is received, you should see output like the following:

```plaintext
Received packet from ('127.0.0.1', 53336)
Received query for the domain: example.com
Sent DNS response to ('127.0.0.1', 53336)
```

## Known Issues

- The server currently only responds with a basic DNS header and doesn't handle full DNS queries yet.
- Only IPv4 queries (A records) are partially supported, with no recursive queries or additional records.
- The server doesn't return actual answers (like IP addresses) in the "Answer" section yet.

---

### Changes Made:
- **Updated "Features Implemented So Far"** to reflect the current state of the project, including DNS header construction and query logging.
- **Added Detailed Instructions** on how to run and test the DNS server.
- **Structured the Future Work Section** to outline the next stages of development (DNS record types, recursive queries, etc.).
- **Example Output** includes real output from the server for better clarity.