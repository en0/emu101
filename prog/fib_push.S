# !! Stack is not working. This code should work but it doesn't

main:   D0=!19
        STACK=D0
        D0=!0
        D1=!1
        D2=ADD D1
        D0=D1
        D1=D2
        D2,STACK=DEC D2
        # This should be IP=@loop?NZ,D2 but i got a issue in the assembler
        IP=@main+4?NZ,D2
        DP=@out
        DATA=D0
        HLT

