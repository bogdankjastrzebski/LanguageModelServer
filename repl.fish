#!/usr/bin/fish

function loading_icon_unicode
    # set -l frames "|/-\\" # Basic spinner
    set -l frames "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏" # Braille spinner
    # set -l frames "🌑🌒🌓🌔🌕🌖🌗🌘" # Moon phase spinner
    while true
        for i in (seq 1 (string length $frames))
            set -l frame (string sub -s $i -l 1 $frames)
            echo -n "$frame\r"
            sleep 0.1
        end
    end
end


function chatbot-repl
    set chatbot $argv[1]
    set mode "gemini"
    while true
        if string match -q "shell" "$mode"
            set prompt_string "shell"
            set prompt_color "red"
        else
            set prompt_string "gemini"
            set prompt_color "blue"
        end
        set_color $prompt_color
        echo -n "$prompt_string "
        set_color normal
        read -p "set_color \"$prompt_color\";
                 echo -n \"$prompt_string\";
                 set_color normal;
                 echo -n '> '" input
        if test -z "$input"
            set input "$(sed '/^$/q')" # (read) (cat) 
        end
        # set_color red
        # echo -n "response"
        set_color normal
        # echo ": "
        # set loading_pid \
        #     (command loading_icon_unicode &; echo $last_pid)
        switch "$input"
            case "exit"
                set_color yellow
                echo "Exiting REPL..."
                set_color normal
                break
            case "clear"
                clear
            case "shell"
                set mode "shell"
            case "gemini"
                set mode "gemini"
            case "*"
                if not test -z "$input"
                    if test $mode = "shell"
                        # set out "$(eval $input 2>&1)"
                        set out "$(eval $input 2>&1)"
                        echo -n "$out"
                        $chatbot "append
                        shell> $input
                        $out"
                    else
                        $chatbot "$input"
                    end
                end
        end
        # if string match -q "exit" "$input"
        #     echo "Exiting REPL..."
        #     break
        # else if string match -q "clear" "$input"
        #     clear
        # else if not test -z "$input"
        #     wonszu "$input"
        # end
    end
    # kill $loading_pid
end
