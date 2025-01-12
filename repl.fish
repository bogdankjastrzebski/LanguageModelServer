#!/usr/bin/fish

function wonszu
    # set tmpfile (mktemp)
    # trap 'rm -f "$tmpfile"' EXIT
    bot "$argv[1]"   \
        --name=wonsz \
        --conversation=default | glow -w 60 # > "$tmpfile"
    # cat "$tmpfile" | glow -w 60
end


function wonszu-repl
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
            set_color red
            echo "response: "
            set_color normal
        end
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
                        set output (eval $input)
                        wonszu append "$output"
                    else
                        wonszu "$input"
                    end
                end
        end
    end
end
