#!/bin/bash
while getopts "t:f:d:s:" opt; do
  case "$opt" in
      t) timeout=$OPTARG ;;
	  f) file=$OPTARG ;;
	  d) diff=$OPTARG ;;
	  s) expSize=$OPTARG ;;
  esac
done
shift $((OPTIND-1))

start_watchdog(){
	timeout="$1"
	file="$2"
	diff="$3"
	expSize="$4"
	prevSize=0
	newSize=0
	while (( newSize<expSize ))
	do
		if [ -e $file ]; then
			sleep $timeout #check status after every x seconds
			sync #need to write to disc for du to work
			sleep 1 #allow disk to finish writing (technically adds 1 second to next iteration's check)
			newSize=$(du -b $file | cut -f1)
			nextSize=$((prevSize+diff))
			wantSize=$((nextSize<expSize?nextSize:expSize))
			if [ $newSize -eq $expSize ]; then
				exit 0
			fi
			if [ $newSize -lt $((wantSize)) ]; then #if time out
				echo "killing process after timeout of $timeout seconds"
				kill -0 $$
				exit 20
			else #if file increases accordingly
				prevSize=$(du -b $file | cut -f1)
			fi
		else 
			echo "file does not exist"
			newSize=expSize ## to avoid infinite loop
		fi
	done
	
	
}


start_watchdog "$timeout" "$file" "$diff" "$expSize" 2>/dev/null &
exec "$@"
return $?

## Based on: http://fahdshariff.blogspot.com/2013/08/executing-shell-command-with-timeout.html
