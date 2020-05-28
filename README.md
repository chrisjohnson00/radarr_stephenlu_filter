Run for dev

    FLASK_APP=app.py FLASK_ENV=development REDIS_HOST=localhost flask run

Run redis locally with

    docker run --name redis -p 6379:6379 -d redis
