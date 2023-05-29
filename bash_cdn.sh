#!/bin/bash

export TZ=America/Chicago
echo 'CDN Script has been started at' $(date)

# build script image
docker build --tag aqua/scripts_cdn . -f dockerfile_cdn.prober

# build vpn image
docker build --tag aqua/vpn_cdn . -f dockerfile.vpn

# Read the country name bfrom the file
for COUNTRY in $(cat ./infralocationanalysis/data/countryList.txt); do
  echo $COUNTRY

  # Connect to VPN server
  docker run --rm -itd --name vpn_cdn_$COUNTRY --cap-add=NET_ADMIN --cap-add=NET_RAW -e CONNECT=$COUNTRY aqua/vpn_cdn

  sleep 10

  echo "VPN Certified Authority works, connected to " $COUNTRY

  docker run --rm -itd --name script_container_cdn -e COUNTRY=$COUNTRY --net container:vpn_cdn_$COUNTRY aqua/scripts_cdn

  # find vpn container id
  vpn_cdn_container_id=$(docker ps --filter "name=$vpn_cdn_$COUNTRY" --format "{{.ID}}")

   # Start the Docker container with the environment variable
  while [ "$(docker ps --filter "name=script_container_cdn" --format '{{.ID}}' | grep . | wc -l)" -ge 1 ]; do
    echo "Waiting for script_container_cdn to stop..."
    sleep 100
  done

  docker stop $vpn_cdn_container_id

  echo "script_container_cdn is not running"

  sleep 120

done

echo "All countries in the file has finished running CDN script"