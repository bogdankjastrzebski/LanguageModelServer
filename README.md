# README

This is an unofficial implementation of Gemini for command line.

## Usage

Combine with `glow` to make a colorful REPL:

```fish
function wonszu
    bot "$argv[1]"   \
        --name=wonsz \
        --conversation=default | glow -w 60
end


function wonszu-repl
    while true
        read input
        if string match -q "exit" $input
            echo "Exiting REPL..."
            break
        else if not test -z "$input"
            wonszu "$input"
        end
    end
end
```

## TODO

- [ ] make a list of available model types in arguments
- [ ] rewrite in c?
