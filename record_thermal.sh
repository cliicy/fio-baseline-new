#!/bin/bash
mydir="$( cd "$( dirname "$0"  )" && pwd  )"
dev_name=$1
output_file=$2
interval=20
disk=${dev_name##*/}

if [ ! -b ${dev_name} ]; then echo "device [${dev_name}] does not exist"; fi
if [ "${output_file}" == "" ]; then output_dir=./${disk}.thermal; fi

source ${mydir}/functions
while ((1==1))
do
    collect_power_consumption ${disk} >> ${output_file}
    collect_temperature ${disk} >> ${output_file}
    echo -e "\n" >> ${output_file}
    sleep ${interval}
done
