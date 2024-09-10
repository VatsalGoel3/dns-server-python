
---

# DNS Server Project

This project is an implementation of a DNS server in Python. The DNS server listens for DNS queries, processes them, and sends back a response. This project is being developed incrementally, with a focus on understanding the DNS protocol and building out the various features of a functioning DNS server.

## Features Implemented So Far

- **UDP Socket Setup**: The server listens on `127.0.0.1` at port `2053` and can receive DNS query packets over UDP.
- **DNS Header Construction**: The server constructs a DNS header according to the DNS protocol specifications:
  - Packet ID: A fixed packet identifier (currently set to `1234`).
  - Flags: Various DNS flags such as QR (Query/Response), Opcode, and RCODE are packed into a 16-bit field.
  - Question Count (QDCOUNT), Answer Count (ANCOUNT), Name Server Count (NSCOUNT), and Additional Records Count (ARCOUNT) are all set to 0 for now.

- **Responding to Queries**: The server receives a query and responds with a minimal DNS response that includes only the header for now.
- **Logging**: The server logs incoming packets and provides basic debugging output for the DNS header fields.

## How It Works

1. The server opens a UDP socket and binds to `127.0.0.1:2053`.
2. It waits for incoming DNS query packets and processes them in a loop.
3. When a query is received, the server constructs a basic DNS header, which includes:
   - A packet ID (currently fixed at `1234`).
   - Flags indicating that the response is a standard query response (`QR = 1`, `Opcode = 0`).
   - No answers or additional records are included in the response for now (QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT are all set to `0`).
4. The server sends this response back to the client.

## Future Work

- **Handling Different DNS Record Types**: The next step is to parse and handle different record types (such as A, AAAA, CNAME, etc.).
- **Recursive Queries**: Implementing recursive query resolution to forward DNS requests and get responses from other DNS servers.
- **Answer Section**: Adding the ability to respond with proper answers (for example, returning IP addresses for domain name queries).
- **Full DNS Packet Parsing**: Fully parsing the incoming DNS queries to support questions and additional sections.

## How to Run

1. **Run the DNS Server**:
   Make sure you have Python 3 installed. You can start the DNS server with the following command:
   ```bash
   python app/main.py
   ```

2. **Test the DNS Server**:
   Use `dig` to send a query to your server:
   ```bash
   dig @127.0.0.1 -p 2053 example.com
   ```

   The server will respond with a minimal DNS header for now.

## Project Structure

- `app/main.py`: The main entry point for the DNS server implementation.
- `README.md`: This file, describing the project and its current state.

## Example Output

When a query is received, you should see output like the following:

```
Received packet from ('127.0.0.1', 53336)
Sent DNS response to ('127.0.0.1', 53336)
```

## Known Issues

- The server currently only responds with a basic DNS header and doesn't handle full DNS queries yet.
- Only IPv4 queries (A records) are partially supported.

---

