
# function bott-repl
#     set chatbot $argv[1]
#     set mode "gemini"
#     while true
#         if string match -q "shell" "$mode"
#             set prompt_string "shell"
#             set prompt_color "red"
#         else
#             set prompt_string "gemini"
#             set prompt_color "blue"
#         end
#         set_color $prompt_color
#         echo -n "$prompt_string "
#         set_color normal
#         read -p "set_color \"$prompt_color\";
#                  echo -n \"$prompt_string\";
#                  set_color normal;
#                  echo -n '> '" input
#         if test -z "$input"
#             set input "$(get_command)" # (cat) # "$(sed '/^$/q')" # (read)
#         end
#         # set_color red
#         # echo -n "response"
#         set_color normal
#         # echo ": "
#         # set loading_pid \
#         #     (command loading_icon_unicode &; echo $last_pid)
#         switch "$input"
#             case "exit"
#                 set_color yellow
#                 echo "Exiting REPL..."
#                 set_color normal
#                 break
#             case "clear"
#                 clear
#             case "shell"
#                 set mode "shell"
#             case "gemini"
#                 set mode "gemini"
#             case "*"
#                 if not test -z "$input"
#                     if test $mode = "shell"
#                         # set out "$(eval $input 2>&1)"
#                         set out "$(eval $input 2>&1)"
#                         echo -n "$out"
#                         $chatbot "append
#                         shell> $input
#                         $out"
#                     else
#                         $chatbot "$input"
#                     end
#                 end
#         end
#     end
# end

function bott-repl
    set chatbot $argv[1]
    while true
        set prompt_string "gemini"
        set prompt_color "blue"
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
                set session_log (mktemp)
                set_color yellow
                echo "-> Starting interactive shell. Type 'exit' to return and capture."
                set_color normal
                # script -q -c fish $session_log
                script -q -c "fish -C 'functions -c fish_prompt __original_fish_prompt;
                                and function fish_prompt;
                                set_color normal;
                                echo -n \"[\"
                                set_color blue;
                                echo -n \"gemini\"
                                set_color normal;
                                echo -n \"] \";
                                __original_fish_prompt;
                              end'" $session_log
                set transcript (cat $session_log)
                rm $session_log
                if test -n "$transcript"
                    $chatbot "append $transcript"
                    set_color green
                    echo "-> Shell session captured and appended to context."
                    set_color normal
                else
                    set_color yellow
                    echo "-> Shell session was empty, nothing to append."
                    set_color normal
                end

            case "*"
                if not test -z "$input"
                    $chatbot "$input"
                end
        end
    end
end
