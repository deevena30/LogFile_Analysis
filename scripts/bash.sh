#!/bin/bash

##########################################bash script for converting log file into csv format#################################################

input_file="$1"
output_file="structuredlog.csv"

if [ ! -f "$input_file" ]; then
    echo "$input_file does not exist."
    exit 1
fi
# check_file_extension() {
#     local file="$1"
#     extension="${file##*.}"
#     if [[ "$extension" != "log" && "$extension" != "txt" ]]; then
#         echo "Not an Apache log file."
#         return 1
#     fi
#     return 0
# }

# check_file_content() {
#     local file="$1"
#     var = sed -n '1p' $file 
#     # Check if the file contains a typical Apache log entry pattern
#     if ! grep -qE 'notice' "$var"; then
#         echo "Not an Apache log file."
#         return 1
#     fi
#     return 0
# }

# CSV Header
echo "LineId,Time,Level,Content,EventId,EventTemplate" > "$output_file"
lineId = 0
awk '
BEGIN { lineId=1 }

{
    # Extract time
    first_lb = index($0, "[")
    first_rb = index($0, "]")
    time = substr($0, first_lb + 1, first_rb - first_lb - 1)

    # Extract level
    second_lb = index(substr($0, first_rb + 1), "[") + first_rb
    second_rb = index(substr($0, second_lb + 1), "]") + second_lb
    level = substr($0, second_lb + 1, second_rb - second_lb - 1)

    # Extract content
    content = substr($0, second_rb + 2)

    # Clean content
    gsub(/\r/, "", content)
    gsub(/\n/, "", content)
    eventId = ""
    template = ""

    if (content ~ /jk2_init\(\) Found child [0-9]+ in scoreboard slot [0-9]+/) {
        eventId = "E1"
        template = "jk2_init() Found child <*> in scoreboard slot <*>"
    } else if (content ~ /workerEnv.init\(\) ok \/etc\/httpd\/conf\/workers2.properties/) {
        eventId = "E2"
        template = "workerEnv.init() ok <*>"
    } else if (content ~ /mod_jk child workerEnv in error state [0-9]+/) {
        eventId = "E3"
        template = "mod_jk child workerEnv in error state <*>"
    } else if (content ~ /\[client [0-9.]+\] Directory index forbidden by rule: \/var\/www\/html\//) {
        eventId = "E4"
        template = "[client <*>] Directory index forbidden by rule: <*>"
    } else if (content ~ /jk2_init\(\) Can'\''t find child [0-9]+ in scoreboard/) {
        eventId = "E5"
        template = "jk2_init() Can'\''t find child <*> in scoreboard"
    } else if (content ~ /mod_jk child init 1 -2/) {
        eventId = "E6"
        template = "mod_jk child init <*> <*>"
    } else {
      # Default case if pattern is unknown
        eventId = " "
        template = " "  
    }

   printf("%d,%s,%s,%s,%s,%s\n", lineId,time,level,content,eventId,template)
   lineId++
}
' "$input_file" >> "$output_file"
