#!/bin/bash
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -c|--config)
    CONFIG="$2"
    shift
    shift
    ;;
    -d|--deviceConfig)
    DEVICE_CONFIG="$2"
    shift
    shift
    ;;
esac
done

if [[ -z "$CONFIG" ]]; then
    echo "Missing -c/--config argument. Please provide appropriate config.yaml file. Exiting."
    exit 1
fi


if [[ -z "$DEVICE_CONFIG" ]]; then
    echo "Missing -d/--deviceConfig argument. Please provide appropriate deviceConfig.json file. Exiting."
    exit 1
fi

echo "config.yaml = $CONFIG"
echo "deviceConfig.json = $DEVICE_CONFIG"


echo "mkdir /etc/hawkbit-client"
mkdir /etc/hawkbit-client

echo "cp config.yaml deviceConfig.json /etc/hawkbit-client/"
cp config.yaml deviceConfig.json /etc/hawkbit-client/

echo "cp hawkbit_client.service /etc/systemd/system/"
cp hawkbit_client.service /etc/systemd/system/

echo "python3 -m pip install ."
python3 -m pip install .

echo "systemctl daemon-reload"
systemctl daemon-reload

echo "systemctl enable hawkbit_client.service"
systemctl enable hawkbit_client.service

echo "systemctl restart hawkbit_client.service"
systemctl restart hawkbit_client.service
