cd toollabs-images/
./build.py --docker-registry localhost:5000 base
./build.py --docker-registry localhost:5000 base --push
./build.py --docker-registry localhost:5000 base --push --single -t latest --no-cache
curl localhost:5000/v2/_catalog
