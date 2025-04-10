
function bott-repl
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
            set input "$(get_command)" # (cat) # "$(sed '/^$/q')" # (read)
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
    end
end
