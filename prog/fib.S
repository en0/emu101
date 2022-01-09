# Fibonacci Test
# Run through a bunch of fibonacci numbers
# to test the emu101

main:   DP=@i
        D0=!19
        DATA=D0
        D0=!0
        D1=!1
loop:   D2=ADD D1
        D0=D1
        D1=D2
        D2=DATA
        D2,DATA=DEC D2
        IP=@loop?NZ,D2
        DP=@out
        DATA=D0
        HLT

