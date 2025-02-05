#!/usr/bin/env zsh

#######################################################
# this is a dev script, not necessary for regular use #
#######################################################

trap kill_ableton INT

run_remote() {
    rm -rf ~/Music/Ableton/User\ Library/Remote\ Scripts/AbletonREPL
    cp -r AbletonREPL ~/Music/Ableton/User\ Library/Remote\ Scripts/AbletonREPL
    open -a "Ableton Live 12 Suite"
}

tail_ableton_log() {
    tail -f ~/Library/Preferences/Ableton/Live\ 12.1.5/Log.txt
}

less_ableton_log() {
    less ~/Library/Preferences/Ableton/Live\ 12.1.5/Log.txt
}

kill_ableton() {
    osascript -e 'tell application "Live" to quit'
}

case "$1" in
    "log")
        less_ableton_log
        ;;
    "ableton")
        run_remote
        tail_ableton_log
        ;;
    *)
        echo "options: ableton_log, ableton"
        ;;
esac
