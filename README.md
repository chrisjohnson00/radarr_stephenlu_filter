Run for dev

    FLASK_APP=app.py FLASK_ENV=development REDIS_HOST=localhost flask run

Run redis locally with

    docker run --rm --name redis -p 6379:6379 -d redis
    
Port forward to consul

    kubectl port-forward service/consul-consul-server 8500:8500 -n consul

## PyPi Dependency updates

    pip install --upgrade pip
    pip install --upgrade python-consul python-pushover redis Flask gunicorn
    pip freeze > requirements.txt
    sed -i '/pkg_resources/d' requirements.txt
    sed -i '/dataclasses/d' requirements.txt
