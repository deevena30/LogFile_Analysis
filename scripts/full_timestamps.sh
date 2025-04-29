#!/bin/bash
############################################# bash script for storing all the timestamps in a text file################################
inputcsv="structuredlog.csv"

awk '
BEGIN {
    FS=","
}
NR > 1 {
    print $2
}' $inputcsv > full_timestamps.txt

