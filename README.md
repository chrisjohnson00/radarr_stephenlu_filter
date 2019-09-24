Run for dev

    FLASK_APP=app.py FLASK_ENV=development flask run

Run in docker

    docker run --rm -p 5000:5000 stephenlu_filter

Run redis locally

    docker run --name redis -p 6379:6379 -d redis

Build the docker

    docker build . -t stephenlu_filter
    
Run with docker compose with 

    docker-compose up -d
