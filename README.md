# naps-api
microservices for the  NAPS applications.

### ⚠️ after changes to DB schema run:
```
flask db migrate -m "update migration"
flask db upgrade
```

### before push (auto linter)
```
autopep8 --in-place --aggressive --aggressive $(git ls-files '*.py')
```