#!/bin/bash
##################################bash script for only extracting the rows for choosed level and similar to bash.sh script( e.g; error or notice or All)#####################################
input_file="$1"
level_to_filter="$2"
output_file="${level_to_filter}_structuredlog.csv"

if [ ! -f "$input_file" ]; then
    echo "$input_file does not exist."
    exit 1
fi

if [ -z "$level_to_filter" ]; then
    echo "Please provide the level to filter (e.g., error or notice)."
    exit 1
fi

# CSV Header
echo "LineId,Time,Level,Content,EventId,EventTemplate" > "$output_file"

awk -v level="$level_to_filter" -v output_file="$output_file" '
BEGIN { lineId=1 }

{
    match($0, /^\[([^]]+)\] \[([^]]+)\] (.*)/, arr)

    time = arr[1]
    level_log = arr[2]
    content = arr[3]
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
        eventId = " "
        template = " "
    }

    if (level_log == level) {
        printf("%d,%s,%s,%s,%s,%s\n", lineId, time, level_log, content, eventId, template) >> output_file
        lineId++
    }
}
' "$input_file"
