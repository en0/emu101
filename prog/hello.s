# Fibonacci Test
# Run through a bunch of fibonacci numbers
# to test the emu101

@i

_main:
        # i = 10 - the 10th fib number
        LDP @i # put the address of i int DP
        LD0 10 # put the value of 10 into d0
        WD0    # Write the value of d0 (10) at DP (i)

        # Setup Registers
        # D0 = 0, D2 = 1
        LD0 0  # D0 = 0
        LD1 1  # D1 = 1
        ### YOU ARE HERE
_fibL:  D0 = D1 + D2
        D1 = D2
        D2 = D0
        i=(DEC i) : jz _fibX
        JMP _fibL

_fibX:  RET

        
