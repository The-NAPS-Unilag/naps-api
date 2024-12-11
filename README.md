# naps-api
microservices for the  NAPS applications.

### ⚠️ after changes to DB schema run:
```
flask db migrate -m "update migration"
flask db upgrade
```