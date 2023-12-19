





curl -X POST http://localhost:5000/messages -H "Content-Type: application/json" -d '{"message": "Your test message", "w": 2}'

**{"message":"Message replicated with required write concern","status":"success"}**

| col1 | col2 | col3 |
| ---- | ---- | ---- |
|      |      |      |


curl http://localhost:5000/health


curl http://localhost:5001/health  # For secondary1
curl http://localhost:5002/health  # For secondary2 (if applicable)


curl http://localhost:5000/secondary_health
