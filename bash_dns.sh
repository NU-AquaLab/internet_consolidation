#!/bin/bash

export TZ=America/Chicago
echo 'Script has been started at' $(date)

# build script image
docker build --tag aqua/scripts_dns . -f dockerfile.prober

# build vpn image
docker build --tag aqua/vpn_dns . -f dockerfile.vpn

# Read the country name bfrom the file
for COUNTRY in $(cat ./infralocationanalysis/data/countryList.txt); do
  echo $COUNTRY

  # Connect to VPN server
  docker run --rm -itd --name vpn_$COUNTRY --cap-add=NET_ADMIN --cap-add=NET_RAW -e CONNECT=$COUNTRY aqua/vpn_dns

  sleep 10

  echo "VPN works, connected to " $COUNTRY

  docker run --rm -itd --name script_container_dns -e COUNTRY=$COUNTRY --net container:vpn_$COUNTRY aqua/scripts_dns

  # find vpn container id
  vpn_container_id=$(docker ps --filter "name=$vpn_$COUNTRY" --format "{{.ID}}")

 # Start the Docker container with the environment variable
  while [ "$(docker ps --filter "name=script_container_dns" --format '{{.ID}}' | grep . | wc -l)" -ge 1 ]; do
    echo "Waiting for script_container_dns to stop..."
    sleep 60
  done

  docker stop $vpn_container_id

  echo "script_container_dns is not running"

  sleep 120

done

echo "All countries in the file has finished running dns script"