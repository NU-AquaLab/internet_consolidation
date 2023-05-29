#!/bin/bash

export TZ=America/Chicago
echo 'Certified Authority Script has been started at' $(date)

# build script image
docker build --tag aqua/scripts_ca . -f dockerfile_ca.prober

# build vpn image
docker build --tag aqua/vpn_ca . -f dockerfile.vpn

# Read the country name bfrom the file
for COUNTRY in $(cat ./infralocationanalysis/data/countryList_CA.txt); do
  echo $COUNTRY

  # Connect to VPN server
  docker run --rm -it --name vpn_ca_$COUNTRY --cap-add=NET_ADMIN --cap-add=NET_RAW -e CONNECT=$COUNTRY aqua/vpn_ca

  sleep 10

  echo "VPN Certified Authority works, connected to " $COUNTRY

  docker run --rm -itd --name script_container_ca -e COUNTRY=$COUNTRY --net container:vpn_ca_$COUNTRY aqua/scripts_ca

  # find vpn container id
  vpn_ca_container_id=$(docker ps --filter "name=$vpn_ca_$COUNTRY" --format "{{.ID}}")

   # Start the Docker container with the environment variable
  while [ "$(docker ps --filter "name=script_container_ca" --format '{{.ID}}' | grep . | wc -l)" -ge 1 ]; do
    echo "Waiting for script_container_ca to stop..."
    sleep 60
  done

  docker stop $vpn_ca_container_id

  echo "script_container_ca is not running"

  sleep 120

done

echo "All countries in the file has finished running Certified Authority script"