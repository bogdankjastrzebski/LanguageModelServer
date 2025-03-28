#!/bin/bash

# Black        0;30     Dark Gray     1;30
# Red          0;31     Light Red     1;31
# Green        0;32     Light Green   1;32
# Brown/Orange 0;33     Yellow        1;33
# Blue         0;34     Light Blue    1;34
# Purple       0;35     Light Purple  1;35
# Cyan         0;36     Light Cyan    1;36
# Light Gray   0;37     White         1;37

RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# cat ./jaskier.txt

#cat "daisy3.txt" | while IFS= read -r line; do
#	echo -e "$line"
#done

# echo "daisy"
# echo "⮟"
# echo "⮮daisy"
# echo -e "\n${GREEN}⮮daisy${NC}" > /dev/tty 
# echo "⯆daisy"
# echo "⮦daisy"

stream_name=$1
arrow_sign=$(printf "\u1b")
lines=("")
line=0
position=0
while true; do
    read -s -r -N1 char 
    # printf "%d" "'$char'" > /dev/tty
    if [ "$char" = $'\x04' ]; then
        for line in "${lines[@]}"; do
            echo "$line"
        done
        break
    elif [ "$char" = $'\x09' ]; then
        remainder=$(expr $position % 4)     
        remainder=$(expr 4 - $remainder)
        # if [ "$remainder" -eq 0 ]; then
        #    remainder=4
        # fi
        stride=$(printf "%*s" "$remainder" "")

        tput sc > /dev/tty 
		first_part="${lines[line]:0:position}"
		second_part="${lines[line]:position}"
       	position=`expr $position + $remainder`
       	lines[line]="$first_part$stride$second_part"
        tput el > /dev/tty 
        echo -n $'\r' > /dev/tty 
        echo -n "${lines[line]}" > /dev/tty 
		tput rc > /dev/tty 

        for (( i=0; i<$remainder; i++ )); do
		    tput cuf1 > /dev/tty 
        done

    elif [ "$char" = $'\x7f' ] || [ "$char" = $'\x08' ]; then
		if [ $position -ne 0 ]; then
			tput sc > /dev/tty 
		
			second_part="${lines[line]:position}"
			position=`expr $position - 1`
			first_part="${lines[line]:0:position}"
			lines[line]=$first_part$second_part
			echo -n $'\r' > /dev/tty 
			tput el > /dev/tty 
			echo -n "${lines[line]}" > /dev/tty 
			
			tput rc > /dev/tty 
			tput cub1 > /dev/tty 


		elif [ $line -ne 0 ]; then
			tput sc > /dev/tty 
			
			prev=`expr $line - 1`

			position="${#lines[prev]}"

			lines[prev]="${lines[prev]}""${lines[line]}"
			
			unset 'lines[line]'
			lines=("${lines[@]}")
			
			line=`expr $line - 1`
			tput cub $position > /dev/tty 
			tput cuu1 > /dev/tty 
	
			for l in "${lines[@]:line}"; do 
				tput el > /dev/tty 
				echo -n "$l" > /dev/tty 
				tput cud1 > /dev/tty 
			done
			# echo -n $'\r' > /dev/tty 
			tput el > /dev/tty 
			
			tput rc > /dev/tty 
			tput cuu1 > /dev/tty 
		        if [ $position -gt 0 ]; then
				tput cuf $position > /dev/tty 
			fi	
		fi
	
	elif [ "$char" = $'\x12' ]; then
    # 	clear
    # 	echo "Your command: " > /dev/tty 
    # 	echo
    # 	for l in "${lines[@]}"; do
	#			echo "$l" > /dev/tty 
    #        	done
    #       	echo > /dev/tty 
	#	 	echo "End of your command."
	#		exit
			
		for l in "${lines[@]}"; do
			echo "$l" >> $stream_name
		done	
		exit

	elif [ "$char" = $'\n' ]; then
			
		# Split 
		first_part="${lines[line]:0:position}"
		second_part="${lines[line]:position}"
		lines[line]=$first_part
			
		# Move 
		line=`expr $line + 1`
		position=0
			
		lines=("${lines[@]:0:line}" "$second_part" "${lines[@]:line}")
		for (( i=`expr $line - 1`; i<"${#lines[@]}"; i++ )); do
       	               	echo -n $'\r' > /dev/tty 
			tput el > /dev/tty 
			echo -n "${lines[i]}" > /dev/tty 
			tput cud1 > /dev/tty 
                done
		moveup=`expr "${#lines[@]}" - $line`
		if [ $moveup -gt 0 ]; then
			tput cuu $moveup > /dev/tty 
		fi
	
	elif [[ $char == $arrow_sign ]]; then
        read -rsn2 mode 
  	    case $mode in
            '[A')
                if [ $line -gt 0 ]; then
					line=`expr $line - 1`
					number_of_chars="${#lines[line]}"
					moveleft=$(( $position > $number_of_chars ? `expr $position - $number_of_chars` : 0 ))
					
					tput cuu1 > /dev/tty 
					if [ $moveleft -gt 0 ]; then
						position=`expr $position - $moveleft`
						tput cub $moveleft > /dev/tty 
					fi
				fi;;
            '[B') 
				if [ $line -lt `expr "${#lines[@]}" - 1` ]; then
                    line=`expr $line + 1`
                    number_of_chars="${#lines[line]}"
                    position=$(( $position > $number_of_chars ? $number_of_chars : $position ))
					tput cud1 > /dev/tty 
                    if [ $position -gt 0 ]; then
                        tput cuf $position > /dev/tty 
                    fi
                fi;;
			'[D')
                if [ $position -gt 0 ]; then
                    position=`expr $position - 1`
					tput cub1 > /dev/tty 
				fi;;
            '[C')
				if [ $position -lt "${#lines[line]}" ]; then
                    position=`expr $position + 1`
                    tput cuf1 > /dev/tty 
                fi;;
            esac
	else	
		tput sc > /dev/tty 
		first_part="${lines[line]:0:position}"
		second_part="${lines[line]:position}"
       	position=`expr $position + 1`
       	lines[line]=$first_part$char$second_part
        tput el > /dev/tty 
        echo -n $'\r' > /dev/tty 
        echo -n "${lines[line]}" > /dev/tty 
		tput rc > /dev/tty 
		tput cuf1 > /dev/tty 
	fi
done

# set! x 3

# for i in 0..n
#     print(3)
