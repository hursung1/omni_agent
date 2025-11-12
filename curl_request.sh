query="재매이햄 요즘 뭐함?"
curl -N -X POST "http://localhost:8888/search/" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\"}"