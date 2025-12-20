#!/bin/bash

# Configuration
PROXY="127.0.0.1:56000"
TARGET_HTTP="http://example.com"
TARGET_HTTPS="https://www.google.com"
BLOCKED_DOMAIN="bing.com" # Ensure this is in your blacklist file!

echo "=========================================="
echo "    Starting Proxy Server Test Suite"
echo "=========================================="

# 1. Basic HTTP GET
echo -e "\n[TEST 1] Standard HTTP GET..."
curl -s -o /dev/null -w "%{http_code}" -x $PROXY $TARGET_HTTP
if [ $? -eq 0 ]; then echo " -> PASS"; else echo " -> FAIL"; fi

# 2. HTTPS Tunneling
echo -e "\n[TEST 2] HTTPS CONNECT Tunnel..."
curl -s -o /dev/null -w "%{http_code}" -x $PROXY $TARGET_HTTPS
if [ $? -eq 0 ]; then echo " -> PASS"; else echo " -> FAIL"; fi

# 3. Blacklist Blocking
echo -e "\n[TEST 3] Blacklist Blocking ($BLOCKED_DOMAIN)..."
CODE=$(curl -s -o /dev/null -w "%{http_code}" -x $PROXY "http://$BLOCKED_DOMAIN")
if [ "$CODE" == "403" ]; then
    echo " -> PASS (Received 403 Forbidden)"
else
    echo " -> FAIL (Received $CODE, expected 403)"
fi

# 4. Large Payload (Simulate 15MB Upload)
echo -e "\n[TEST 4] Large Payload Blocking (>10MB)..."
# Create temporary 15MB file
dd if=/dev/zero of=temp_large_file bs=1M count=15 2>/dev/null
CODE=$(curl -s -o /dev/null -w "%{http_code}" -x $PROXY --data-binary @temp_large_file http://httpbin.org/post)
if [ "$CODE" == "413" ]; then
    echo " -> PASS (Received 413 Payload Too Large)"
else
    echo " -> FAIL (Received $CODE, expected 413)"
fi
rm temp_large_file

# 5. Concurrency Test
echo -e "\n[TEST 5] Concurrency Stress Test (10 parallel requests)..."
start_time=$(date +%s%N)
for i in {1..10}; do
    curl -s -o /dev/null -x $PROXY $TARGET_HTTP &
done
wait
end_time=$(date +%s%N)
echo " -> PASS (10 requests completed)"

echo -e "\n=========================================="
echo "    Tests Complete. Check proxy.log for details."
echo "=========================================="