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
        if test -z "$input"
            echo "(ctrl-d to exit)"
            set input (cat) # (read) (sed '/^$/q') 
            echo 
        end
        if string match -q "exit" $input
            echo "Exiting REPL..."
            break
        else if not test -z "$input"
            wonszu "$input"
        end
    end
end
```

Basic usage:
```bash
~/.c/chatbot on main ⨯ wonszu-repl
read> let's write then something in scheme! like memoization, how to do it only on simple structs without libraries?
```

```scheme
    (define (memoize func)                                    
      (let ((cache (make-hash)))                              
        (lambda args                                          
          (if (hash-has-key? cache args)                      
              (hash-ref cache args)                           
              (let ((result (apply func args)))               
                (hash-set! cache args result)                 
                result)))))                                   
                                                              
                                                              
    ;; Example usage:                                         
    (define (factorial n)                                     
      (if (<= n 1)                                            
          1                                                   
          (* n (factorial (- n 1)))))                         
                                                              
    (define memoized-factorial (memoize factorial))           
                                                              
    (display (memoized-factorial 5)) (newline) ; Output: 120  
    (display (memoized-factorial 5)) (newline) ; Output: 120  
  (from cache)                                                
    (display (memoized-factorial 10)) (newline) ; Output:     
  3628800                                                     
```
                                      
```markdown
read> Tell me, step by step, how to cook, let's say, curry tikka-masala.
```

```
  Okay, let's break down how to make a delicious Chicken Tikka
  Masala, step-by-step:                                       
                                                              
  Ingredients You'll Need:                                    
                                                              
  • For the Chicken Tikka Marinade:                           
    • 1.5 lbs boneless, skinless chicken thighs or breasts,   
    cut into 1-inch pieces                                    
    • 1 cup plain yogurt                                      
    • 2 tbsp lemon juice
```


## TODO

- [ ] make a list of available model types in arguments
- [ ] rewrite in c?
