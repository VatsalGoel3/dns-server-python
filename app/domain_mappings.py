# For storing domain to IP address mapping, to avoid storing this information in main.py
# Intially using same IP address for all server for testing
# Added single AAAA record, to test IPv6
domain_ip_mapping = {
    'example.com' : '28.121.220.44',
    'test.com' : '28.121.220.44',
    'helloworld.com' : '28.121.220.44',
    'random.org' : '28.121.220.44',
    'codecrafters.io' : '28.121.220.44',
    'ipv6example.com' : '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
}